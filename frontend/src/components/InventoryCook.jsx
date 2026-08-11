import React, { useState } from 'react';
import { ChefHat, Plus, Sparkles } from 'lucide-react';

export default function InventoryCook({ userProfile, onLogMeal }) {
  const [pantryItems, setPantryItems] = useState([
    'rice', 'dal', 'tomato', 'onion', 'paneer', 'spinach', 'eggs', 'curd', 'peanuts'
  ]);
  const [newItem, setNewItem] = useState('');
  const [recipes, setRecipes] = useState(null);
  const [loading, setLoading] = useState(false);

  const togglePantryItem = (item) => {
    setPantryItems((prev) =>
      prev.includes(item) ? prev.filter((i) => i !== item) : [...prev, item]
    );
  };

  const handleAddItem = (e) => {
    e.preventDefault();
    if (newItem.trim() && !pantryItems.includes(newItem.trim().toLowerCase())) {
      setPantryItems([...pantryItems, newItem.trim().toLowerCase()]);
      setNewItem('');
    }
  };

  const handleFindRecipes = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('nutritwin_token');
      const res = await fetch('/api/v1/optimize/pantry-meals', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ available_ingredients: pantryItems })
      });
      if (res.ok) {
        const data = await res.json();
        setRecipes(data.recipes);
      }
    } catch (err) {
      console.error('Error finding pantry recipes:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 pb-12 space-y-6">
      <div className="glass-panel p-6 border-l-4 border-l-amber-500">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <ChefHat className="w-6 h-6 text-amber-400" />
          Cook With What You Have
        </h2>
        <p className="text-xs text-gray-400">Select available ingredients in your kitchen to generate tasty recipes and reduce food waste.</p>
      </div>

      <div className="glass-panel p-6 space-y-4">
        <h3 className="text-base font-bold text-white">Your Kitchen Inventory</h3>
        
        {/* Ingredient Chips */}
        <div className="flex flex-wrap gap-2">
          {['rice', 'dal', 'tomato', 'onion', 'potato', 'paneer', 'spinach', 'eggs', 'curd', 'peanuts', 'semolina', 'flattened rice', 'chicken breast'].map((ing) => {
            const active = pantryItems.includes(ing);
            return (
              <button
                key={ing}
                onClick={() => togglePantryItem(ing)}
                className={`px-3.5 py-2 rounded-xl text-xs font-semibold border transition ${
                  active
                    ? 'bg-amber-500/20 border-amber-500 text-amber-300'
                    : 'bg-gray-900/60 border-gray-800 text-gray-400 hover:text-white'
                }`}
              >
                {active ? '✓ ' : '+ '} {ing.toUpperCase()}
              </button>
            );
          })}
        </div>

        {/* Add custom item form */}
        <form onSubmit={handleAddItem} className="flex gap-3 pt-2">
          <input
            type="text"
            placeholder="Add custom ingredient (e.g. broccoli, tofu)..."
            value={newItem}
            onChange={(e) => setNewItem(e.target.value)}
            className="form-input text-xs max-w-sm"
          />
          <button type="submit" className="btn-secondary py-2 px-4 text-xs">
            <Plus className="w-4 h-4" /> Add
          </button>
        </form>

        <button onClick={handleFindRecipes} disabled={loading} className="btn-primary w-full py-3 justify-center text-sm">
          <Sparkles className="w-4 h-4" />
          {loading ? 'Finding recipes from your ingredients...' : 'Find Meals I Can Cook Now'}
        </button>
      </div>

      {/* Matching Recipes Grid */}
      {recipes && (
        <div className="space-y-4">
          <h3 className="text-lg font-bold text-white">Matched Pantry Recipes ({recipes.length})</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {recipes.map((item) => {
              const f = item.food;
              return (
                <div key={f.id} className="glass-panel p-5 space-y-3 flex flex-col justify-between">
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="badge badge-amber">{item.match_pct}% Ingredient Match</span>
                      <span className="text-xs text-emerald-400 font-bold">{f.calories} kcal</span>
                    </div>
                    <h4 className="font-bold text-white text-base leading-snug">{f.name}</h4>
                    <p className="text-xs text-gray-400">Protein: {f.protein_g}g • Carbs: {f.carbs_g}g</p>

                    <div className="text-[11px] space-y-1 bg-gray-900/50 p-2.5 rounded-xl">
                      <p className="text-emerald-400">
                        <strong className="text-gray-300">In Kitchen:</strong> {item.matched_ingredients.join(', ')}
                      </p>
                      {item.missing_ingredients.length > 0 && (
                        <p className="text-rose-400">
                          <strong className="text-gray-300">Missing:</strong> {item.missing_ingredients.join(', ')}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
