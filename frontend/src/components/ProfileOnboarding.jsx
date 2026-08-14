import React, { useState } from 'react';
import { User, Activity, Sparkles, CheckCircle, ShieldAlert, HeartPulse, ChevronRight, ChevronLeft, DollarSign, Clock, Moon, Edit3, Calendar } from 'lucide-react';

export default function ProfileOnboarding({ userProfile, onProfileUpdated, onGenerateDiet }) {
  const [currentStep, setCurrentStep] = useState(0); // 0 = guided landing screen

  const [formData, setFormData] = useState({
    // Step 1: Body Details
    age: userProfile?.age || 22,
    gender: userProfile?.gender || 'male',
    height_cm: userProfile?.height_cm || 165,
    current_weight_kg: userProfile?.current_weight_kg || 72,
    target_weight_kg: userProfile?.target_weight_kg || 65,

    // Step 2: Fitness & Activity
    fitness_goal: userProfile?.fitness_goal || 'weight_loss',
    activity_level: userProfile?.activity_level || 'moderate',
    goes_to_gym: true,
    gym_days_per_week: 5,
    workout_type: 'Gym / Strength Training',
    workout_duration_mins: 50,
    workout_time: 'Evening (6 PM - 8 PM)',
    daily_steps: 6500,

    // Step 3: Diet Preference
    dietary_preference: userProfile?.dietary_preference || 'vegetarian',
    liked_foods: userProfile?.liked_foods || ['paneer', 'rajma', 'dosa', 'oats', 'dal'],
    disliked_foods: userProfile?.disliked_foods || ['karela'],
    allergies: userProfile?.allergies || [],
    foods_to_avoid: userProfile?.foods_to_avoid || [],
    meals_per_day: 4,
    preferred_meal_timings: ['08:30 AM', '01:30 PM', '06:00 PM', '09:00 PM'],

    // Step 4: Health Conditions
    selected_conditions: userProfile?.medical_conditions || ['diabetes'],
    not_sure_guidance_requested: false,
    condition_details: {
      diabetes_type: 'Type 2',
      typical_carb_intake: 'Balanced carbs',
      monitors_glucose: 'Occasionally',
      salt_preference: 'Moderate salt'
    },

    // Step 5: Budget (Required)
    daily_budget_inr: userProfile?.daily_budget_inr || 250,
    weekly_budget_inr: userProfile?.weekly_budget_inr || 1750,

    // Step 6: Lifestyle
    sleep_duration_hours: 7.5,
    water_intake_target_l: 2.8,
    wake_up_time: '07:00 AM',
    sleep_time: '11:00 PM',
    work_schedule: '9 AM - 5 PM Desk Job'
  });

  // Sync formData whenever userProfile changes
  React.useEffect(() => {
    if (userProfile) {
      setFormData((prev) => ({
        ...prev,
        age: userProfile.age ?? prev.age,
        gender: userProfile.gender ?? prev.gender,
        height_cm: userProfile.height_cm ?? prev.height_cm,
        current_weight_kg: userProfile.current_weight_kg ?? prev.current_weight_kg,
        target_weight_kg: userProfile.target_weight_kg ?? prev.target_weight_kg,
        fitness_goal: userProfile.fitness_goal ?? prev.fitness_goal,
        activity_level: userProfile.activity_level ?? prev.activity_level,
        dietary_preference: userProfile.dietary_preference ?? prev.dietary_preference,
        daily_budget_inr: userProfile.daily_budget_inr ?? prev.daily_budget_inr,
        weekly_budget_inr: userProfile.weekly_budget_inr ?? prev.weekly_budget_inr,
        selected_conditions: userProfile.medical_conditions || prev.selected_conditions,
        liked_foods: userProfile.liked_foods || prev.liked_foods,
        disliked_foods: userProfile.disliked_foods || prev.disliked_foods,
        allergies: userProfile.allergies || prev.allergies
      }));
    }
  }, [userProfile]);

  const [saving, setSaving] = useState(false);
  const [healthProfileResult, setHealthProfileResult] = useState(null);

  // Real-time body calculations for Step 1
  const calculateRealtimeBodyMetrics = () => {
    const h = formData.height_cm / 100;
    const w = formData.current_weight_kg;
    const bmi = h > 0 ? (w / (h * h)).toFixed(1) : 22.0;

    let bmiCat = 'Normal weight';
    if (bmi < 18.5) bmiCat = 'Underweight';
    else if (bmi >= 25 && bmi < 29.9) bmiCat = 'Overweight';
    else if (bmi >= 30) bmiCat = 'Obese';

    // BMR (Mifflin-St Jeor)
    let bmr = 10 * w + 6.25 * formData.height_cm - 5 * formData.age + (formData.gender === 'male' ? 5 : -161);
    bmr = Math.round(bmr);

    const actMults = { sedentary: 1.2, light: 1.375, moderate: 1.55, very_active: 1.725, athlete: 1.9 };
    const tdee = Math.round(bmr * (actMults[formData.activity_level] || 1.55));
    const maintenance = tdee;

    let targetCals = tdee;
    if (formData.fitness_goal === 'weight_loss') targetCals = Math.round(tdee - 450);
    else if (formData.fitness_goal === 'muscle_gain') targetCals = Math.round(tdee + 350);

    const proG = Math.round((targetCals * 0.25) / 4);
    const carbG = Math.round((targetCals * 0.50) / 4);
    const fatG = Math.round((targetCals * 0.25) / 9);

    return { bmi, bmiCat, bmr, tdee, maintenance, targetCals, proG, carbG, fatG };
  };

  const bodyMetrics = calculateRealtimeBodyMetrics();

  const steps = [
    { num: 1, title: 'Body' },
    { num: 2, title: 'Fitness & Gym' },
    { num: 3, title: 'Diet & Preferences' },
    { num: 4, title: 'Health Conditions' },
    { num: 5, title: 'Budget' },
    { num: 6, title: 'Lifestyle' },
    { num: 7, title: 'Nutrition Results' },
    { num: 8, title: 'AI Profile' },
    { num: 9, title: 'Generate Diet' }
  ];

  const presetBudgets = [100, 150, 200, 250, 300, 500];

  const handleChange = (field, val) => {
    setFormData((prev) => {
      const updated = { ...prev, [field]: val };
      if (field === 'daily_budget_inr') {
        updated.weekly_budget_inr = val * 7;
      }
      return updated;
    });
  };

  const handleConditionToggle = (code) => {
    setFormData((prev) => {
      let current = [...prev.selected_conditions];
      if (code === 'none') {
        current = ['none'];
      } else {
        current = current.filter((c) => c !== 'none');
        if (current.includes(code)) {
          current = current.filter((c) => c !== code);
          if (current.length === 0) current = ['none'];
        } else {
          current.push(code);
        }
      }
      return { ...prev, selected_conditions: current };
    });
  };

  const handleCompleteAssessment = async () => {
    setSaving(true);
    try {
      const token = localStorage.getItem('nutritwin_token');
      const headers = {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      };

      const onboardRes = await fetch('/api/v1/profile/onboard', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          age: formData.age,
          gender: formData.gender,
          height_cm: formData.height_cm,
          current_weight_kg: formData.current_weight_kg,
          target_weight_kg: formData.target_weight_kg,
          activity_level: formData.activity_level,
          fitness_goal: formData.fitness_goal,
          dietary_preference: formData.dietary_preference,
          daily_budget_inr: formData.daily_budget_inr,
          weekly_budget_inr: formData.weekly_budget_inr,
          location_region: 'North India',
          allergies: formData.allergies,
          medical_conditions: formData.selected_conditions,
          liked_foods: formData.liked_foods,
          disliked_foods: formData.disliked_foods
        })
      });

      if (onboardRes.ok) {
        const pData = await onboardRes.json();
        if (onProfileUpdated) onProfileUpdated(pData);
      }

      const healthRes = await fetch('/api/v1/health/profile', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          selected_conditions: formData.selected_conditions,
          not_sure_guidance_requested: formData.not_sure_guidance_requested,
          condition_details: formData.condition_details,
          daily_steps: formData.daily_steps,
          exercise_frequency: `${formData.gym_days_per_week} days/week`,
          workout_type: formData.workout_type,
          workout_duration_mins: formData.workout_duration_mins,
          workout_time: formData.workout_time
        })
      });

      if (healthRes.ok) {
        const hData = await healthRes.json();
        setHealthProfileResult(hData);
      }

      setCurrentStep(7);
    } catch (err) {
      console.error('Error submitting onboarding data:', err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 pb-12 space-y-6">
      {/* STEP 0: Guided Landing Screen */}
      {currentStep === 0 && (
        <div className="space-y-6">
          <div className="glass-panel p-8 text-center space-y-4 border-b-4 border-b-emerald-500">
            <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mx-auto">
              <HeartPulse className="w-8 h-8" />
            </div>
            <h2 className="text-3xl font-extrabold text-white">Let's Build Your Personalized Diet</h2>
            <p className="text-gray-300 max-w-xl mx-auto text-sm leading-relaxed">
              NutriTwin needs a few details to create a 7-day personalized Indian meal plan tailored to your body, health conditions, fitness goals, and food budget.
            </p>
            <p className="text-xs text-gray-500">Takes about 3 minutes • All fields are optional except budget</p>
          </div>

          {/* What you'll fill in */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[
              { icon: '🧍', title: 'Step 1 — Body Details', desc: 'Height, weight, age, gender, and target weight. We instantly calculate your BMI, BMR, and daily calorie needs.' },
              { icon: '🏋️', title: 'Step 2 — Fitness & Gym', desc: 'Your goal (fat loss, muscle gain), activity level, whether you go to the gym, and workout timing.' },
              { icon: '🥗', title: 'Step 3 — Diet Preference', desc: 'Vegetarian, vegan, or non-vegetarian. Foods you like, dislike, and any allergies.' },
              { icon: '❤️', title: 'Step 4 — Health Conditions', desc: 'Select any diagnosed conditions like Diabetes, Hypertension, or PCOS. Your plan will be adjusted accordingly.' },
              { icon: '💰', title: 'Step 5 — Daily Budget', desc: 'Set your daily food budget (₹100 to ₹500+). The planner strictly stays within this limit.' },
              { icon: '🌙', title: 'Step 6 — Lifestyle', desc: 'Sleep schedule, wake-up time, and work hours help personalize your meal timing.' },
            ].map((item) => (
              <div key={item.title} className="glass-panel p-5 space-y-2">
                <span className="text-2xl">{item.icon}</span>
                <h4 className="font-bold text-white text-sm">{item.title}</h4>
                <p className="text-xs text-gray-400 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>

          <div className="glass-panel p-5 flex flex-col sm:flex-row items-center justify-between gap-4 border border-emerald-500/30">
            <div>
              <p className="font-semibold text-white text-sm">After completing the form:</p>
              <p className="text-xs text-gray-400 mt-1">NutriTwin calculates your nutrition targets → applies your health requirements → generates a complete 7-day Indian meal plan within your budget.</p>
            </div>
            <button onClick={() => setCurrentStep(1)} className="btn-primary py-3 px-8 text-sm whitespace-nowrap">
              Start Building My Diet <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* 9-Step Progress Indicator (only shown on steps 1–9) */}
      {currentStep >= 1 && (
        <>
          {/* Mobile step info header */}
          <div className="flex sm:hidden items-center justify-between text-xs px-1 text-gray-400">
            <span className="font-bold text-white">Step {currentStep} of 9: <span className="text-emerald-400">{steps.find(s => s.num === currentStep)?.title}</span></span>
            <span>{Math.round((currentStep / 9) * 100)}% Completed</span>
          </div>

          <div className="glass-panel p-2.5 sm:p-3 flex justify-between items-center overflow-x-auto text-xs gap-1.5 no-scrollbar">
            {steps.map((s) => {
              const isActive = currentStep === s.num;
              const isDone = currentStep > s.num;
              return (
                <div key={s.num} className="flex items-center gap-1 whitespace-nowrap shrink-0">
                  <span
                    className={`w-5 h-5 rounded-full flex items-center justify-center font-bold text-[10px] transition ${
                      isDone
                        ? 'bg-emerald-500 text-white'
                        : isActive
                        ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/30'
                        : 'bg-gray-800 text-gray-400 border border-gray-700'
                    }`}
                  >
                    {isDone ? '✓' : s.num}
                  </span>
                  <span className={`font-semibold text-[11px] ${isActive ? 'text-white' : 'text-gray-400'}`}>{s.title}</span>
                  {s.num < 9 && <ChevronRight className="w-3 h-3 text-gray-600 shrink-0" />}
                </div>
              );
            })}
          </div>

      {/* STEP 1: Body Details */}
      {currentStep === 1 && (
        <div className="glass-panel p-6 space-y-5">
          <h3 className="text-base font-bold text-white flex items-center gap-2 border-b border-gray-800 pb-2">
            <User className="w-4 h-4 text-emerald-400" />
            Step 1: Body Details
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="text-xs text-gray-400 block mb-1">Age (Years) *</label>
              <input type="number" value={formData.age} onChange={(e) => handleChange('age', parseInt(e.target.value))} className="form-input" />
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Gender *</label>
              <select value={formData.gender} onChange={(e) => handleChange('gender', e.target.value)} className="form-input">
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Height (cm) *</label>
              <input type="number" value={formData.height_cm} onChange={(e) => handleChange('height_cm', parseFloat(e.target.value))} className="form-input" />
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Current Weight (kg) *</label>
              <input type="number" value={formData.current_weight_kg} onChange={(e) => handleChange('current_weight_kg', parseFloat(e.target.value))} className="form-input" />
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Target Weight (kg) *</label>
              <input type="number" value={formData.target_weight_kg} onChange={(e) => handleChange('target_weight_kg', parseFloat(e.target.value))} className="form-input" />
            </div>
          </div>

          {/* Real-time calculated body metrics card */}
          <div className="bg-gray-900/80 p-4 rounded-xl border border-emerald-500/30 space-y-2">
            <p className="text-xs text-emerald-400 font-bold uppercase tracking-wider">Calculated Body & Energy Requirements</p>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-center text-xs">
              <div className="bg-gray-800/60 p-2.5 rounded-lg">
                <p className="text-[10px] text-gray-400">BMI</p>
                <p className="font-extrabold text-white text-base">{bodyMetrics.bmi}</p>
                <p className="text-[9px] text-emerald-400">{bodyMetrics.bmiCat}</p>
              </div>
              <div className="bg-gray-800/60 p-2.5 rounded-lg">
                <p className="text-[10px] text-gray-400">RESTING CALORIES</p>
                <p className="font-extrabold text-white text-base">{bodyMetrics.bmr} <span className="text-[9px] text-gray-400">kcal</span></p>
              </div>
              <div className="bg-gray-800/60 p-2.5 rounded-lg">
                <p className="text-[10px] text-gray-400">MAINTENANCE CALORIES</p>
                <p className="font-extrabold text-white text-base">{bodyMetrics.maintenance} <span className="text-[9px] text-gray-400">kcal</span></p>
              </div>
              <div className="bg-gray-800/60 p-2.5 rounded-lg">
                <p className="text-[10px] text-gray-400">DAILY CALORIES TARGET</p>
                <p className="font-extrabold text-emerald-400 text-base">{bodyMetrics.targetCals} <span className="text-[9px] text-gray-400">kcal</span></p>
              </div>
              <div className="bg-gray-800/60 p-2.5 rounded-lg">
                <p className="text-[10px] text-gray-400">TARGET WEIGHT</p>
                <p className="font-extrabold text-indigo-400 text-base">{formData.target_weight_kg} <span className="text-[9px] text-gray-400">kg</span></p>
              </div>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button onClick={() => setCurrentStep(2)} className="btn-primary">
              Next: Fitness & Gym <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: Fitness & Gym */}
      {currentStep === 2 && (
        <div className="glass-panel p-6 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2 border-b border-gray-800 pb-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            Step 2: Fitness & Activity Details
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-400 block mb-1">Fitness Goal *</label>
              <select value={formData.fitness_goal} onChange={(e) => handleChange('fitness_goal', e.target.value)} className="form-input">
                <option value="weight_loss">Lose weight / Fat Loss</option>
                <option value="muscle_gain">Gain weight / Build Muscle</option>
                <option value="maintenance">Maintain weight</option>
                <option value="health">Improve health & fitness</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Activity Level *</label>
              <select value={formData.activity_level} onChange={(e) => handleChange('activity_level', e.target.value)} className="form-input">
                <option value="sedentary">Sedentary (Desk Job)</option>
                <option value="light">Lightly active (1-3 days/wk)</option>
                <option value="moderate">Moderately active (3-5 days/wk)</option>
                <option value="very_active">Very active (6-7 days/wk)</option>
                <option value="athlete">Athlete / Heavy Training</option>
              </select>
            </div>
          </div>

          <div className="bg-gray-900/60 p-4 rounded-xl space-y-3 border border-gray-800">
            <div className="flex items-center justify-between">
              <label className="text-xs text-white font-bold">Do you go to the gym or exercise regularly?</label>
              <input
                type="checkbox"
                checked={formData.goes_to_gym}
                onChange={(e) => handleChange('goes_to_gym', e.target.checked)}
                className="w-5 h-5 accent-emerald-500 cursor-pointer"
              />
            </div>

            {formData.goes_to_gym && (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                <div>
                  <label className="text-[11px] text-gray-400 block mb-1">Gym Days / Week</label>
                  <input type="number" min="1" max="7" value={formData.gym_days_per_week} onChange={(e) => handleChange('gym_days_per_week', parseInt(e.target.value))} className="form-input text-xs" />
                </div>
                <div>
                  <label className="text-[11px] text-gray-400 block mb-1">Workout Type</label>
                  <select value={formData.workout_type} onChange={(e) => handleChange('workout_type', e.target.value)} className="form-input text-xs">
                    <option value="Gym / Strength Training">Gym / Strength Training</option>
                    <option value="Cardio / Running">Cardio / Running</option>
                    <option value="Yoga / Pilates">Yoga / Pilates</option>
                    <option value="CrossFit / HIIT">CrossFit / HIIT</option>
                  </select>
                </div>
                <div>
                  <label className="text-[11px] text-gray-400 block mb-1">Workout Timing</label>
                  <select value={formData.workout_time} onChange={(e) => handleChange('workout_time', e.target.value)} className="form-input text-xs">
                    <option value="Evening (6 PM - 8 PM)">Evening (6 PM - 8 PM)</option>
                    <option value="Morning (6 AM - 8 AM)">Morning (6 AM - 8 AM)</option>
                    <option value="Afternoon (12 PM - 2 PM)">Afternoon (12 PM - 2 PM)</option>
                  </select>
                </div>
              </div>
            )}
          </div>

          <div className="flex justify-between pt-2">
            <button onClick={() => setCurrentStep(1)} className="btn-secondary">
              <ChevronLeft className="w-4 h-4" /> Back
            </button>
            <button onClick={() => setCurrentStep(3)} className="btn-primary">
              Next: Diet Preference <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: Diet Preference */}
      {currentStep === 3 && (
        <div className="glass-panel p-6 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2 border-b border-gray-800 pb-2">
            <Sparkles className="w-4 h-4 text-purple-400" />
            Step 3: Diet Preference & Food Likes
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-400 block mb-1">Diet Type *</label>
              <select value={formData.dietary_preference} onChange={(e) => handleChange('dietary_preference', e.target.value)} className="form-input">
                <option value="vegetarian">Vegetarian</option>
                <option value="vegan">Vegan</option>
                <option value="eggetarian">Eggetarian</option>
                <option value="non_vegetarian">Non-Vegetarian</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Meals Per Day</label>
              <select value={formData.meals_per_day} onChange={(e) => handleChange('meals_per_day', parseInt(e.target.value))} className="form-input">
                <option value={3}>3 Meals (Breakfast, Lunch, Dinner)</option>
                <option value={4}>4 Meals (Breakfast, Lunch, Snack, Dinner)</option>
                <option value={5}>5 Meals (+ Pre/Post Workout)</option>
              </select>
            </div>
          </div>

          <div className="flex justify-between pt-2">
            <button onClick={() => setCurrentStep(2)} className="btn-secondary">
              <ChevronLeft className="w-4 h-4" /> Back
            </button>
            <button onClick={() => setCurrentStep(4)} className="btn-primary">
              Next: Health Conditions <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 4: Health Conditions */}
      {currentStep === 4 && (
        <div className="glass-panel p-6 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2 border-b border-gray-800 pb-2">
            <HeartPulse className="w-4 h-4 text-rose-400" />
            Step 4: Diagnosed Health Conditions
          </h3>
          <p className="text-xs text-gray-400">Do you currently have any diagnosed health conditions? (Select all that apply)</p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { code: 'none', label: 'None' },
              { code: 'diabetes', label: 'Diabetes' },
              { code: 'prediabetes', label: 'Prediabetes' },
              { code: 'hypertension', label: 'Hypertension' },
              { code: 'high_cholesterol', label: 'High Cholesterol' },
              { code: 'pcos', label: 'PCOS / PCOD' },
              { code: 'thyroid', label: 'Thyroid Condition' },
              { code: 'anemia', label: 'Anemia' },
              { code: 'heart_condition', label: 'Heart Condition' },
              { code: 'kidney_condition', label: 'Kidney Condition' },
              { code: 'liver_condition', label: 'Liver Condition' },
              { code: 'gi_condition', label: 'GI / Acid Reflux' }
            ].map((c) => {
              const active = formData.selected_conditions.includes(c.code);
              return (
                <div
                  key={c.code}
                  onClick={() => handleConditionToggle(c.code)}
                  className={`p-3 rounded-xl border cursor-pointer text-xs font-semibold flex items-center justify-between transition ${
                    active ? 'bg-rose-500/20 border-rose-500 text-rose-300' : 'bg-gray-900/60 border-gray-800 text-gray-300'
                  }`}
                >
                  <span>{c.label}</span>
                  {active && <span className="text-emerald-400 font-bold">✓</span>}
                </div>
              );
            })}
          </div>

          <div className="flex justify-between pt-2">
            <button onClick={() => setCurrentStep(3)} className="btn-secondary">
              <ChevronLeft className="w-4 h-4" /> Back
            </button>
            <button onClick={() => setCurrentStep(5)} className="btn-primary">
              Next: Budget <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 5: Required Budget */}
      {currentStep === 5 && (
        <div className="glass-panel p-6 space-y-4 border-l-4 border-l-cyan-400">
          <h3 className="text-base font-bold text-white flex items-center gap-2 border-b border-gray-800 pb-2">
            <DollarSign className="w-4 h-4 text-cyan-400" />
            Step 5: Food Budget (Required for PuLP Optimizer)
          </h3>
          <p className="text-xs text-gray-400">Select your daily food budget limit. The PuLP linear optimizer strictly enforces this limit.</p>

          <div className="space-y-3">
            <label className="text-xs text-gray-400 block font-semibold">Select Preset Daily Budget (INR):</label>
            <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
              {presetBudgets.map((b) => (
                <button
                  type="button"
                  key={b}
                  onClick={() => handleChange('daily_budget_inr', b)}
                  className={`p-3 rounded-xl text-sm font-extrabold border transition ${
                    formData.daily_budget_inr === b
                      ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300 shadow-md shadow-cyan-500/20'
                      : 'bg-gray-900/60 border-gray-800 text-gray-300 hover:border-gray-700'
                  }`}
                >
                  ₹{b}/day
                </button>
              ))}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-3">
              <div>
                <label className="text-xs text-gray-400 block mb-1">Custom Daily Budget (₹ INR)</label>
                <input
                  type="number"
                  value={formData.daily_budget_inr}
                  onChange={(e) => handleChange('daily_budget_inr', parseFloat(e.target.value))}
                  className="form-input"
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Calculated Weekly Budget (₹ INR)</label>
                <input
                  type="number"
                  value={formData.weekly_budget_inr}
                  onChange={(e) => handleChange('weekly_budget_inr', parseFloat(e.target.value))}
                  className="form-input"
                />
              </div>
            </div>
          </div>

          <div className="flex justify-between pt-2">
            <button onClick={() => setCurrentStep(4)} className="btn-secondary">
              <ChevronLeft className="w-4 h-4" /> Back
            </button>
            <button onClick={() => setCurrentStep(6)} className="btn-primary">
              Next: Lifestyle <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 6: Lifestyle */}
      {currentStep === 6 && (
        <div className="glass-panel p-6 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2 border-b border-gray-800 pb-2">
            <Clock className="w-4 h-4 text-indigo-400" />
            Step 6: Lifestyle & Timings
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="text-xs text-gray-400 block mb-1">Sleep Duration (Hours)</label>
              <input type="number" step="0.5" value={formData.sleep_duration_hours} onChange={(e) => handleChange('sleep_duration_hours', parseFloat(e.target.value))} className="form-input" />
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Wake-up Time</label>
              <input type="text" value={formData.wake_up_time} onChange={(e) => handleChange('wake_up_time', e.target.value)} className="form-input" />
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Sleep Time</label>
              <input type="text" value={formData.sleep_time} onChange={(e) => handleChange('sleep_time', e.target.value)} className="form-input" />
            </div>
          </div>

          <div className="flex justify-between pt-2">
            <button onClick={() => setCurrentStep(5)} className="btn-secondary">
              <ChevronLeft className="w-4 h-4" /> Back
            </button>
            <button onClick={handleCompleteAssessment} disabled={saving} className="btn-primary">
              {saving ? 'Calculating...' : 'Calculate Requirements'} <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 7 & 8: Nutrition Results & AI Profile Summary */}
      {currentStep >= 7 && (
        <div className="space-y-6">
          <div className="glass-panel p-6 border-l-4 border-l-emerald-400 space-y-4">
            <div className="flex justify-between items-center border-b border-gray-800 pb-3">
              <div>
                <span className="badge badge-emerald">YOUR DAILY NUTRITION REQUIREMENTS</span>
                <h3 className="text-xl font-bold text-white mt-1">Calculated Daily Target Summary</h3>
              </div>

              <button onClick={() => setCurrentStep(1)} className="btn-secondary text-xs">
                <Edit3 className="w-3.5 h-3.5" /> Edit Information
              </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-center bg-gray-900/80 p-4 rounded-xl border border-gray-800">
              <div>
                <p className="text-[10px] text-gray-400">CALORIES</p>
                <p className="font-extrabold text-white text-lg">{bodyMetrics.targetCals} <span className="text-[10px] text-gray-400">kcal</span></p>
              </div>
              <div>
                <p className="text-[10px] text-gray-400">PROTEIN</p>
                <p className="font-extrabold text-emerald-400 text-lg">{bodyMetrics.proG}g</p>
              </div>
              <div>
                <p className="text-[10px] text-gray-400">CARBS</p>
                <p className="font-extrabold text-indigo-300 text-lg">{bodyMetrics.carbG}g</p>
              </div>
              <div>
                <p className="text-[10px] text-gray-400">FAT</p>
                <p className="font-extrabold text-amber-400 text-lg">{bodyMetrics.fatG}g</p>
              </div>
              <div>
                <p className="text-[10px] text-gray-400">FIBER</p>
                <p className="font-extrabold text-purple-300 text-lg">25-30g</p>
              </div>
              <div>
                <p className="text-[10px] text-gray-400">WATER</p>
                <p className="font-extrabold text-cyan-400 text-lg">{formData.water_intake_target_l} L</p>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs bg-gray-900/50 p-3 rounded-xl">
              <div>
                <span className="text-gray-500">Goal:</span> <strong className="text-white">{formData.fitness_goal.toUpperCase()}</strong>
              </div>
              <div>
                <span className="text-gray-500">Budget:</span> <strong className="text-cyan-400">₹{formData.daily_budget_inr}/day</strong>
              </div>
              <div>
                <span className="text-gray-500">Diet:</span> <strong className="text-emerald-400">{formData.dietary_preference.toUpperCase()}</strong>
              </div>
              <div>
                <span className="text-gray-500">Pathway:</span> <strong className="text-indigo-300">{healthProfileResult?.classified_pathway || 'Diabetes-Aware'}</strong>
              </div>
            </div>
          </div>

          <div className="flex justify-center">
            <button
              onClick={() => {
                if (onGenerateDiet) onGenerateDiet();
              }}
              className="btn-primary py-4 px-10 text-base shadow-xl shadow-emerald-500/25"
            >
              <Calendar className="w-5 h-5" />
              Generate My 7-Day AI Diet Plan
            </button>
          </div>
        </div>
      )}
      </>
      )}
    </div>
  );
}
