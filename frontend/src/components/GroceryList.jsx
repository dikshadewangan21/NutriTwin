import React, { useState, useEffect } from 'react';
import { ShoppingBag, RefreshCw } from 'lucide-react';

export default function GroceryList() {
  const [groceryData, setGroceryData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchGroceryList();
  }, []);

  const fetchGroceryList = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('nutritwin_token');
      const res = await fetch('/api/v1/optimize/grocery-list', {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      if (res.ok) {
        const data = await res.json();
        setGroceryData(data.grocery_list);
      }
    } catch (err) {
      console.error('Error fetching grocery list:', err);
    } finally {
      setLoading(false);
    }
  };

  const categories = groceryData?.grocery_by_category || {};

  return (
    <div className="max-w-5xl mx-auto px-4 pb-12 space-y-6">
      <div className="glass-panel p-6 border-l-4 border-l-purple-500 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="badge badge-indigo">7-Day Shopping Helper</span>
          </div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2 mt-1">
            <ShoppingBag className="w-6 h-6 text-purple-400" />
            Your 7-Day Shopping List
          </h2>
          <p className="text-xs text-gray-400">Combines all ingredients for your weekly meals into a neat shopping list.</p>
        </div>

        {groceryData && (
          <div className="bg-purple-950/40 border border-purple-500/30 px-5 py-3 rounded-2xl text-right">
            <p className="text-[10px] text-purple-300 font-medium">ESTIMATED WEEKLY TOTAL</p>
            <p className="text-2xl font-extrabold text-white">₹{groceryData.total_estimated_cost_inr}</p>
          </div>
        )}
      </div>

      {loading ? (
        <div className="glass-panel p-12 text-center text-gray-400 text-sm">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto text-purple-400 mb-2" />
          Combining your weekly meal ingredients...
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {Object.entries(categories).map(([categoryName, items]) => (
            <div key={categoryName} className="glass-panel p-5 space-y-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2 border-b border-gray-800 pb-2">
                <span className="w-2.5 h-2.5 rounded-full bg-purple-400"></span>
                {categoryName} ({items.length})
              </h3>

              <div className="space-y-2">
                {items.map((item, idx) => (
                  <div key={idx} className="flex justify-between items-center bg-gray-900/60 p-3 rounded-xl border border-gray-800/80">
                    <span className="text-sm font-medium text-gray-200">{item.ingredient}</span>
                    <div className="flex items-center gap-3">
                      <span className="badge badge-emerald text-[11px]">{item.estimated_quantity}</span>
                      <span className="text-[10px] text-gray-500">{item.frequency_in_meals} meals</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
