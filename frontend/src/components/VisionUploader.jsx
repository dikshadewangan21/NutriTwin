import React, { useState, useRef, useCallback } from 'react';
import {
  Camera, Upload, Edit3, Plus, Sparkles, Search, CheckCircle,
  ChevronDown, AlertCircle, RefreshCw, Info, X
} from 'lucide-react';

const CATEGORY_COLORS = {
  breakfast: 'badge-amber',
  lunch: 'badge-emerald',
  dinner: 'badge-purple',
  snack: 'badge-indigo',
  pre_workout: 'badge-indigo',
  post_workout: 'badge-emerald',
};

export default function VisionUploader({ onMealLogged }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [servingMult, setServingMult] = useState(1.0);
  const [activeFoodId, setActiveFoodId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [logged, setLogged] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);
  const searchTimeout = useRef(null);

  // ── File helpers ──────────────────────────────────────────────────────────
  const loadFile = (file) => {
    if (!file) return;
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setScanResult(null);
    setLogged(false);
    setSearchResults([]);
    setSearchQuery('');
  };

  const handleFileChange = (e) => loadFile(e.target.files[0]);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) loadFile(file);
  }, []);

  const handleDragOver = (e) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = () => setIsDragging(false);

  // ── Scan ──────────────────────────────────────────────────────────────────
  const handleScan = async () => {
    if (!selectedFile) return;
    setScanning(true);
    setScanResult(null);
    try {
      const token = localStorage.getItem('nutritwin_token');
      const formData = new FormData();
      formData.append('file', selectedFile);

      const res = await fetch('/api/v1/vision/scan-meal', {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData
      });

      if (res.ok) {
        const data = await res.json();
        setScanResult(data);
        setActiveFoodId(data.detected_food?.food_id || null);
        setServingMult(1.0);
      } else {
        const err = await res.json();
        alert(err.detail || 'Scan failed. Please try a clearer image.');
      }
    } catch (err) {
      console.error('Scan error:', err);
    } finally {
      setScanning(false);
    }
  };

  // ── Manual search ─────────────────────────────────────────────────────────
  const handleSearch = (q) => {
    setSearchQuery(q);
    clearTimeout(searchTimeout.current);
    if (q.length < 2) { setSearchResults([]); return; }
    setSearching(true);
    searchTimeout.current = setTimeout(async () => {
      try {
        const token = localStorage.getItem('nutritwin_token');
        const res = await fetch(`/api/v1/vision/food-search?q=${encodeURIComponent(q)}&limit=8`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        });
        if (res.ok) {
          const data = await res.json();
          setSearchResults(data.results || []);
        }
      } catch (_) {}
      finally { setSearching(false); }
    }, 350);
  };

  const selectFood = (food) => {
    setActiveFoodId(food.food_id);
    setServingMult(1.0);
    setSearchQuery('');
    setSearchResults([]);
    // Inject into scan result as override
    setScanResult((prev) => prev
      ? { ...prev, detected_food: food }
      : { success: true, detected_food: food, top_candidates: [food], detection_notes: [] }
    );
  };

  // ── Log meal ──────────────────────────────────────────────────────────────
  const handleLog = async () => {
    const food = scanResult?.detected_food;
    if (!food) return;
    const token = localStorage.getItem('nutritwin_token');
    await fetch(`/api/v1/tracking/log-meal?food_id=${food.food_id}&servings=${servingMult}`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    });
    setLogged(true);
    if (onMealLogged) onMealLogged();
  };

  const food = scanResult?.detected_food;
  const candidates = scanResult?.top_candidates || [];
  const features = scanResult?.visual_features;
  const notes = scanResult?.detection_notes || [];

  // Calculated nutrition with serving multiplier
  const calc = (val) => Math.round((val || 0) * servingMult);

  return (
    <div className="max-w-7xl mx-auto px-4 pb-12 space-y-6">
      {/* Header */}
      <div className="glass-panel p-6 border-l-4 border-l-cyan-400 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="badge badge-indigo mb-2">Multi-Signal Recognition</span>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Camera className="w-6 h-6 text-cyan-400" />
            Food Scanner
          </h2>
          <p className="text-xs text-gray-400">
            Snap or upload a photo of your meal. The system analyzes colors, textures, and visual patterns to identify the dish.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* ─── Left: Upload Area ─────────────────────────────────── */}
        <div className="space-y-4">
          {/* Drop zone */}
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            className={`glass-panel flex flex-col items-center justify-center min-h-[320px] border-2 border-dashed transition-all ${
              isDragging ? 'border-cyan-400 bg-cyan-500/10' : 'border-gray-700 hover:border-gray-600'
            }`}
          >
            {previewUrl ? (
              <div className="w-full p-4 space-y-4 text-center">
                <div className="relative inline-block">
                  <img
                    src={previewUrl}
                    alt="Your meal photo"
                    className="max-h-64 mx-auto rounded-2xl object-cover border border-gray-700 shadow-xl"
                  />
                  <button
                    onClick={() => { setPreviewUrl(null); setSelectedFile(null); setScanResult(null); }}
                    className="absolute top-2 right-2 w-7 h-7 rounded-full bg-gray-900/90 border border-gray-700 flex items-center justify-center text-gray-400 hover:text-white"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
                <div className="flex justify-center gap-3">
                  <label className="btn-secondary py-2 px-3 text-xs cursor-pointer">
                    <Upload className="w-4 h-4" /> Change Photo
                    <input type="file" accept="image/*" onChange={handleFileChange} className="hidden" ref={fileInputRef} />
                  </label>
                  <button
                    onClick={handleScan}
                    disabled={scanning}
                    className="btn-primary py-2 text-xs"
                  >
                    {scanning
                      ? <><RefreshCw className="w-4 h-4 animate-spin" /> Analyzing...</>
                      : <><Sparkles className="w-4 h-4" /> Identify Food</>
                    }
                  </button>
                </div>
              </div>
            ) : (
              <label className="cursor-pointer flex flex-col items-center gap-4 p-8 text-center">
                <div className={`w-20 h-20 rounded-3xl flex items-center justify-center border transition-all ${
                  isDragging ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300' : 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400'
                }`}>
                  <Upload className="w-10 h-10" />
                </div>
                <div>
                  <p className="text-base font-semibold text-white">Drop your meal photo here</p>
                  <p className="text-xs text-gray-400 mt-1">or click to browse • JPG, PNG, WEBP • max 10MB</p>
                </div>
                <p className="text-xs text-gray-500 max-w-xs">
                  Works best with well-lit, single-dish photos. The scanner reads colors and textures to identify Indian dishes.
                </p>
                <input type="file" accept="image/*" onChange={handleFileChange} className="hidden" />
              </label>
            )}
          </div>

          {/* Visual Feature Debug Info */}
          {features && (
            <div className="glass-panel p-4 space-y-3">
              <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5" /> What the Scanner Detected
              </h4>
              <div className="grid grid-cols-3 gap-3 text-xs text-center">
                <div className="bg-gray-900/60 p-2.5 rounded-xl">
                  <p className="text-gray-500">COLOR TONE</p>
                  <p className="font-bold text-white">{features.dominant_hue_deg}°</p>
                  <p className="text-[10px] text-gray-600">Hue (0=red, 120=green)</p>
                </div>
                <div className="bg-gray-900/60 p-2.5 rounded-xl">
                  <p className="text-gray-500">SATURATION</p>
                  <p className="font-bold text-white">{Math.round(features.color_saturation * 100)}%</p>
                  <p className="text-[10px] text-gray-600">Vivid vs muted</p>
                </div>
                <div className="bg-gray-900/60 p-2.5 rounded-xl">
                  <p className="text-gray-500">BRIGHTNESS</p>
                  <p className="font-bold text-white">{Math.round(features.brightness * 100)}%</p>
                  <p className="text-[10px] text-gray-600">Dark vs light</p>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {features.is_green_dish && <span className="badge badge-emerald text-[10px]">🟢 Green/Leafy Dish</span>}
                {features.is_red_dish && <span className="badge badge-rose text-[10px]">🔴 Curry/Tandoori</span>}
                {features.color_variety > 35 && <span className="badge badge-indigo text-[10px]">🌈 Multi-colored Platter</span>}
              </div>
              {notes.map((n, i) => (
                <p key={i} className="text-[11px] text-cyan-300 flex items-start gap-1.5">
                  <Info className="w-3 h-3 mt-0.5 shrink-0" /> {n}
                </p>
              ))}
            </div>
          )}
        </div>

        {/* ─── Right: Results ────────────────────────────────────── */}
        <div className="space-y-4">

          {/* Manual Search Override */}
          <div className="glass-panel p-4 space-y-3">
            <h4 className="text-xs font-bold text-gray-300 flex items-center gap-1.5">
              <Search className="w-3.5 h-3.5 text-indigo-400" />
              Search & Select Food Manually
            </h4>
            <div className="relative">
              <input
                type="text"
                placeholder="Type food name (e.g. 'dal tadka', 'idli', 'paneer')"
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                className="form-input pr-8 text-sm"
              />
              {searching && <RefreshCw className="w-4 h-4 animate-spin text-gray-400 absolute right-3 top-3" />}
            </div>
            {searchResults.length > 0 && (
              <div className="space-y-1 max-h-48 overflow-y-auto">
                {searchResults.map((r) => (
                  <button
                    key={r.food_id}
                    onClick={() => selectFood(r)}
                    className="w-full text-left flex items-center justify-between px-3 py-2.5 rounded-xl hover:bg-gray-800 transition text-xs border border-gray-800"
                  >
                    <div>
                      <p className="font-semibold text-white">{r.name}</p>
                      {r.name_hindi && <p className="text-gray-500 text-[10px]">{r.name_hindi}</p>}
                    </div>
                    <div className="text-right">
                      <p className="text-white font-bold">{r.calories} kcal</p>
                      <span className={`badge ${CATEGORY_COLORS[r.category] || 'badge-indigo'} text-[9px]`}>{r.category}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Top Match */}
          {food && (
            <div className="glass-panel p-5 space-y-4 border-t-2 border-t-cyan-400">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-emerald-400" />
                  <h3 className="font-bold text-white text-base">Identified Food</h3>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`badge ${
                    food.confidence_pct >= 80 ? 'badge-emerald'
                    : food.confidence_pct >= 65 ? 'badge-amber'
                    : 'badge-rose'
                  } text-xs`}>
                    {food.confidence_pct}% match
                  </span>
                  <span className={`badge ${CATEGORY_COLORS[food.category] || 'badge-indigo'} text-[10px]`}>
                    {food.category}
                  </span>
                </div>
              </div>

              <div>
                <h4 className="text-xl font-bold text-white">{food.name}</h4>
                {food.name_hindi && <p className="text-sm text-gray-400">{food.name_hindi}</p>}
                <p className="text-xs text-gray-500 mt-1">{food.estimated_serving} • {food.estimated_weight_g}g</p>
                {food.description && <p className="text-xs text-gray-400 mt-2 italic">{food.description}</p>}
              </div>

              {/* Serving slider */}
              <div className="bg-gray-900/60 p-4 rounded-xl space-y-2 border border-gray-800">
                <div className="flex justify-between items-center text-xs">
                  <span className="flex items-center gap-1 text-gray-300 font-semibold">
                    <Edit3 className="w-3.5 h-3.5 text-amber-400" /> Adjust Portion:
                  </span>
                  <span className="font-bold text-emerald-400 text-sm">{servingMult}x serving</span>
                </div>
                <input
                  type="range"
                  min="0.5" max="3.0" step="0.25"
                  value={servingMult}
                  onChange={(e) => setServingMult(parseFloat(e.target.value))}
                  className="w-full accent-emerald-500"
                />
                <div className="flex justify-between text-[10px] text-gray-600">
                  <span>½ serving</span><span>1 serving</span><span>2×</span><span>3×</span>
                </div>
              </div>

              {/* Nutrition */}
              <div className="grid grid-cols-4 gap-2 text-center bg-gray-900/80 p-3 rounded-xl">
                <div>
                  <p className="text-[10px] text-gray-500">CALORIES</p>
                  <p className="font-bold text-white text-lg">{calc(food.calories)}</p>
                </div>
                <div>
                  <p className="text-[10px] text-gray-500">PROTEIN</p>
                  <p className="font-bold text-emerald-400 text-lg">{calc(food.protein_g)}g</p>
                </div>
                <div>
                  <p className="text-[10px] text-gray-500">CARBS</p>
                  <p className="font-bold text-indigo-300 text-lg">{calc(food.carbs_g)}g</p>
                </div>
                <div>
                  <p className="text-[10px] text-gray-500">FAT</p>
                  <p className="font-bold text-amber-400 text-lg">{calc(food.fat_g)}g</p>
                </div>
              </div>

              {logged ? (
                <div className="flex items-center justify-center gap-2 bg-emerald-950/60 border border-emerald-500/40 rounded-xl p-3 text-emerald-300 text-sm font-semibold">
                  <CheckCircle className="w-5 h-5" />
                  Added {food.name} ({servingMult}× serving) to your daily intake!
                </div>
              ) : (
                <button onClick={handleLog} className="btn-primary w-full py-3 justify-center text-sm">
                  <Plus className="w-4 h-4" />
                  Add to Today's Intake
                </button>
              )}
            </div>
          )}

          {/* Other Candidates */}
          {candidates.length > 1 && (
            <div className="glass-panel p-4 space-y-3">
              <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">
                Other Possible Matches — Tap to Select
              </h4>
              <div className="space-y-2">
                {candidates.slice(1).map((c) => (
                  <button
                    key={c.food_id}
                    onClick={() => selectFood(c)}
                    className={`w-full text-left flex items-center justify-between px-3 py-2.5 rounded-xl border transition text-xs ${
                      activeFoodId === c.food_id
                        ? 'border-emerald-500 bg-emerald-950/40 text-white'
                        : 'border-gray-800 hover:border-gray-700 hover:bg-gray-800/50'
                    }`}
                  >
                    <div>
                      <p className="font-semibold text-white">{c.name}</p>
                      <p className="text-gray-500">{c.calories} kcal • {c.estimated_serving}</p>
                    </div>
                    <span className={`badge text-[10px] ${
                      c.confidence_pct >= 80 ? 'badge-emerald'
                      : c.confidence_pct >= 65 ? 'badge-amber'
                      : 'badge-rose'
                    }`}>{c.confidence_pct}%</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Empty state */}
          {!food && !scanning && (
            <div className="glass-panel p-12 text-center text-gray-500 space-y-3">
              <Camera className="w-12 h-12 mx-auto text-gray-700" />
              <p className="font-semibold text-sm">Upload a meal photo and tap "Identify Food"</p>
              <p className="text-xs text-gray-600">
                Or use the search above to find any dish by name and log it directly.
              </p>
            </div>
          )}

          {scanning && (
            <div className="glass-panel p-12 text-center space-y-3">
              <Sparkles className="w-8 h-8 animate-spin mx-auto text-cyan-400" />
              <p className="text-white font-semibold">Analyzing your meal photo...</p>
              <p className="text-xs text-gray-400">Extracting color patterns, textures, and brightness zones.</p>
            </div>
          )}
        </div>
      </div>


    </div>
  );
}
