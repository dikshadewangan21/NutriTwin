import React, { useState, useEffect } from 'react';
import { Flame, Activity, Sparkles, Plus, Info, DollarSign, Dumbbell, Edit3 } from 'lucide-react';

export default function Dashboard({ userProfile, onOpenExplain, onLogMeal, onViewPlanner, onEditProfile }) {
  const [todayData, setTodayData] = useState(null);
  const [dailyRecs, setDailyRecs] = useState(null);
  const [healthSummary, setHealthSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, [userProfile]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('nutritwin_token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};

      const [logRes, recRes, healthRes] = await Promise.all([
        fetch('/api/v1/tracking/today', { headers }),
        fetch('/api/v1/recommend/daily', { headers }),
        fetch('/api/v1/health/nutrition-profile', { headers })
      ]);

      if (logRes.ok) {
        const data = await logRes.json();
        setTodayData(data);
      }
      if (recRes.ok) {
        const rdata = await recRes.json();
        setDailyRecs(rdata.recommendations_by_meal);
      }
      if (healthRes.ok) {
        const hdata = await healthRes.json();
        setHealthSummary(hdata.health_summary);
      }
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLog = async (foodId) => {
    const token = localStorage.getItem('nutritwin_token');
    await fetch(`/api/v1/tracking/log-meal?food_id=${foodId}&servings=1.0`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    });
    fetchDashboardData();
  };

  const targets = todayData?.targets || { calories: 1750, protein_g: 110, carbs_g: 190, fat_g: 55, water_l: 2.8 };
  const current = todayData || { total_calories: 680, total_protein_g: 45, total_carbs_g: 75, total_fat_g: 20, water_ml: 1400 };

  const calPct = Math.min(100, Math.round((current.total_calories / targets.calories) * 100));
  const proPct = Math.min(100, Math.round((current.total_protein_g / targets.protein_g) * 100));
  const carbPct = Math.min(100, Math.round((current.total_carbs_g / targets.carbs_g) * 100));

  return (
    <div className="space-y-6 max-w-7xl mx-auto px-4 pb-12">
      {/* Header Banner */}
      <div className="glass-panel p-4 sm:p-6 relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between gap-4 sm:gap-6 border-l-4 border-l-emerald-500">
        <div className="space-y-2 z-10">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="badge badge-emerald">Smart Personal Assistant</span>
            <span className="text-xs text-gray-400">Updated today</span>
          </div>
          <h2 className="text-xl sm:text-2xl md:text-3xl font-extrabold text-white leading-tight">
            Welcome back, <span className="text-emerald-400">{userProfile?.full_name || 'Fitness Enthusiast'}</span>
          </h2>
          <p className="text-xs sm:text-sm text-gray-300 max-w-2xl">
            {todayData?.adaptive_adherence?.insight || "Your personal assistant is tracking your daily nutrition and organizing your ideal meal balance."}
          </p>
        </div>

        <div className="flex items-center gap-3 z-10 w-full md:w-auto">
          <button onClick={onViewPlanner} className="btn-primary w-full md:w-auto justify-center text-xs sm:text-sm py-2.5 px-4">
            <Sparkles className="w-4 h-4" />
            Generate 7-Day Plan
          </button>
        </div>
      </div>

      {/* MY NUTRITION PROFILE Card */}
      <div className="glass-panel p-4 sm:p-5 border-l-4 border-l-indigo-500 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-800 pb-2">
          <h3 className="text-sm sm:text-base font-bold text-white flex items-center gap-2">
            <Dumbbell className="w-4 h-4 sm:w-5 sm:h-5 text-indigo-400 shrink-0" />
            MY NUTRITION PROFILE
          </h3>

          <div className="flex items-center gap-2">
            <span className="badge badge-indigo text-[10px] sm:text-xs">{healthSummary?.classified_pathway || 'General Health'}</span>
            <button onClick={onEditProfile} className="btn-secondary py-1 px-2.5 sm:py-1.5 sm:px-3 text-xs">
              <Edit3 className="w-3.5 h-3.5" /> Edit Profile
            </button>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2.5 sm:gap-3 text-xs bg-gray-900/60 p-3 rounded-xl min-w-0">
          <div className="min-w-0">
            <p className="text-gray-500 text-[10px] sm:text-xs">HEIGHT</p>
            <p className="font-bold text-white truncate">{userProfile?.height_cm ? `${userProfile.height_cm} cm` : '—'}</p>
          </div>
          <div className="min-w-0">
            <p className="text-gray-500 text-[10px] sm:text-xs">WEIGHT</p>
            <p className="font-bold text-white truncate">{userProfile?.current_weight_kg ? `${userProfile.current_weight_kg} kg` : '—'}</p>
          </div>
          <div className="min-w-0">
            <p className="text-gray-500 text-[10px] sm:text-xs">TARGET</p>
            <p className="font-bold text-indigo-300 truncate">{userProfile?.target_weight_kg ? `${userProfile.target_weight_kg} kg` : '—'}</p>
          </div>
          <div className="min-w-0">
            <p className="text-gray-500 text-[10px] sm:text-xs">GOAL</p>
            <p className="font-bold text-emerald-400 truncate">{userProfile?.fitness_goal ? userProfile.fitness_goal.replace('_', ' ').toUpperCase() : 'HEALTH'}</p>
          </div>
          <div className="min-w-0">
            <p className="text-gray-500 text-[10px] sm:text-xs">GYM / ACTIVITY</p>
            <p className="font-bold text-white truncate">{healthSummary?.workout_type || (userProfile?.activity_level ? userProfile.activity_level.replace('_', ' ').toUpperCase() : 'MODERATE')}</p>
          </div>
          <div className="min-w-0">
            <p className="text-gray-500 text-[10px] sm:text-xs">DIET</p>
            <p className="font-bold text-indigo-300 truncate">{(userProfile?.dietary_preference || healthSummary?.dietary_preference || 'FLEXIBLE').toUpperCase()}</p>
          </div>
          <div className="min-w-0">
            <p className="text-gray-500 text-[10px] sm:text-xs">HEALTH</p>
            <p className="font-bold text-rose-300 truncate">
              {healthSummary?.selected_conditions?.filter(c => c && c !== 'none')?.length > 0
                ? healthSummary.selected_conditions.filter(c => c && c !== 'none').join(', ')
                : (userProfile?.medical_conditions?.filter(c => c && c !== 'none')?.length > 0
                  ? userProfile.medical_conditions.filter(c => c && c !== 'none').join(', ')
                  : 'General Health')}
            </p>
          </div>
          <div className="min-w-0">
            <p className="text-gray-500 text-[10px] sm:text-xs">BUDGET</p>
            <p className="font-bold text-cyan-400 truncate">₹{userProfile?.daily_budget_inr || healthSummary?.daily_budget_inr || 250}/day</p>
          </div>
        </div>
      </div>

      {/* Daily Progress Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Calories */}
        <div className="glass-panel p-5 space-y-3">
          <div className="flex justify-between items-center text-xs text-gray-400 font-medium">
            <span>CALORIES EATEN TODAY</span>
            <Flame className="w-4 h-4 text-amber-500" />
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-extrabold text-white">{Math.round(current.total_calories)}</span>
            <span className="text-xs text-gray-400">/ {targets.calories} kcal</span>
          </div>
          <div className="w-full bg-gray-800 h-2.5 rounded-full overflow-hidden">
            <div className="bg-gradient-to-r from-amber-500 to-orange-500 h-full rounded-full transition-all duration-500" style={{ width: `${calPct}%` }}></div>
          </div>
          <p className="text-[11px] text-gray-400 text-right">{100 - calPct}% remaining today</p>
        </div>

        {/* Protein */}
        <div className="glass-panel p-5 space-y-3">
          <div className="flex justify-between items-center text-xs text-gray-400 font-medium">
            <span>PROTEIN TARGET</span>
            <Activity className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-extrabold text-emerald-400">{Math.round(current.total_protein_g)}g</span>
            <span className="text-xs text-gray-400">/ {targets.protein_g}g</span>
          </div>
          <div className="w-full bg-gray-800 h-2.5 rounded-full overflow-hidden">
            <div className="bg-gradient-to-r from-emerald-400 to-teal-500 h-full rounded-full transition-all duration-500" style={{ width: `${proPct}%` }}></div>
          </div>
          <p className="text-[11px] text-emerald-400/90 text-right">{proPct}% target met</p>
        </div>

        {/* Carbs */}
        <div className="glass-panel p-5 space-y-3">
          <div className="flex justify-between items-center text-xs text-gray-400 font-medium">
            <span>CARBS (ENERGY)</span>
            <span className="text-indigo-400 text-xs font-semibold">ENERGY</span>
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-extrabold text-white">{Math.round(current.total_carbs_g)}g</span>
            <span className="text-xs text-gray-400">/ {targets.carbs_g}g</span>
          </div>
          <div className="w-full bg-gray-800 h-2.5 rounded-full overflow-hidden">
            <div className="bg-gradient-to-r from-indigo-500 to-blue-500 h-full rounded-full transition-all duration-500" style={{ width: `${carbPct}%` }}></div>
          </div>
          <p className="text-[11px] text-gray-400 text-right">{carbPct}% used</p>
        </div>

        {/* Budget */}
        <div className="glass-panel p-5 space-y-3">
          <div className="flex justify-between items-center text-xs text-gray-400 font-medium">
            <span>DAILY BUDGET</span>
            <DollarSign className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-extrabold text-cyan-400">₹{userProfile?.daily_budget_inr || 250}</span>
            <span className="text-xs text-gray-400">Target / Day</span>
          </div>
          <div className="w-full bg-gray-800 h-2.5 rounded-full overflow-hidden">
            <div className="bg-gradient-to-r from-cyan-400 to-emerald-400 h-full rounded-full" style={{ width: '65%' }}></div>
          </div>
          <p className="text-[11px] text-cyan-400 text-right">~₹110 remaining</p>
        </div>
      </div>

      {/* Recommended Meals Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-emerald-400" />
              Recommended Meals for Today
            </h3>
            <p className="text-xs text-gray-400">Personalized to match your fitness goals, health pathway, taste, and budget</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {['breakfast', 'lunch', 'dinner', 'snack'].map((slot) => {
            const topOption = dailyRecs?.[slot]?.[0];
            const food = topOption?.food;
            if (!food) return null;

            return (
              <div key={slot} className="glass-panel p-5 flex flex-col justify-between space-y-4 border-t-2 border-t-emerald-500/50">
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="badge badge-indigo text-[10px]">{slot.toUpperCase()}</span>
                    <span className="text-xs font-bold text-emerald-400">
                      {Math.round(topOption.recommendation_score * 100)}% Match
                    </span>
                  </div>
                  <h4 className="font-bold text-white text-base leading-snug">{food.name}</h4>
                  <p className="text-xs text-gray-400">{food.serving_unit} • ₹{food.approx_cost_inr}</p>

                  <div className="grid grid-cols-3 gap-1 bg-gray-900/60 p-2 rounded-xl text-center text-xs">
                    <div>
                      <p className="text-[10px] text-gray-500">CALS</p>
                      <p className="font-bold text-white">{food.calories}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-gray-500">PRO</p>
                      <p className="font-bold text-emerald-400">{food.protein_g}g</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-gray-500">CARB</p>
                      <p className="font-bold text-indigo-300">{food.carbs_g}g</p>
                    </div>
                  </div>
                </div>

                <div className="space-y-2 pt-2 border-t border-gray-800">
                  <button
                    onClick={() => onOpenExplain(food.id)}
                    className="w-full text-xs text-gray-400 hover:text-emerald-400 flex items-center justify-center gap-1 transition"
                  >
                    <Info className="w-3.5 h-3.5" />
                    Why this meal was picked
                  </button>

                  <button
                    onClick={() => handleQuickLog(food.id)}
                    className="w-full btn-primary py-2 text-xs justify-center"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    Log Meal Intake
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
