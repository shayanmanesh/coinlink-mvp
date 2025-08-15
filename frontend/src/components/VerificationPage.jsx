import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';

const VerificationPage = () => {
  const [searchParams] = useSearchParams();
  const [verificationStatus, setVerificationStatus] = useState('verifying');
  const [message, setMessage] = useState('');
  const token = searchParams.get('token');

  useEffect(() => {
    const verifyAccount = async () => {
      if (!token) {
        setVerificationStatus('error');
        setMessage('No verification token provided');
        return;
      }

      try {
        const response = await fetch(`/api/auth/verify?token=${token}`);
        const data = await response.json();

        if (response.ok && data.success) {
          setVerificationStatus('success');
          setMessage(data.message);
        } else {
          setVerificationStatus('error');
          setMessage(data.detail || 'Verification failed');
        }
      } catch (error) {
        setVerificationStatus('error');
        setMessage('Network error during verification');
      }
    };

    verifyAccount();
  }, [token]);

  const getStatusIcon = () => {
    switch (verificationStatus) {
      case 'verifying':
        return (
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        );
      case 'success':
        return (
          <div className="rounded-full h-12 w-12 bg-green-500 flex items-center justify-center">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        );
      case 'error':
        return (
          <div className="rounded-full h-12 w-12 bg-red-500 flex items-center justify-center">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
        );
      default:
        return null;
    }
  };

  const getStatusText = () => {
    switch (verificationStatus) {
      case 'verifying':
        return 'Verifying your account...';
      case 'success':
        return 'Account Verified!';
      case 'error':
        return 'Verification Failed';
      default:
        return '';
    }
  };

  const getStatusColor = () => {
    switch (verificationStatus) {
      case 'verifying':
        return 'text-blue-500';
      case 'success':
        return 'text-green-500';
      case 'error':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-gray-800 rounded-lg shadow-xl p-8">
        <div className="text-center">
          {getStatusIcon()}
          
          <h2 className={`mt-6 text-2xl font-bold ${getStatusColor()}`}>
            {getStatusText()}
          </h2>
          
          <p className="mt-4 text-gray-300 text-sm">
            {message}
          </p>

          {verificationStatus === 'success' && (
            <div className="mt-6">
              <p className="text-gray-400 text-sm mb-4">
                Your account has been successfully verified. You can now close this window and return to CoinLink.
              </p>
              <button
                onClick={() => window.close()}
                className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
              >
                Close Window
              </button>
            </div>
          )}

          {verificationStatus === 'error' && (
            <div className="mt-6">
              <p className="text-gray-400 text-sm mb-4">
                If you continue to have issues, please contact support or try registering again.
              </p>
              <button
                onClick={() => window.location.href = '/'}
                className="bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
              >
                Return to CoinLink
              </button>
            </div>
          )}

          {verificationStatus === 'verifying' && (
            <div className="mt-6">
              <p className="text-gray-400 text-sm">
                Please wait while we verify your account...
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VerificationPage;
