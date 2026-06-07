import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../api/auth';
import { Shield, Lock, User, AlertCircle, Loader2 } from 'lucide-react';
import axios from 'axios';

const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const response = await authApi.login(username, password);
      await login(response.access_token);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      console.error('Login error', err);
      if (axios.isAxiosError(err)) {
        if (err.response?.status === 401) {
          setError('Invalid username or password');
        } else if (err.message === 'Network Error') {
          setError('Cannot connect to server');
        } else {
          setError('An unexpected error occurred');
        }
      } else {
        setError('An unexpected error occurred');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-background">
      {/* Left side - Branding */}
      <div className="hidden lg:flex flex-col justify-center w-1/2 p-12 bg-card border-r">
        <div className="max-w-md mx-auto">
          <div className="flex items-center mb-8">
            <Shield className="w-12 h-12 mr-4 text-primary" />
            <h1 className="text-4xl font-bold tracking-tight">Honeypot SOC</h1>
          </div>
          <p className="text-xl text-muted-foreground mb-8">
            Advanced AI-powered threat detection and response platform. Monitor, analyze, and defend against active attacks in real-time.
          </p>
          
          <div className="space-y-6">
            <div className="flex items-start">
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/20 text-primary mr-4 shrink-0">
                <div className="w-2 h-2 rounded-full bg-primary" />
              </div>
              <div>
                <h3 className="font-semibold mb-1">Real-time Visibility</h3>
                <p className="text-sm text-muted-foreground">Monitor live attacks on honeypot infrastructure as they happen.</p>
              </div>
            </div>
            <div className="flex items-start">
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/20 text-primary mr-4 shrink-0">
                <div className="w-2 h-2 rounded-full bg-primary" />
              </div>
              <div>
                <h3 className="font-semibold mb-1">AI Investigation</h3>
                <p className="text-sm text-muted-foreground">Leverage advanced LLMs and RAG to automatically investigate complex threats.</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right side - Login Form */}
      <div className="flex flex-col justify-center w-full lg:w-1/2 p-8 sm:p-12">
        <div className="max-w-sm w-full mx-auto">
          <div className="lg:hidden flex items-center justify-center mb-10">
            <Shield className="w-10 h-10 mr-3 text-primary" />
            <h1 className="text-3xl font-bold">Honeypot SOC</h1>
          </div>

          <div className="mb-8 text-center lg:text-left">
            <h2 className="text-2xl font-semibold mb-2">Welcome back</h2>
            <p className="text-muted-foreground">Sign in to your account to continue</p>
          </div>

          {error && (
            <div className="flex items-center p-4 mb-6 rounded-md bg-destructive/15 text-destructive border border-destructive/20">
              <AlertCircle className="w-5 h-5 mr-3 shrink-0" />
              <p className="text-sm font-medium">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="username">
                Username
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                  <User className="w-5 h-5 text-muted-foreground" />
                </div>
                <input
                  id="username"
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full h-11 pl-10 pr-4 rounded-md border bg-background hover:border-muted-foreground/50 focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all"
                  placeholder="admin"
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium" htmlFor="password">
                  Password
                </label>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                  <Lock className="w-5 h-5 text-muted-foreground" />
                </div>
                <input
                  id="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full h-11 pl-10 pr-4 rounded-md border bg-background hover:border-muted-foreground/50 focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading || !username || !password}
              className="flex items-center justify-center w-full h-11 px-4 text-sm font-medium transition-colors rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed mt-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Signing in...
                </>
              ) : (
                'Sign in'
              )}
            </button>
          </form>
          
          <div className="mt-8 text-center text-xs text-muted-foreground">
            <p>Authorized personnel only. All access is logged.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
