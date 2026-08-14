import React, { useState } from 'react';
import {
  LayoutDashboard, Calendar, Camera, ShoppingBag, ChefHat,
  LineChart, Shield, Bot, User, LogOut, ChevronDown, Menu, X
} from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, userProfile, openChat, onLogout }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [profileDropdown, setProfileDropdown] = useState(false);

  const userName = localStorage.getItem('nutritwin_name') || userProfile?.full_name || 'User';
  const userInitial = userName.charAt(0).toUpperCase();

  const navItems = [
    { id: 'dashboard',  label: 'Dashboard',      icon: LayoutDashboard },
    { id: 'planner',    label: '7-Day Meal Plan', icon: Calendar },
    { id: 'vision',     label: 'Food Scanner',    icon: Camera },
    { id: 'pantry',     label: 'Cook Leftovers',  icon: ChefHat },
    { id: 'grocery',    label: 'Grocery List',    icon: ShoppingBag },
    { id: 'analytics',  label: 'My Progress',     icon: LineChart },
    { id: 'admin',      label: 'System',          icon: Shield },
  ];

  const handleNav = (id) => {
    setActiveTab(id);
    setMobileOpen(false);
  };

  return (
    <>
      <nav className="glass-panel sticky top-2 sm:top-4 z-40 mx-2 sm:mx-4 my-2 sm:my-3 px-3 sm:px-6 py-2.5 sm:py-3.5 flex items-center justify-between">
        {/* Brand */}
        <div
          className="flex items-center gap-2 sm:gap-3 cursor-pointer min-w-0"
          onClick={() => setActiveTab('dashboard')}
        >
          <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-indigo-600 flex items-center justify-center text-lg sm:text-xl shadow-lg shadow-emerald-500/20 shrink-0">
            🥗
          </div>
          <div className="hidden sm:block truncate">
            <h1 className="text-lg sm:text-xl font-bold tracking-tight text-white leading-tight">NutriTwin</h1>
            <p className="text-[11px] text-gray-400">Personalized Diet Intelligence</p>
          </div>
        </div>

        {/* Desktop Nav Links */}
        <div className="hidden lg:flex items-center gap-1 bg-gray-900/60 p-1.5 rounded-2xl border border-gray-800">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleNav(item.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 sm:px-3.5 sm:py-2 rounded-xl text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-emerald-500 to-emerald-600 text-white shadow-md shadow-emerald-500/20 font-semibold'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {item.label}
              </button>
            );
          })}
        </div>

        {/* Right Controls */}
        <div className="flex items-center gap-1.5 sm:gap-2">
          {/* AI Assistant */}
          <button
            onClick={openChat}
            className="btn-primary py-1.5 px-2.5 sm:py-2 sm:px-3 text-xs rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 shadow-indigo-500/25 shrink-0"
          >
            <Bot className="w-4 h-4" />
            <span className="hidden md:inline">AI Assistant</span>
          </button>

          {/* Profile dropdown */}
          <div className="relative">
            <button
              onClick={() => setProfileDropdown(!profileDropdown)}
              className="flex items-center gap-1.5 sm:gap-2 bg-gray-800/80 border border-gray-700 hover:border-emerald-500/50 px-2 sm:px-3 py-1.5 sm:py-2 rounded-xl text-xs transition"
            >
              {/* Avatar circle */}
              <div className="w-6 h-6 sm:w-7 sm:h-7 rounded-full bg-gradient-to-tr from-emerald-500 to-indigo-500 flex items-center justify-center text-white font-bold text-xs sm:text-sm shrink-0">
                {userInitial}
              </div>
              <div className="hidden md:block text-left max-w-[90px] truncate">
                <p className="text-white font-semibold leading-none truncate">{userName.split(' ')[0]}</p>
                <p className="text-[9px] text-emerald-400 mt-0.5 truncate">{userProfile?.assigned_cluster_label || 'Active'}</p>
              </div>
              <ChevronDown className={`w-3.5 h-3.5 text-gray-400 transition ${profileDropdown ? 'rotate-180' : ''}`} />
            </button>

            {profileDropdown && (
              <div className="absolute right-0 top-12 w-48 bg-gray-900 border border-gray-800 rounded-2xl shadow-xl z-50 py-1 overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-800">
                  <p className="text-white font-semibold text-sm truncate">{userName}</p>
                  <p className="text-xs text-gray-400 truncate">{userProfile?.email || ''}</p>
                </div>
                <button
                  onClick={() => { setProfileDropdown(false); setActiveTab('profile'); }}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-gray-300 hover:bg-gray-800 hover:text-white transition"
                >
                  <User className="w-4 h-4 text-emerald-400" />
                  My Profile
                </button>
                <button
                  onClick={() => { setProfileDropdown(false); onLogout(); }}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-rose-400 hover:bg-rose-950/50 hover:text-rose-300 transition"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>
            )}
          </div>

          {/* Mobile burger */}
          <button
            className="lg:hidden text-gray-400 hover:text-white p-1.5 rounded-lg hover:bg-gray-800/60"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle Navigation Menu"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </nav>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          {/* Backdrop */}
          <div className="flex-1 bg-black/70 backdrop-blur-sm transition-opacity" onClick={() => setMobileOpen(false)} />
          {/* Drawer */}
          <div className="w-72 max-w-[85vw] bg-gray-950 border-l border-gray-800 flex flex-col p-5 space-y-2 overflow-y-auto shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-gray-800 mb-2">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-500 to-indigo-600 flex items-center justify-center text-lg">🥗</div>
                <span className="font-bold text-white text-base">NutriTwin</span>
              </div>
              <button onClick={() => setMobileOpen(false)} className="text-gray-400 hover:text-white p-1">
                <X className="w-5 h-5" />
              </button>
            </div>
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleNav(item.id)}
                  className={`flex items-center gap-3 w-full px-3.5 py-2.5 rounded-xl text-xs font-semibold transition ${
                    isActive
                      ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/30'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800/70'
                  }`}
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  {item.label}
                </button>
              );
            })}
            <div className="pt-4 border-t border-gray-800 space-y-1.5 mt-auto">
              <button
                onClick={() => { handleNav('profile'); }}
                className="flex items-center gap-3 w-full px-3.5 py-2.5 rounded-xl text-xs font-medium text-gray-300 hover:bg-gray-800 transition"
              >
                <User className="w-4 h-4 text-emerald-400 shrink-0" />
                My Profile
              </button>
              <button
                onClick={() => { setMobileOpen(false); onLogout(); }}
                className="flex items-center gap-3 w-full px-3.5 py-2.5 rounded-xl text-xs font-medium text-rose-400 hover:bg-rose-950/50 transition"
              >
                <LogOut className="w-4 h-4 shrink-0" />
                Sign Out
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
