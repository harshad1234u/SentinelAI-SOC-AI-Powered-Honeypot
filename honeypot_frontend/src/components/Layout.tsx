import React from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, LayoutDashboard, Activity, Search, Bot, Bell, Settings, LogOut, Menu } from 'lucide-react';

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/feed', label: 'Live Feed', icon: Activity },
  { to: '/assistant', label: 'AI Assistant', icon: Bot },
  { to: '/alerts', label: 'Alerts', icon: Bell },
  { to: '/settings', label: 'Settings', icon: Settings },
];

export const Layout: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground">
      {/* Sidebar */}
      <aside className="hidden w-64 border-r bg-card md:flex md:flex-col">
        <div className="flex items-center h-16 px-6 border-b">
          <Shield className="w-6 h-6 mr-2 text-primary" />
          <span className="text-lg font-bold tracking-tight">Honeypot SOC</span>
        </div>
        
        <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center px-3 py-2.5 text-sm font-medium rounded-md transition-colors ${
                  isActive
                    ? 'bg-primary/10 text-primary'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                }`
              }
            >
              <item.icon className="w-5 h-5 mr-3" />
              {item.label}
            </NavLink>
          ))}
        </nav>
        
        <div className="p-4 border-t">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/20 text-primary">
                {user?.username.charAt(0).toUpperCase() || 'U'}
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-medium leading-none">{user?.username}</span>
                <span className="text-xs text-muted-foreground mt-1">{user?.role}</span>
              </div>
            </div>
          </div>
          <button
            onClick={logout}
            className="flex items-center w-full px-3 py-2 text-sm font-medium text-red-500 transition-colors rounded-md hover:bg-red-500/10"
          >
            <LogOut className="w-5 h-5 mr-3" />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex flex-col flex-1 w-full overflow-hidden">
        {/* Topbar */}
        <header className="flex items-center justify-between h-16 px-6 border-b bg-card md:px-8">
          <div className="flex items-center md:hidden">
            <button className="p-2 -ml-2 text-muted-foreground hover:text-foreground">
              <Menu className="w-6 h-6" />
            </button>
            <Shield className="w-5 h-5 ml-4 mr-2 text-primary" />
            <span className="text-base font-bold">Honeypot SOC</span>
          </div>
          
          <div className="hidden md:flex flex-1 max-w-xl px-4">
            <div className="relative w-full group">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
              <input
                type="text"
                placeholder="Search IPs, usernames, or ask AI... (Ctrl+K)"
                className="w-full h-10 pl-10 pr-4 text-sm bg-accent/50 border-transparent rounded-full focus:bg-background focus:border-primary/50 focus:ring-1 focus:ring-primary outline-none transition-all placeholder:text-muted-foreground"
              />
              <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 text-xs text-muted-foreground/70 font-medium">
                <kbd className="px-1.5 py-0.5 rounded border bg-background/50">⌘</kbd>
                <kbd className="px-1.5 py-0.5 rounded border bg-background/50">K</kbd>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-background p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
