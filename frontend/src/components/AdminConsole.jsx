import React, { useState, useEffect } from 'react';
import { Shield, Database, Search, Filter } from 'lucide-react';

const CATEGORY_COLORS = {
  breakfast: 'badge-amber',
  lunch: 'badge-emerald',
  dinner: 'badge-purple',
  snack: 'badge-indigo',
  pre_workout: 'badge-rose',
  post_workout: 'badge-cyan',
};

export default function AdminConsole() {
  const [foodItems, setFoodItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');

  useEffect(() => {
    fetchAdminData();
  }, []);

  const fetchAdminData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('nutritwin_token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const fRes = await fetch('/api/v1/admin/food-items', { headers });
      if (fRes.ok) setFoodItems(await fRes.json());
    } catch (err) {
      console.error('Error fetching food data:', err);
    } finally {
      setLoading(false);
    }
  };

  const categories = ['all', ...Array.from(new Set(foodItems.map(f => f.category))).sort()];

  const filtered = foodItems.filter(item => {
    const matchesSearch = !search || item.name.toLowerCase().includes(search.toLowerCase()) ||
      (item.dietary_type || '').toLowerCase().includes(search.toLowerCase()) ||
      (item.cuisine || '').toLowerCase().includes(search.toLowerCase());
    const matchesCat = categoryFilter === 'all' || item.category === categoryFilter;
    return matchesSearch && matchesCat;
  });

  const stats = {
    total: foodItems.length,
    breakfast: foodItems.filter(f => f.category === 'breakfast').length,
    lunch: foodItems.filter(f => f.category === 'lunch').length,
    dinner: foodItems.filter(f => f.category === 'dinner').length,
    snack: foodItems.filter(f => f.category === 'snack').length,
    pre_post: foodItems.filter(f => ['pre_workout','post_workout'].includes(f.category)).length,
  };

  return (
    <div className="max-w-7xl mx-auto px-4 pb-12 space-y-6">
      {/* Header */}
      <div className="glass-panel p-6 border-l-4 border-l-purple-500">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Shield className="w-6 h-6 text-purple-400" />
          System Management & Food Database
        </h2>
        <p className="text-xs text-gray-400 mt-1">Complete Indian nutrition knowledge base for diet planning and AI recommendations.</p>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {[
          { label: 'Total Dishes', value: stats.total, color: 'text-white' },
          { label: 'Breakfast', value: stats.breakfast, color: 'text-amber-400' },
          { label: 'Lunch', value: stats.lunch, color: 'text-emerald-400' },
          { label: 'Dinner', value: stats.dinner, color: 'text-purple-400' },
          { label: 'Snacks', value: stats.snack, color: 'text-indigo-400' },
          { label: 'Workout', value: stats.pre_post, color: 'text-rose-400' },
        ].map((s) => (
          <div key={s.label} className="glass-panel p-4 text-center">
            <p className={`text-2xl font-extrabold ${s.color}`}>{s.value}</p>
            <p className="text-[10px] text-gray-500 uppercase tracking-wider mt-1">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Food DB */}
      <div className="glass-panel p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Database className="w-5 h-5 text-emerald-400" />
            Indian Food Knowledge Base
            <span className="badge badge-emerald ml-1">{filtered.length} of {foodItems.length} Dishes</span>
          </h3>

          {/* Filters */}
          <div className="flex gap-2 flex-wrap">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
              <input
                type="text"
                placeholder="Search dish, cuisine..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="form-input pl-8 py-1.5 text-xs w-48"
              />
            </div>
            <select
              value={categoryFilter}
              onChange={e => setCategoryFilter(e.target.value)}
              className="form-input py-1.5 text-xs"
            >
              {categories.map(c => (
                <option key={c} value={c}>{c === 'all' ? 'All Categories' : c.charAt(0).toUpperCase() + c.slice(1).replace('_', ' ')}</option>
              ))}
            </select>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-500 text-sm">Loading food database...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-gray-300">
              <thead className="bg-gray-900/80 text-gray-400 uppercase text-[10px]">
                <tr>
                  <th className="p-3">#</th>
                  <th className="p-3">Dish Name</th>
                  <th className="p-3">Category</th>
                  <th className="p-3">Dietary</th>
                  <th className="p-3">Cuisine</th>
                  <th className="p-3">Calories</th>
                  <th className="p-3">Protein</th>
                  <th className="p-3">Carbs</th>
                  <th className="p-3">Fat</th>
                  <th className="p-3">Cost (₹)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {filtered.map((item, idx) => (
                  <tr key={item.id} className="hover:bg-gray-900/50 transition-colors">
                    <td className="p-3 text-gray-600">{idx + 1}</td>
                    <td className="p-3">
                      <p className="font-semibold text-white">{item.name}</p>
                      {item.name_hindi && <p className="text-[10px] text-gray-500">{item.name_hindi}</p>}
                    </td>
                    <td className="p-3">
                      <span className={`badge ${CATEGORY_COLORS[item.category] || 'badge-indigo'} text-[10px]`}>
                        {item.category?.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="p-3">
                      <span className="badge badge-emerald text-[10px]">{item.dietary_type?.replace('_', ' ')}</span>
                    </td>
                    <td className="p-3 text-gray-400">{item.cuisine}</td>
                    <td className="p-3 font-bold text-white">{item.calories}</td>
                    <td className="p-3 font-bold text-emerald-400">{item.protein_g}g</td>
                    <td className="p-3 text-indigo-300">{item.carbs_g}g</td>
                    <td className="p-3 text-amber-400">{item.fat_g}g</td>
                    <td className="p-3 text-gray-400">₹{item.approx_cost_inr}</td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={10} className="p-8 text-center text-gray-500">No dishes match your search.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
