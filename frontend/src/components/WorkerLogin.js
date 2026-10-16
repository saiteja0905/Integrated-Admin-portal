import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
  Lock, 
  Mail, 
  Phone, 
  Eye, 
  EyeOff, 
  User, 
  Wrench, 
  ShieldCheck, 
  ArrowRight, 
  Briefcase,
  CheckCircle2,
  Loader2
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { API, getErrorMessage } from '../lib/api';
import { signInWithGoogle, checkRedirectResult } from '../lib/firebase';

export const WorkerLogin = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    email: '',
    password: '',
    email_or_phone: '',
    skill: 'General Worker'
  });
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Handle redirect Google sign-in callback
    const handleRedirect = async () => {
      try {
        const googleUser = await checkRedirectResult();
        if (googleUser) {
          setLoading(true);
          const payload = {
            email: googleUser.email,
            name: googleUser.displayName || 'Worker Partner',
            role: 'worker',
            uid: googleUser.uid,
            photo_url: googleUser.photoURL
          };
          const response = await axios.post(`${API}/auth/google`, payload);
          handleLoginSuccess(response.data);
        }
      } catch (err) {
        console.error('Redirect sign-in error:', err);
      } finally {
        setLoading(false);
      }
    };
    handleRedirect();
  }, []);

  const handleLoginSuccess = (tokenData) => {
    localStorage.setItem('token', tokenData.access_token);
    axios.defaults.headers.common['Authorization'] = `Bearer ${tokenData.access_token}`;
    toast.success(`Welcome, ${tokenData.user?.name || 'Worker'}!`);
    window.location.href = '/dashboard';
  };

  const handleGoogleSignIn = async () => {
    setLoading(true);
    try {
      const googleUser = await signInWithGoogle();
      if (!googleUser) return;

      const payload = {
        email: googleUser.email,
        name: googleUser.displayName || 'Worker Partner',
        role: 'worker',
        uid: googleUser.uid,
        photo_url: googleUser.photoURL
      };

      const response = await axios.post(`${API}/auth/google`, payload);
      handleLoginSuccess(response.data);
    } catch (error) {
      toast.error(getErrorMessage(error, 'Google sign-in failed. Please try again.'));
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (isLogin) {
        const identifier = (formData.email_or_phone || formData.email || formData.phone || '').trim();
        const payload = {
          email_or_phone: identifier,
          phone: identifier,
          email: identifier.includes('@') ? identifier.toLowerCase() : undefined,
          password: formData.password
        };
        const response = await axios.post(`${API}/auth/login`, payload);
        const userData = response.data;
        
        // Log in worker
        handleLoginSuccess(userData);
      } else {
        // Worker Registration
        const phone = formData.phone.trim();
        const email = formData.email.trim();
        const payload = {
          name: formData.name.trim(),
          phone: phone,
          password: formData.password,
          role: 'worker',
          ...(email ? { email: email.toLowerCase() } : {})
        };
        const response = await axios.post(`${API}/auth/register`, payload);
        handleLoginSuccess(response.data);
      }
    } catch (error) {
      toast.error(getErrorMessage(error, 'Authentication failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-amber-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full my-6">
        {/* Worker Portal Header Branding */}
        <div className="text-center mb-6">
          <h1 className="text-4xl font-extrabold text-orange-600 tracking-tight">Sanyuth</h1>
          <p className="text-gray-600 font-medium text-sm mt-0.5">Worker Partner Portal</p>
          <div className="inline-flex items-center px-3.5 py-1 rounded-full text-xs font-bold bg-orange-100 text-orange-800 border border-orange-200 mt-2.5">
            <Wrench className="w-3.5 h-3.5 mr-1.5 text-orange-600" />
            Service Professional Access
          </div>
        </div>

        {/* Auth Card */}
        <div className="bg-white rounded-2xl shadow-xl border border-orange-100 p-8">
          {/* Tab Switcher */}
          <div className="flex mb-6 bg-gray-100 rounded-xl p-1">
            <button
              type="button"
              className={`flex-1 py-2 px-4 rounded-lg text-sm font-bold transition-all ${
                isLogin ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500 hover:text-gray-700'
              }`}
              onClick={() => setIsLogin(true)}
            >
              Worker Login
            </button>
            <button
              type="button"
              className={`flex-1 py-2 px-4 rounded-lg text-sm font-bold transition-all ${
                !isLogin ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500 hover:text-gray-700'
              }`}
              onClick={() => setIsLogin(false)}
            >
              Join as Worker
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <>
                <div>
                  <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">Full Name</label>
                  <div className="relative">
                    <User className="w-4 h-4 text-gray-400 absolute left-3 top-3.5" />
                    <input
                      type="text"
                      required
                      placeholder="e.g. Ramesh Kumar"
                      className="w-full pl-9 pr-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">Phone Number (10 digits)</label>
                  <div className="relative">
                    <Phone className="w-4 h-4 text-gray-400 absolute left-3 top-3.5" />
                    <input
                      type="tel"
                      required
                      maxLength={10}
                      placeholder="Enter 10-digit mobile number (e.g. 9876543210)"
                      className="w-full pl-9 pr-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value.replace(/\D/g, '').slice(0, 10) })}
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">Email (Optional)</label>
                  <div className="relative">
                    <Mail className="w-4 h-4 text-gray-400 absolute left-3 top-3.5" />
                    <input
                      type="email"
                      placeholder="e.g. ramesh@example.com (optional)"
                      className="w-full pl-9 pr-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    />
                  </div>
                </div>
              </>
            )}

            {isLogin && (
              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                  Worker Email or Phone Number
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-gray-400 absolute left-3 top-3.5" />
                  <input
                    type="text"
                    required
                    placeholder="Enter registered email or 10-digit phone number"
                    className="w-full pl-9 pr-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
                    value={formData.email_or_phone}
                    onChange={(e) => {
                      const val = e.target.value;
                      setFormData({
                        ...formData,
                        email_or_phone: val,
                        phone: val,
                        email: val.includes('@') ? val : ''
                      });
                    }}
                  />
                </div>
              </div>
            )}

            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider">Password</label>
                {!isLogin && <span className="text-[11px] text-gray-400">Min 6 characters</span>}
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 text-gray-400 absolute left-3 top-3.5" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  minLength={isLogin ? undefined : 6}
                  placeholder={isLogin ? "Enter your password" : "Create a strong password (min 6 characters)"}
                  className="w-full pl-9 pr-10 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-orange-600 text-white py-3 px-4 rounded-xl hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-orange-500 font-bold shadow-md shadow-orange-600/20 disabled:opacity-50 transition flex items-center justify-center text-sm"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              ) : (
                <ArrowRight className="w-4 h-4 mr-2" />
              )}
              {isLogin ? 'Sign In to Worker Portal' : 'Register as Service Worker'}
            </button>
          </form>

          {/* Social Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-200"></div>
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-white px-3 text-gray-400 font-bold tracking-wider">Or</span>
            </div>
          </div>

          {/* Google Sign-in */}
          <button
            type="button"
            onClick={handleGoogleSignIn}
            disabled={loading}
            className="w-full flex items-center justify-center gap-3 bg-white border border-gray-300 text-gray-700 py-2.5 px-4 rounded-xl hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-orange-500 font-semibold shadow-sm transition disabled:opacity-50 text-sm"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
            </svg>
            Continue with Google
          </button>

          {/* Quick Cross-Portal Switcher Links */}
          <div className="mt-6 pt-5 border-t border-gray-100 flex flex-col space-y-2 text-center text-xs text-gray-500">
            <div>
              Looking to hire skilled professionals?{' '}
              <Link to="/auth" className="text-orange-600 font-bold hover:underline">
                Customer Login
              </Link>
            </div>
          </div>
        </div>

        {/* Benefits Footnote */}
        <div className="mt-6 text-center text-xs text-gray-500 space-y-1">
          <p className="flex items-center justify-center font-medium text-gray-600">
            <ShieldCheck className="w-4 h-4 text-emerald-600 mr-1" />
            Two-Stage Verified Worker Network
          </p>
          <p className="text-[11px] text-gray-400">Direct job requests, timely payments &amp; in-person identity badges.</p>
        </div>
      </div>
    </div>
  );
};
