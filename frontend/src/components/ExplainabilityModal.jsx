import React, { useState, useEffect } from 'react';
import { X, Sparkles, CheckCircle } from 'lucide-react';

export default function ExplainabilityModal({ foodId, isOpen, onClose }) {
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isOpen && foodId) {
      fetchExplanation();
    }
  }, [isOpen, foodId]);

  const fetchExplanation = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('nutritwin_token');
      const res = await fetch(`/api/v1/recommend/explain/${foodId}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      if (res.ok) {
        const data = await res.json();
        setExplanation(data);
      }
    } catch (err) {
      console.error('Error fetching explanation:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const getCleanFeatureName = (name) => {
    if (name.includes('Macros') || name.includes('Nutritional')) return 'Matches Your Daily Nutrition Needs';
    if (name.includes('Taste') || name.includes('Preference')) return 'Matches Your Taste & Favorite Foods';
    if (name.includes('Budget')) return 'Fits Comfortably in Your Budget';
    if (name.includes('Variety') || name.includes('Diversity')) return 'Adds Variety to Your Meals';
    if (name.includes('Local') || name.includes('Regional')) return 'Uses Popular Regional Ingredients';
    return name;
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-3 sm:p-4">
      <div className="glass-panel w-full max-w-xl p-4 sm:p-6 space-y-4 sm:space-y-6 border-2 border-emerald-500/40 shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center border-b border-gray-800 pb-3">
          <div>
            <span className="badge badge-emerald text-[10px]">Why This Meal Was Chosen</span>
            <h3 className="text-xl font-bold text-white mt-1">{explanation?.food_name || 'Food Recommendation'}</h3>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        {loading ? (
          <div className="text-center py-8 text-gray-400 text-xs">Analyzing meal highlights...</div>
        ) : (
          <div className="space-y-6">
            {/* Feature Contribution Bars */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-gray-300 uppercase tracking-wider">Nutrition & Match Highlights</h4>

              {explanation?.shap_feature_contributions?.map((feat, idx) => (
                <div key={idx} className="space-y-1">
                  <div className="flex justify-between text-xs font-medium">
                    <span className="text-gray-300">{getCleanFeatureName(feat.feature)}</span>
                    <span className="text-emerald-400 font-bold">+{feat.contribution_pct}%</span>
                  </div>
                  <div className="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-emerald-500 to-teal-400 h-full rounded-full"
                      style={{ width: `${feat.contribution_pct}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>

            {/* Bullet Reasons */}
            <div className="space-y-2 bg-gray-900/60 p-4 rounded-xl border border-gray-800">
              <h4 className="text-xs font-bold text-white flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-emerald-400" />
                Why NutriTwin Picked This Meal:
              </h4>

              <ul className="space-y-2 text-xs text-gray-300">
                {explanation?.explanation_bullets?.map((bullet, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
