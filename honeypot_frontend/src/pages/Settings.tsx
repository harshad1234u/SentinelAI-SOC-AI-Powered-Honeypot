import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { User, Shield, Key, Bell, Moon } from 'lucide-react';

const Settings: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'appearance', label: 'Appearance', icon: Moon }
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'profile':
        return (
          <>
            <div className="p-6 border rounded-lg bg-card space-y-6">
              <div>
                <h3 className="text-lg font-semibold">Profile Information</h3>
                <p className="text-sm text-muted-foreground">Personal details and role assignment.</p>
              </div>
              <div className="space-y-4">
                <div className="grid gap-2">
                  <label className="text-sm font-medium">Username</label>
                  <input 
                    type="text" 
                    disabled 
                    value={user?.username || ''}
                    className="w-full px-3 py-2 text-sm border rounded-md bg-muted/50 cursor-not-allowed"
                  />
                </div>
                <div className="grid gap-2">
                  <label className="text-sm font-medium">Role</label>
                  <div className="flex items-center">
                    <span className="px-2.5 py-1 text-xs font-semibold rounded-md bg-primary/20 text-primary uppercase tracking-wider">
                      {user?.role || 'Operator'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            <div className="p-6 border rounded-lg bg-card space-y-6">
              <div>
                <h3 className="text-lg font-semibold flex items-center">
                  <Key className="w-5 h-5 mr-2" /> Change Password
                </h3>
                <p className="text-sm text-muted-foreground">Password management is handled by the identity provider.</p>
              </div>
              <div className="space-y-4">
                <button 
                  onClick={() => alert("Password reset instructions have been sent to your registered email address.")}
                  className="px-4 py-2 text-sm font-medium border rounded-md bg-background hover:bg-accent transition-colors">
                  Request Password Reset
                </button>
              </div>
            </div>
          </>
        );
      case 'security':
        return (
          <div className="p-6 border rounded-lg bg-card space-y-6">
            <div>
              <h3 className="text-lg font-semibold">Security Settings</h3>
              <p className="text-sm text-muted-foreground">Manage multi-factor authentication and active sessions.</p>
            </div>
            <div className="p-4 border rounded-md bg-muted/30 flex items-center justify-between">
              <div>
                <p className="font-medium">Two-Factor Authentication (2FA)</p>
                <p className="text-sm text-muted-foreground">Add an extra layer of security to your account.</p>
              </div>
              <button 
                onClick={() => alert("2FA setup wizard initialized. Check your email for the next steps.")}
                className="px-3 py-1.5 text-sm font-medium border rounded-md bg-background hover:bg-accent transition-colors">
                Configure
              </button>
            </div>
          </div>
        );
      case 'notifications':
        return (
          <div className="p-6 border rounded-lg bg-card space-y-6">
            <div>
              <h3 className="text-lg font-semibold">Notification Preferences</h3>
              <p className="text-sm text-muted-foreground">Control how you receive alerts and updates.</p>
            </div>
            <div className="space-y-3">
              {['Email Alerts', 'Telegram Notifications', 'In-app Popups'].map((label) => (
                <label key={label} className="flex items-center space-x-3 p-3 border rounded-md cursor-pointer hover:bg-muted/50 transition-colors">
                  <input type="checkbox" className="form-checkbox h-4 w-4 text-primary rounded" defaultChecked />
                  <span className="font-medium text-sm">{label}</span>
                </label>
              ))}
            </div>
          </div>
        );
      case 'appearance':
        return (
          <div className="p-6 border rounded-lg bg-card space-y-6">
            <div>
              <h3 className="text-lg font-semibold">Appearance</h3>
              <p className="text-sm text-muted-foreground">Customize the interface theme.</p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <button className="flex flex-col items-center justify-center p-6 border-2 border-primary rounded-lg bg-card">
                <Moon className="w-8 h-8 mb-2" />
                <span className="font-medium">Dark Mode</span>
              </button>
              <button 
                onClick={() => alert("Light mode is still under development by the UI team!")}
                className="flex flex-col items-center justify-center p-6 border rounded-lg bg-muted/30 hover:bg-accent transition-colors">
                <span className="w-8 h-8 mb-2 block rounded-full border-2 border-foreground" />
                <span className="font-medium">Light Mode (Coming Soon)</span>
              </button>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Settings</h2>
        <p className="text-muted-foreground">Manage your account and SOC preferences.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-4">
        {/* Navigation Sidebar */}
        <div className="md:col-span-1 space-y-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  isActive 
                    ? 'bg-primary/10 text-primary' 
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                }`}
              >
                <Icon className="w-4 h-4 mr-2" /> {tab.label}
              </button>
            );
          })}
        </div>

        {/* Content Area */}
        <div className="md:col-span-3 space-y-6">
          {renderContent()}
        </div>
      </div>
    </div>
  );
};

export default Settings;
