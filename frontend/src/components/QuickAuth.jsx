import React, { useState } from 'react';
import { authAPI } from '../services/api';

const QuickAuth = ({ onAuthSuccess, onClose }) => {
  const [mode, setMode] = useState('signup'); // 'signup' or 'login'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess(false);

    try {
      const response = mode === 'signup' 
        ? await authAPI.signup(email, password)
        : await authAPI.login(email, password);

      if (response.data.success) {
        setSuccess(true);
        
        // Store token
        localStorage.setItem('authToken', response.data.token);
        localStorage.setItem('userEmail', email);
        
        // Notify parent component
        setTimeout(() => {
          onAuthSuccess(response.data.token, response.data.user);
        }, 500);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-[#1B1B1B] border border-gray-700 rounded-lg p-6 w-full max-w-md">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-white">
            {mode === 'signup' ? 'Quick Sign Up' : 'Login'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white"
          >
            ✕
          </button>
        </div>

        {success && (
          <div className="mb-4 p-3 bg-green-900 border border-green-700 rounded text-green-300">
            ✓ {mode === 'signup' ? 'Account created successfully!' : 'Logged in successfully!'}
          </div>
        )}

        {error && (
          <div className="mb-4 p-3 bg-red-900 border border-red-700 rounded text-red-300">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-300 text-sm font-medium mb-2">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 bg-[#0F0F0F] border border-gray-600 rounded text-white focus:outline-none focus:border-orange-500"
              required
              placeholder="your@email.com"
            />
          </div>

          <div className="mb-4">
            <label className="block text-gray-300 text-sm font-medium mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 bg-[#0F0F0F] border border-gray-600 rounded text-white focus:outline-none focus:border-orange-500"
              required
              placeholder="Minimum 8 characters"
              minLength={8}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-orange-500 hover:bg-orange-600 text-white font-medium py-2 px-4 rounded transition-colors disabled:opacity-50"
          >
            {loading ? 'Processing...' : (mode === 'signup' ? 'Sign Up' : 'Login')}
          </button>
        </form>

        <div className="mt-4 text-center">
          <button
            onClick={() => {
              setMode(mode === 'signup' ? 'login' : 'signup');
              setError('');
              setSuccess(false);
            }}
            className="text-gray-400 hover:text-white text-sm"
          >
            {mode === 'signup' 
              ? 'Already have an account? Login' 
              : "Don't have an account? Sign Up"}
          </button>
        </div>

        <div className="mt-4 pt-4 border-t border-gray-700">
          <div className="text-xs text-gray-400">
            <div className="mb-2">
              <strong className="text-gray-300">Rate Limits:</strong>
            </div>
            <div className="ml-2">
              • Free: 5 prompts then 1 hour lock<br/>
              • Authenticated: 50 prompts per 12 hours
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuickAuth;