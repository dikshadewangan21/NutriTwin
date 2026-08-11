class NutritionCalculator:
    """
    Calculates metabolic baselines using Mifflin-St Jeor and Harris-Benedict formulas.
    Distinguishes deterministic baseline requirements from ML adjustments.
    """
    def calculate_bmr(self, weight_kg, height_cm, age, gender):
        """Mifflin-St Jeor BMR equation."""
        if gender.lower() == "male":
            return round(10.0 * weight_kg + 6.25 * height_cm - 5.0 * age + 5.0, 1)
        else:
            return round(10.0 * weight_kg + 6.25 * height_cm - 5.0 * age - 161.0, 1)

    def calculate_tdee(self, bmr, activity_level):
        """Activity multiplier on BMR."""
        multipliers = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "very_active": 1.725,
            "extra_active": 1.9
        }
        mult = multipliers.get(activity_level.lower(), 1.375)
        return round(bmr * mult, 1)

    def calculate_bmi(self, weight_kg, height_cm):
        """Body Mass Index (BMI)."""
        height_m = height_cm / 100.0
        if height_m == 0:
            return 22.0
        bmi = weight_kg / (height_m * height_m)
        
        category = "Normal"
        if bmi < 18.5:
            category = "Underweight"
        elif 25.0 <= bmi < 30.0:
            category = "Overweight"
        elif bmi >= 30.0:
            category = "Obese"
            
        return {"bmi": round(bmi, 1), "category": category}

    def compute_nutritional_profile(self, age, gender, height_cm, weight_kg, target_weight_kg, activity_level, fitness_goal):
        """Computes comprehensive daily calorie and macronutrient requirements."""
        bmr = self.calculate_bmr(weight_kg, height_cm, age, gender)
        tdee = self.calculate_tdee(bmr, activity_level)
        bmi_data = self.calculate_bmi(weight_kg, height_cm)

        # Calorie target adjustment based on fitness goal
        if fitness_goal == "weight_loss":
            target_calories = tdee - 500.0 # 0.45kg loss/week
        elif fitness_goal == "muscle_gain":
            target_calories = tdee + 300.0 # Lean mass gain
        else:
            target_calories = tdee

        # Enforce healthy safety bounds (min 1200 kcal for female, 1500 for male)
        min_cals = 1200.0 if gender.lower() == "female" else 1500.0
        target_calories = max(min_cals, target_calories)

        # Macro split calculations
        # Protein: 1.6-2.0g/kg for muscle gain/loss, 1.2g/kg maintenance
        if fitness_goal in ["muscle_gain", "weight_loss"]:
            protein_g = weight_kg * 1.8
        else:
            protein_g = weight_kg * 1.2

        # Fat: 25% of total calories (9 kcal/g)
        fat_calories = target_calories * 0.25
        fat_g = fat_calories / 9.0

        # Carbs: Remaining calories (4 kcal/g)
        protein_calories = protein_g * 4.0
        carb_calories = target_calories - (protein_calories + fat_calories)
        carb_g = max(50.0, carb_calories / 4.0)

        # Fiber: 14g per 1000 kcal
        fiber_g = (target_calories / 1000.0) * 14.0

        # Hydration: 35ml per kg body weight
        hydration_l = (weight_kg * 35.0) / 1000.0

        return {
            "bmr": bmr,
            "tdee": tdee,
            "bmi": bmi_data["bmi"],
            "bmi_category": bmi_data["category"],
            "target_calories": round(target_calories, 1),
            "target_protein_g": round(protein_g, 1),
            "target_carbs_g": round(carb_g, 1),
            "target_fat_g": round(fat_g, 1),
            "target_fiber_g": round(fiber_g, 1),
            "target_hydration_l": round(hydration_l, 1)
        }

nutrition_calculator = NutritionCalculator()
