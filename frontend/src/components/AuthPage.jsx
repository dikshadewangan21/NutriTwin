import React, { useState } from 'react';
import { Leaf, Eye, EyeOff, LogIn, UserPlus, HeartPulse, Sparkles } from 'lucide-react';

export default function AuthPage({ onAuthenticated }) {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ full_name: '', email: '', password: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isLogin) {
        // Login
        const res = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: formData.email, password: formData.password })
        });
        const data = await res.json();
        if (!res.ok) { setError(data.detail || 'Invalid email or password.'); return; }
        localStorage.setItem('nutritwin_token', data.access_token);
        localStorage.setItem('nutritwin_name', data.full_name || formData.email.split('@')[0]);
        onAuthenticated(data.access_token);
      } else {
        // Register
        if (!formData.full_name.trim()) { setError('Please enter your full name.'); return; }
        const res = await fetch('/api/v1/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData)
        });
        const data = await res.json();
        if (!res.ok) { setError(data.detail || 'Registration failed. Try a different email.'); return; }
        localStorage.setItem('nutritwin_token', data.access_token);
        localStorage.setItem('nutritwin_name', formData.full_name);
        onAuthenticated(data.access_token);
      }
    } catch (err) {
      setError('Connection error. Please make sure the server is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col md:flex-row">
      {/* Left panel — branding */}
      <div className="hidden md:flex flex-col justify-center items-start p-14 w-1/2 bg-gradient-to-br from-gray-950 via-gray-900 to-emerald-950 space-y-8 relative overflow-hidden">
        {/* Decorative circles */}
        <div className="absolute -top-24 -left-24 w-96 h-96 rounded-full bg-emerald-500/5 blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 right-0 w-72 h-72 rounded-full bg-indigo-500/5 blur-3xl pointer-events-none" />

        <div className="flex items-center gap-3 z-10">
          <div className="w-12 h-12 rounded-2xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center">
            <HeartPulse className="w-6 h-6 text-emerald-400" />
          </div>
          <span className="text-2xl font-extrabold text-white tracking-tight">NutriTwin</span>
        </div>

        <div className="z-10 space-y-4">
          <h1 className="text-4xl font-extrabold text-white leading-tight">
            Your Personal<br />
            <span className="text-emerald-400">AI Nutrition</span><br />
            Coach
          </h1>
          <p className="text-gray-400 text-sm leading-relaxed max-w-sm">
            Enter your body details, fitness goal, and health conditions. NutriTwin builds a personalized 7-day Indian meal plan that fits your budget and adapts as you progress.
          </p>
        </div>

        <div className="z-10 space-y-3">
          {[
            { icon: '🧬', text: 'Calculates your exact daily calorie & protein needs' },
            { icon: '❤️', text: 'Diabetes, PCOS, Hypertension-aware meal planning' },
            { icon: '💰', text: 'Stays strictly within your daily budget (₹100–₹500+)' },
            { icon: '📅', text: 'Generates a varied 7-day Indian meal plan daily' },
          ].map((f) => (
            <div key={f.text} className="flex items-center gap-3 text-sm text-gray-300">
              <span className="text-lg">{f.icon}</span>
              <span>{f.text}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Right panel — auth form */}
      <div className="flex-1 flex flex-col justify-center items-center p-6 md:p-14 bg-gray-950">
        {/* Mobile brand */}
        <div className="flex md:hidden items-center gap-2 mb-8">
          <HeartPulse className="w-6 h-6 text-emerald-400" />
          <span className="text-xl font-extrabold text-white">NutriTwin</span>
        </div>

        <div className="w-full max-w-md space-y-6">
          {/* Toggle tabs */}
          <div className="flex bg-gray-900 rounded-2xl p-1 gap-1 border border-gray-800">
            <button
              onClick={() => { setIsLogin(true); setError(''); }}
              className={`flex-1 py-2.5 rounded-xl text-sm font-semibold transition ${isLogin ? 'bg-emerald-600 text-white shadow-md' : 'text-gray-400 hover:text-white'}`}
            >
              <LogIn className="w-4 h-4 inline mr-1.5" /> Sign In
            </button>
            <button
              onClick={() => { setIsLogin(false); setError(''); }}
              className={`flex-1 py-2.5 rounded-xl text-sm font-semibold transition ${!isLogin ? 'bg-emerald-600 text-white shadow-md' : 'text-gray-400 hover:text-white'}`}
            >
              <UserPlus className="w-4 h-4 inline mr-1.5" /> Create Account
            </button>
          </div>

          <div className="glass-panel p-7 space-y-5">
            <div>
              <h2 className="text-xl font-bold text-white">
                {isLogin ? 'Welcome back!' : 'Create your account'}
              </h2>
              <p className="text-xs text-gray-400 mt-1">
                {isLogin ? 'Sign in to access your personalized nutrition plan.' : 'Start building your personalized diet plan in minutes.'}
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {!isLogin && (
                <div>
                  <label className="text-xs text-gray-400 block mb-1.5">Full Name</label>
                  <input
                    type="text"
                    placeholder="e.g. Priya Sharma"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    className="form-input"
                    required={!isLogin}
                  />
                </div>
              )}

              <div>
                <label className="text-xs text-gray-400 block mb-1.5">Email Address</label>
                <input
                  type="email"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="form-input"
                  required
                />
              </div>

              <div>
                <label className="text-xs text-gray-400 block mb-1.5">Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    placeholder={isLogin ? 'Your password' : 'Min 8 characters'}
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="form-input pr-10"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {error && (
                <div className="bg-rose-950/50 border border-rose-500/40 text-rose-300 text-xs p-3 rounded-xl">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full py-3 justify-center text-sm"
              >
                {loading ? (
                  <span className="flex items-center gap-2"><Sparkles className="w-4 h-4 animate-spin" /> {isLogin ? 'Signing in...' : 'Creating account...'}</span>
                ) : (
                  isLogin ? '→ Sign In to NutriTwin' : '→ Create Account & Start'
                )}
              </button>
            </form>

            <p className="text-center text-xs text-gray-500">
              {isLogin ? "Don't have an account? " : 'Already have an account? '}
              <button onClick={() => { setIsLogin(!isLogin); setError(''); }} className="text-emerald-400 hover:underline font-semibold">
                {isLogin ? 'Create one free' : 'Sign in'}
              </button>
            </p>
          </div>

          <p className="text-center text-[11px] text-gray-600">
            NutriTwin provides general wellness nutrition guidance. Not a medical service.
          </p>
        </div>
      </div>
    </div>
  );
}
