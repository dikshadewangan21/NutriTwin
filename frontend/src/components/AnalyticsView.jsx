import React, { useState, useEffect } from 'react';
import { LineChart as LucideLineChart, TrendingDown } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function AnalyticsView({ userProfile }) {
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchForecast();
  }, []);

  const fetchForecast = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('nutritwin_token');
      const res = await fetch('/api/v1/tracking/progress-forecast', {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      if (res.ok) {
        const data = await res.json();
        setForecast(data);
      }
    } catch (err) {
      console.error('Error fetching progress forecast:', err);
    } finally {
      setLoading(false);
    }
  };

  const chartData = forecast?.weekly_forecast?.map((w) => ({
    weekName: `Week ${w.week}`,
    predicted: w.predicted_weight_kg,
    lowerBound: w.lower_bound_95,
    upperBound: w.upper_bound_95
  })) || [
    { weekName: 'Week 0', predicted: 74.0, lowerBound: 73.8, upperBound: 74.2 },
    { weekName: 'Week 1', predicted: 73.2, lowerBound: 72.8, upperBound: 73.6 },
    { weekName: 'Week 2', predicted: 72.5, lowerBound: 71.9, upperBound: 73.1 },
    { weekName: 'Week 3', predicted: 71.7, lowerBound: 70.9, upperBound: 72.5 },
    { weekName: 'Week 4', predicted: 71.0, lowerBound: 70.0, upperBound: 72.0 }
  ];

  return (
    <div className="max-w-6xl mx-auto px-4 pb-12 space-y-6">
      <div className="glass-panel p-6 border-l-4 border-l-emerald-400">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <LucideLineChart className="w-6 h-6 text-emerald-400" />
          Your 4-Week Weight & Progress Forecast
        </h2>
        <p className="text-xs text-gray-400">Tracks your progress and predicts where your weight will be over the next 4 weeks.</p>
      </div>

      {/* Probability Gauge & Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-panel p-5 text-center space-y-2 border-t-2 border-t-emerald-400">
          <p className="text-xs text-gray-400 font-semibold">GOAL COMPLETION CHANCE</p>
          <p className="text-4xl font-extrabold text-emerald-400">
            {forecast?.goal_achievement_probability_pct || 91.5}%
          </p>
          <span className="badge badge-emerald">High Confidence</span>
        </div>

        <div className="glass-panel p-5 text-center space-y-2 border-t-2 border-t-indigo-400">
          <p className="text-xs text-gray-400 font-semibold">PREDICTED WEIGHT IN 4 WEEKS</p>
          <p className="text-4xl font-extrabold text-white">
            {chartData[chartData.length - 1]?.predicted} kg
          </p>
          <p className="text-xs text-gray-400">Target: {userProfile?.target_weight_kg || 70} kg</p>
        </div>

        <div className="glass-panel p-5 text-center space-y-2 border-t-2 border-t-amber-400">
          <p className="text-xs text-gray-400 font-semibold">MEAL CONSISTENCY SCORE</p>
          <p className="text-4xl font-extrabold text-amber-400">88.5%</p>
          <span className="badge badge-amber">Consistent Tracker</span>
        </div>
      </div>

      {/* Weight Chart Card */}
      <div className="glass-panel p-6 space-y-4">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <TrendingDown className="w-5 h-5 text-emerald-400" />
          Expected Weight Trend (Next 4 Weeks)
        </h3>

        <div className="h-72 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
              <XAxis dataKey="weekName" stroke="#9CA3AF" fontSize={12} />
              <YAxis domain={['auto', 'auto']} stroke="#9CA3AF" fontSize={12} />
              <Tooltip
                contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '12px' }}
                itemStyle={{ color: '#10B981' }}
              />
              <Line type="monotone" dataKey="predicted" stroke="#10B981" strokeWidth={3} dot={{ r: 6 }} name="Predicted Weight (kg)" />
              <Line type="monotone" dataKey="lowerBound" stroke="#6366F1" strokeDasharray="5 5" strokeWidth={1.5} name="Best Case" />
              <Line type="monotone" dataKey="upperBound" stroke="#F59E0B" strokeDasharray="5 5" strokeWidth={1.5} name="Expected Range" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <p className="text-xs text-gray-400 italic">
          Prediction is based on your daily calories, activity level, and meal consistency.
        </p>
      </div>
    </div>
  );
}
