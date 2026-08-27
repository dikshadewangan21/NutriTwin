import os
import sys
import json
import time
import copy
from pathlib import Path
from typing import Dict, List, Tuple, Any

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms, models
from torchvision.models import mobilenet_v3_small, MobileNet_V3_Small_Weights
from PIL import Image, ImageFile
from sklearn.metrics import classification_report, confusion_matrix

ImageFile.LOAD_TRUNCATED_IMAGES = True

# Directory Paths
BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "datasets" / "vision" / "indian_food_16"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
PROCESSED_DIR = BASE_DIR / "processed"

MODEL_SAVE_PATH = ARTIFACTS_DIR / "mobilenet_v3_indian_food.pth"
MAPPING_SAVE_PATH = ARTIFACTS_DIR / "vision_class_mapping.json"
EVAL_SAVE_PATH = PROCESSED_DIR / "vision_model_evaluation.json"

ALT_ARTIFACTS_DIR = BASE_DIR.parent / "ml_artifacts"

# ImageNet normalization standard
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


class VerifiedImageFolderDataset(Dataset):
    """
    Custom PyTorch Dataset that verifies image integrity during initialization,
    purging any corrupted or unreadable images.
    """
    def __init__(self, root_dir: Path, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.samples = []
        self.classes = sorted([d.name for d in root_dir.iterdir() if d.is_dir()])
        self.class_to_idx = {cls_name: idx for idx, cls_name in enumerate(self.classes)}
        
        corrupted_count = 0
        valid_extensions = {".jpg", ".jpeg", ".png", ".webp"}

        for cls_name in self.classes:
            cls_dir = root_dir / cls_name
            for img_path in cls_dir.iterdir():
                if img_path.is_file() and img_path.suffix.lower() in valid_extensions:
                    try:
                        with Image.open(img_path) as img:
                            img.verify() # Fast integrity check
                        self.samples.append((str(img_path), self.class_to_idx[cls_name]))
                    except Exception:
                        corrupted_count += 1

        if corrupted_count > 0:
            print(f"[{root_dir.name} Dataset] Purged {corrupted_count} corrupted/unreadable images.")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, target = self.samples[idx]
        try:
            with Image.open(path) as img:
                img = img.convert("RGB")
        except Exception:
            # Fallback for transient load errors
            img = Image.new("RGB", (224, 224), (128, 128, 128))

        if self.transform is not None:
            img = self.transform(img)

        return img, target


def get_transforms():
    """Define transforms for training, validation, and testing."""
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.10),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
    ])

    eval_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
    ])

    return train_transform, eval_transform


def calculate_topk_accuracy(outputs, targets, topk=(1, 5)):
    """Calculate Top-1 and Top-K accuracy for evaluation batch."""
    maxk = max(topk)
    batch_size = targets.size(0)

    _, pred = outputs.topk(maxk, 1, True, True)
    pred = pred.t()
    correct = pred.eq(targets.view(1, -1).expand_as(pred))

    res = []
    for k in topk:
        correct_k = correct[:k].reshape(-1).float().sum(0, keepdim=True)
        res.append(correct_k.item())
    return res # Returns count of correct top-1 and top-k predictions


def train_vision_classifier(epochs: int = 5, batch_size: int = 32, lr: float = 1e-3):
    """
    Train MobileNetV3 transfer learning model on Indian Food 16 dataset.
    """
    print("=" * 75)
    print("PHASE 3 — TRAINING FOOD VISION CLASSIFIER (MOBILENETV3)")
    print("=" * 75)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Executing on Compute Device: {device}")

    train_dir = DATASET_DIR / "Train"
    val_dir = DATASET_DIR / "Validate"
    test_dir = DATASET_DIR / "Test"

    if not train_dir.exists() or not val_dir.exists() or not test_dir.exists():
        raise FileNotFoundError(f"Vision dataset splits missing at: {DATASET_DIR}")

    train_tf, eval_tf = get_transforms()

    # Load datasets
    print("\n1. Loading and verifying dataset splits...")
    train_dataset = VerifiedImageFolderDataset(train_dir, transform=train_tf)
    val_dataset = VerifiedImageFolderDataset(val_dir, transform=eval_tf)
    test_dataset = VerifiedImageFolderDataset(test_dir, transform=eval_tf)

    class_names = train_dataset.classes
    num_classes = len(class_names)

    print(f"   -> Detected {num_classes} Indian Food Classes:")
    print(f"      {', '.join(class_names)}")
    print(f"   -> Split Sizes: Train={len(train_dataset)}, Val={len(val_dataset)}, Test={len(test_dataset)}")

    # Data Loaders
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=0)

    # Initialize MobileNetV3 Small transfer learning model
    print("\n2. Initializing pre-trained MobileNetV3 Small Transfer Learning Model...")
    model = mobilenet_v3_small(weights=MobileNet_V3_Small_Weights.DEFAULT)

    # Replace final classification head
    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, num_classes)
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_model_wts = copy.deepcopy(model.state_dict())
    best_val_acc = 0.0

    print(f"\n3. Training model over {epochs} epochs...")
    start_time = time.time()

    for epoch in range(1, epochs + 1):
        print(f"\n --- Epoch {epoch}/{epochs} ---")
        
        # Training Phase
        model.train()
        running_loss = 0.0
        running_corrects = 0
        total_train = 0

        for inputs, labels in train_loader:
            inputs = inputs.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            _, preds = torch.max(outputs, 1)
            running_loss += loss.item() * inputs.size(0)
            running_corrects += torch.sum(preds == labels.data).item()
            total_train += inputs.size(0)

        scheduler.step()
        epoch_train_loss = running_loss / max(1, total_train)
        epoch_train_acc = running_corrects / max(1, total_train)

        # Validation Phase (Validate after every epoch)
        model.eval()
        val_loss = 0.0
        val_corrects = 0
        total_val = 0

        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs = inputs.to(device)
                labels = labels.to(device)

                outputs = model(inputs)
                loss = criterion(outputs, labels)

                _, preds = torch.max(outputs, 1)
                val_loss += loss.item() * inputs.size(0)
                val_corrects += torch.sum(preds == labels.data).item()
                total_val += inputs.size(0)

        epoch_val_loss = val_loss / max(1, total_val)
        epoch_val_acc = val_corrects / max(1, total_val)

        print(f" Train Loss: {epoch_train_loss:.4f} | Train Acc: {epoch_train_acc*100:.2f}%")
        print(f" Val Loss  : {epoch_val_loss:.4f} | Val Acc  : {epoch_val_acc*100:.2f}%")

        # Deep copy best model weights
        if epoch_val_acc > best_val_acc:
            best_val_acc = epoch_val_acc
            best_model_wts = copy.deepcopy(model.state_dict())
            print(f"   -> [Checkpoint Saved] Highest Validation Accuracy: {best_val_acc*100:.2f}%")

    training_time_sec = round(time.time() - start_time, 2)
    print(f"\nTraining Complete in {training_time_sec} seconds. Best Val Acc: {best_val_acc*100:.2f}%")

    # Load best model weights for untouched Test set evaluation
    model.load_state_dict(best_model_wts)
    model.eval()

    # 4. Evaluation on Untouched Test Set
    print("\n4. Evaluating best model on untouched Test Set...")
    all_preds = []
    all_targets = []
    top1_correct = 0
    top5_correct = 0
    total_test = 0

    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs = inputs.to(device)
            labels = labels.to(device)

            outputs = model(inputs)
            t1, t5 = calculate_topk_accuracy(outputs, labels, topk=(1, min(5, num_classes)))

            top1_correct += t1
            top5_correct += t5
            total_test += labels.size(0)

            _, preds = torch.max(outputs, 1)
            all_preds.extend(preds.cpu().numpy())
            all_targets.extend(labels.cpu().numpy())

    top1_acc = round(top1_correct / max(1, total_test), 4)
    top5_acc = round(top5_correct / max(1, total_test), 4)

    clf_report = classification_report(all_targets, all_preds, target_names=class_names, output_dict=True)
    cm = confusion_matrix(all_targets, all_preds).tolist()

    print("\n=======================================================================")
    print("UNTOUCHED TEST SET PERFORMANCE METRICS")
    print("=======================================================================")
    print(f" Top-1 Accuracy : {top1_acc*100:.2f}% ({int(top1_correct)}/{total_test})")
    print(f" Top-5 Accuracy : {top5_acc*100:.2f}% ({int(top5_correct)}/{total_test})")
    print(f" Macro Precision : {clf_report['macro avg']['precision']:.4f}")
    print(f" Macro Recall    : {clf_report['macro avg']['recall']:.4f}")
    print(f" Macro F1-Score  : {clf_report['macro avg']['f1-score']:.4f}")
    print("=======================================================================")

    # 5. Save Artifacts
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Save model weights
    torch.save(best_model_wts, MODEL_SAVE_PATH)
    print(f"\n5. Saved trained model weights to: {MODEL_SAVE_PATH}")

    if ALT_ARTIFACTS_DIR.exists():
        torch.save(best_model_wts, ALT_ARTIFACTS_DIR / "mobilenet_v3_indian_food.pth")

    # Save class to index mapping
    class_mapping = {
        "class_to_idx": train_dataset.class_to_idx,
        "idx_to_class": {idx: cls_name for cls_name, idx in train_dataset.class_to_idx.items()},
        "classes": class_names,
        "num_classes": num_classes
    }
    with open(MAPPING_SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(class_mapping, f, indent=2, ensure_ascii=False)

    print(f"   Saved class mapping JSON to: {MAPPING_SAVE_PATH}")

    # Save evaluation report JSON
    eval_report = {
        "model_architecture": "MobileNetV3_Small",
        "num_classes": num_classes,
        "classes": class_names,
        "test_sample_count": total_test,
        "top1_accuracy": top1_acc,
        "top5_accuracy": top5_acc,
        "macro_avg": clf_report["macro avg"],
        "weighted_avg": clf_report["weighted avg"],
        "per_class_metrics": {cls_name: clf_report[cls_name] for cls_name in class_names if cls_name in clf_report},
        "confusion_matrix": cm,
        "training_time_sec": training_time_sec
    }
    with open(EVAL_SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2, ensure_ascii=False)

    print(f"   Saved evaluation report JSON to: {EVAL_SAVE_PATH}")
    print("=" * 75)

    return model, eval_report


if __name__ == "__main__":
    train_vision_classifier(epochs=5)
