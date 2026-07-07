import { useState, FormEvent } from 'react';
import { useAuth } from '../lib/auth';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

export default function LoginPage() {
  const { login, verify2FA } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [show2FA, setShow2FA] = useState(false);
  const [tempToken, setTempToken] = useState('');
  const [twoFactorCode, setTwoFactorCode] = useState('');

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const result = await login(email, password);
      if (result.requires_2fa && result.temp_token) {
        setTempToken(result.temp_token);
        setShow2FA(true);
      } else {
        toast.success('Logged in successfully');
        navigate('/dashboard');
      }
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handle2FA = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await verify2FA(email, twoFactorCode, tempToken);
      toast.success('Logged in successfully');
      navigate('/dashboard');
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || '2FA verification failed');
    } finally {
      setLoading(false);
    }
  };

  if (show2FA) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950 px-4">
        <div className="w-full max-w-md space-y-6 bg-white dark:bg-gray-900 p-8 rounded-xl shadow-lg">
          <h1 className="text-2xl font-bold text-center">Two-Factor Authentication</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 text-center">
            Enter the code from your authenticator app
          </p>
          <form onSubmit={handle2FA} className="space-y-4">
            <input
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              placeholder="000000"
              maxLength={6}
              value={twoFactorCode}
              onChange={(e) => setTwoFactorCode(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-center text-2xl tracking-widest focus:outline-none focus:ring-2 focus:ring-brand-500"
              required
            />
            <button
              type="submit"
              disabled={loading || twoFactorCode.length !== 6}
              className="w-full py-2 px-4 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white rounded-lg font-medium transition-colors"
            >
              {loading ? 'Verifying...' : 'Verify'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950 px-4">
      <div className="w-full max-w-md space-y-6 bg-white dark:bg-gray-900 p-8 rounded-xl shadow-lg">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-brand-600">TenderPilot AI</h1>
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">Sign in to your account</p>
        </div>
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-1">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
              required
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium mb-1">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 px-4 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white rounded-lg font-medium transition-colors"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}
