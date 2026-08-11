import React, { useState, useEffect } from 'react';
import { Calendar, RefreshCw, ArrowRightLeft, Info, ShieldCheck } from 'lucide-react';

const MEAL_ORDER = ['breakfast', 'pre_workout', 'post_workout', 'lunch', 'snack', 'dinner'];
const MEAL_COLORS = {
  breakfast: 'badge-amber',
  pre_workout: 'badge-indigo',
  post_workout: 'badge-emerald',
  lunch: 'badge-emerald',
  snack: 'badge-indigo',
  dinner: 'badge-purple',
};
const MEAL_LABELS = {
  breakfast: 'Breakfast',
  pre_workout: 'Pre-Workout',
  post_workout: 'Post-Workout',
  lunch: 'Lunch',
  snack: 'Snack',
  dinner: 'Dinner',
};

export default function MealPlanner({ userProfile, onOpenSubstitute }) {
  const [selectedDay, setSelectedDay] = useState('Monday');
  const [planData, setPlanData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expandedMeal, setExpandedMeal] = useState(null);

  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

  useEffect(() => {
    generatePlan();
  }, [userProfile]);

  const generatePlan = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('nutritwin_token');
      const res = await fetch('/api/v1/optimize/7-day-plan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ start_date: new Date().toISOString().split('T')[0], num_days: 7 })
      });
      if (res.ok) {
        const data = await res.json();
        setPlanData(data);
      } else {
        console.error('Failed to generate plan:', await res.text());
      }
    } catch (err) {
      console.error('Error generating meal plan:', err);
    } finally {
      setLoading(false);
    }
  };

  const currentDayPlan = planData?.days?.find((d) => d.day_name === selectedDay);

  // Sort meals in proper meal-time order for the selected day
  const sortedMeals = currentDayPlan?.meals
    ? [...currentDayPlan.meals].sort(
        (a, b) => MEAL_ORDER.indexOf(a.meal_type) - MEAL_ORDER.indexOf(b.meal_type)
      )
    : [];

  // Per-day totals
  const dayTotals = sortedMeals.reduce(
    (acc, m) => ({
      calories: acc.calories + (m.calories || 0),
      protein_g: acc.protein_g + (m.protein_g || 0),
      carbs_g: acc.carbs_g + (m.carbs_g || 0),
      cost_inr: acc.cost_inr + (m.cost_inr || 0),
    }),
    { calories: 0, protein_g: 0, carbs_g: 0, cost_inr: 0 }
  );

  return (
    <div className="max-w-7xl mx-auto px-4 pb-12 space-y-6">
      {/* Top Banner */}
      <div className="glass-panel p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 border-l-4 border-l-emerald-500">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="badge badge-emerald">Smart Weekly Diet Planner</span>
            {planData?.health_pathway && planData.health_pathway !== 'General Wellness Pathway' && (
              <span className="badge badge-rose flex items-center gap-1">
                <ShieldCheck className="w-3 h-3" />
                {planData.health_pathway}
              </span>
            )}
          </div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2 mt-1">
            <Calendar className="w-6 h-6 text-emerald-400" />
            Your 7-Day Personal Meal Plan
          </h2>
          <p className="text-xs text-gray-400">
            Automatically balances nutrition, stays within ₹{userProfile?.daily_budget_inr || 250}/day budget, and varies meals each day.
          </p>
        </div>

        <button onClick={generatePlan} disabled={loading} className="btn-primary">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Building your 7-day plan...' : 'Regenerate Plan'}
        </button>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="glass-panel p-12 text-center space-y-3">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto text-emerald-400" />
          <p className="text-white font-semibold">
            Building your personalized 7-day diet plan...
          </p>
          <p className="text-xs text-gray-400">
            Applying your health profile, budget constraints, and food preferences.
          </p>
        </div>
      )}

      {/* Plan Summary Ribbon */}
      {!loading && planData?.summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="glass-panel p-4 text-center">
            <p className="text-xs text-gray-400">AVG DAILY CALORIES</p>
            <p className="text-xl font-bold text-white">{planData.summary.avg_daily_calories} kcal</p>
          </div>
          <div className="glass-panel p-4 text-center">
            <p className="text-xs text-gray-400">AVG DAILY PROTEIN</p>
            <p className="text-xl font-bold text-emerald-400">{planData.summary.avg_daily_protein_g}g</p>
          </div>
          <div className="glass-panel p-4 text-center">
            <p className="text-xs text-gray-400">EST. WEEKLY COST</p>
            <p className="text-xl font-bold text-cyan-400">₹{planData.summary.total_weekly_cost_inr}</p>
          </div>
          <div className="glass-panel p-4 text-center">
            <p className="text-xs text-gray-400">DAILY BUDGET LIMIT</p>
            <p className="text-xl font-bold text-amber-400">₹{planData.summary.daily_budget_target_inr}</p>
          </div>
        </div>
      )}

      {/* Day Tabs */}
      {!loading && (
        <div className="flex gap-2 overflow-x-auto pb-2 border-b border-gray-800">
          {days.map((day) => {
            const dayPlanData = planData?.days?.find((d) => d.day_name === day);
            const hasMeals = dayPlanData?.meals?.length > 0;
            return (
              <button
                key={day}
                onClick={() => setSelectedDay(day)}
                className={`px-5 py-2.5 rounded-xl font-semibold text-xs transition whitespace-nowrap ${
                  selectedDay === day
                    ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/20'
                    : 'bg-gray-900/60 text-gray-400 hover:text-white border border-gray-800'
                }`}
              >
                {day}
                {hasMeals && selectedDay !== day && (
                  <span className="ml-1.5 w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block"></span>
                )}
              </button>
            );
          })}
        </div>
      )}

      {/* Day Totals Bar */}
      {!loading && sortedMeals.length > 0 && (
        <div className="glass-panel p-4 flex flex-wrap gap-4 items-center justify-between text-xs">
          <span className="font-bold text-white text-sm">{selectedDay}'s Totals</span>
          <div className="flex gap-4 flex-wrap">
            <span><span className="text-gray-400">Calories:</span> <strong className="text-white">{Math.round(dayTotals.calories)} kcal</strong></span>
            <span><span className="text-gray-400">Protein:</span> <strong className="text-emerald-400">{Math.round(dayTotals.protein_g)}g</strong></span>
            <span><span className="text-gray-400">Carbs:</span> <strong className="text-indigo-300">{Math.round(dayTotals.carbs_g)}g</strong></span>
            <span><span className="text-gray-400">Est. Cost:</span> <strong className="text-cyan-400">₹{dayTotals.cost_inr.toFixed(0)}</strong></span>
            <span className={`font-semibold ${dayTotals.cost_inr <= (userProfile?.daily_budget_inr || 250) ? 'text-emerald-400' : 'text-rose-400'}`}>
              {dayTotals.cost_inr <= (userProfile?.daily_budget_inr || 250) ? '✓ Within Budget' : '⚠ Over Budget'}
            </span>
          </div>
        </div>
      )}

      {/* Meals Grid for Selected Day */}
      {!loading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {sortedMeals.length > 0 ? sortedMeals.map((meal) => (
            <div key={meal.item_id} className="glass-panel p-5 space-y-4 flex flex-col justify-between border-t-2 border-t-emerald-500/40">
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className={`badge ${MEAL_COLORS[meal.meal_type] || 'badge-indigo'} text-[10px]`}>
                    {MEAL_LABELS[meal.meal_type] || meal.meal_type.toUpperCase()}
                  </span>
                  <span className="text-xs text-cyan-400 font-bold">₹{meal.cost_inr}</span>
                </div>

                <h4 className="font-bold text-white text-base leading-snug">{meal.food_name}</h4>

                <div className="grid grid-cols-4 gap-1 bg-gray-900/60 p-2.5 rounded-xl text-center text-xs">
                  <div>
                    <p className="text-[10px] text-gray-500">CALS</p>
                    <p className="font-bold text-white">{meal.calories}</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-gray-500">PRO</p>
                    <p className="font-bold text-emerald-400">{meal.protein_g}g</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-gray-500">CARB</p>
                    <p className="font-bold text-indigo-300">{meal.carbs_g}g</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-gray-500">FAT</p>
                    <p className="font-bold text-amber-400">{meal.fat_g}g</p>
                  </div>
                </div>

                {/* Why this meal */}
                {meal.explanation && (
                  <button
                    onClick={() => setExpandedMeal(expandedMeal === meal.item_id ? null : meal.item_id)}
                    className="w-full text-left text-[11px] text-indigo-300 hover:text-indigo-200 flex items-center gap-1 transition"
                  >
                    <Info className="w-3 h-3 shrink-0" />
                    {expandedMeal === meal.item_id ? 'Hide reason' : 'Why this meal was picked'}
                  </button>
                )}
                {expandedMeal === meal.item_id && meal.explanation && (
                  <div className="bg-indigo-950/50 border border-indigo-500/30 p-2.5 rounded-xl text-[11px] text-indigo-200 leading-relaxed">
                    {meal.explanation}
                  </div>
                )}
              </div>

              <div className="pt-2 border-t border-gray-800">
                <button
                  onClick={() => onOpenSubstitute(meal.food_id)}
                  className="w-full btn-secondary py-2 text-xs justify-center hover:border-emerald-500/50"
                >
                  <ArrowRightLeft className="w-3.5 h-3.5" />
                  Swap Ingredient / Dish
                </button>
              </div>
            </div>
          )) : (
            <div className="col-span-3 glass-panel p-12 text-center text-gray-400 space-y-2">
              <Calendar className="w-10 h-10 mx-auto text-gray-600" />
              <p className="font-semibold">No meals planned for {selectedDay} yet.</p>
              <button onClick={generatePlan} className="btn-primary mt-2">
                Generate Meal Plan
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
