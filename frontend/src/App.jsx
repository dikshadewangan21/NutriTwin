import React, { useState, useEffect } from 'react';
import AuthPage from './components/AuthPage';
import Navbar from './components/Navbar';
import Dashboard from './components/Dashboard';
import ProfileOnboarding from './components/ProfileOnboarding';
import MealPlanner from './components/MealPlanner';
import VisionUploader from './components/VisionUploader';
import InventoryCook from './components/InventoryCook';
import GroceryList from './components/GroceryList';
import AnalyticsView from './components/AnalyticsView';
import AdminConsole from './components/AdminConsole';
import AIAssistantModal from './components/AIAssistantModal';
import ExplainabilityModal from './components/ExplainabilityModal';

// App states:
// 'auth'       → Show Login / Register page
// 'onboarding' → User just registered, no profile yet — show profile setup first
// 'app'        → Fully authenticated with profile → show dashboard & all features

export default function App() {
  const [appState, setAppState] = useState('loading'); // 'loading' | 'auth' | 'onboarding' | 'app'
  const [activeTab, setActiveTab] = useState('dashboard');
  const [userProfile, setUserProfile] = useState(null);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [explainFoodId, setExplainFoodId] = useState(null);
  const [isNewUser, setIsNewUser] = useState(false);

  useEffect(() => {
    checkExistingSession();
  }, []);

  const checkExistingSession = async () => {
    const token = localStorage.getItem('nutritwin_token');
    if (!token) {
      setAppState('auth');
      return;
    }
    await fetchUserProfile(token);
  };

  const fetchUserProfile = async (token) => {
    try {
      const res = await fetch('/api/v1/profile/me', {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.ok) {
        const pdata = await res.json();
        setUserProfile(pdata);
        setAppState('app');
      } else {
        // Token is valid but no profile yet — new user who just registered
        setAppState('onboarding');
        setIsNewUser(true);
      }
    } catch {
      // Server error or token invalid
      localStorage.removeItem('nutritwin_token');
      setAppState('auth');
    }
  };

  const handleAuthenticated = async (token) => {
    await fetchUserProfile(token);
  };

  const handleLogout = () => {
    localStorage.removeItem('nutritwin_token');
    localStorage.removeItem('nutritwin_name');
    setUserProfile(null);
    setAppState('auth');
    setActiveTab('dashboard');
  };

  const handleProfileComplete = (updatedProfile) => {
    setUserProfile(updatedProfile);
    // After completing profile, go straight to the 7-day planner
    setAppState('app');
    setActiveTab('planner');
  };

  // Loading splash
  if (appState === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <div className="text-center space-y-3">
          <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center mx-auto">
            <span className="text-2xl">🥗</span>
          </div>
          <p className="text-white font-bold text-lg">NutriTwin</p>
          <p className="text-gray-400 text-xs">Loading your nutrition profile...</p>
        </div>
      </div>
    );
  }

  // Not authenticated → show login/register
  if (appState === 'auth') {
    return <AuthPage onAuthenticated={handleAuthenticated} />;
  }

  // Authenticated but no profile → show profile setup first
  if (appState === 'onboarding') {
    return (
      <div className="min-h-screen flex flex-col">
        {/* Minimal header during onboarding */}
        <header className="px-6 py-4 border-b border-gray-800 bg-gray-950/80 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">🥗</span>
            <span className="font-extrabold text-white text-lg">NutriTwin</span>
          </div>
          <button onClick={handleLogout} className="text-xs text-gray-400 hover:text-white">
            Sign out
          </button>
        </header>
        <main className="flex-1 py-6">
          <ProfileOnboarding
            userProfile={null}
            onProfileUpdated={handleProfileComplete}
            onGenerateDiet={() => {
              setAppState('app');
              setActiveTab('planner');
            }}
          />
        </main>
      </div>
    );
  }

  // Full app
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        userProfile={userProfile}
        openChat={() => setIsChatOpen(true)}
        onLogout={handleLogout}
      />

      <main className="flex-1 py-4">
        {activeTab === 'dashboard' && (
          <Dashboard
            userProfile={userProfile}
            onOpenExplain={(fid) => setExplainFoodId(fid)}
            onLogMeal={() => {}}
            onViewPlanner={() => setActiveTab('planner')}
            onEditProfile={() => setActiveTab('profile')}
          />
        )}

        {activeTab === 'profile' && (
          <ProfileOnboarding
            userProfile={userProfile}
            onProfileUpdated={(updated) => {
              setUserProfile(updated);
            }}
            onGenerateDiet={() => setActiveTab('planner')}
          />
        )}

        {activeTab === 'planner' && (
          <MealPlanner
            userProfile={userProfile}
            onOpenSubstitute={(fid) => setExplainFoodId(fid)}
          />
        )}

        {activeTab === 'vision' && <VisionUploader onMealLogged={() => setActiveTab('dashboard')} />}
        {activeTab === 'pantry' && <InventoryCook userProfile={userProfile} onLogMeal={() => {}} />}
        {activeTab === 'grocery' && <GroceryList />}
        {activeTab === 'analytics' && <AnalyticsView userProfile={userProfile} />}
        {activeTab === 'admin' && <AdminConsole />}
      </main>

      <AIAssistantModal isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
      <ExplainabilityModal
        foodId={explainFoodId}
        isOpen={Boolean(explainFoodId)}
        onClose={() => setExplainFoodId(null)}
      />
    </div>
  );
}
