import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import ErrorBoundary from './components/ErrorBoundary';

// Suppress external/cross-origin or event-like errors to avoid noisy overlays in development
// Catch as early as possible (capture phase) and suppress noisy external/event-like errors
window.addEventListener('error', (e) => {
  try {
    const isScriptError = e && (e.message === 'Script error.' || typeof e.message === 'object');
    const fromExternal = e && typeof e.filename === 'string' && /tradingview\.com|coinbase\.com/i.test(e.filename);
    const noErrorObject = !e || !('error' in e) || e.error == null; // typical cross-origin script error
    const eventLike = e && (e instanceof Event);
    if (isScriptError || fromExternal || noErrorObject || eventLike) {
      e.preventDefault();
    }
  } catch {}
}, true);

// Fallback handler that some browsers consult; returning true suppresses the console overlay
window.onerror = function(message, source, lineno, colno, error) {
  try {
    const isScriptError = message === 'Script error.' || Object.prototype.toString.call(message) === '[object Event]';
    const fromExternal = typeof source === 'string' && /tradingview\.com|coinbase\.com/i.test(source);
    if (isScriptError || fromExternal) {
      return true;
    }
  } catch {}
  return false;
};

// Prevent overlay for cross-origin Promise rejections without useful context
window.addEventListener('unhandledrejection', (e) => {
  try {
    const r = e && e.reason;
    const isNoReason = !r;
    const isEventLike = r && (typeof r === 'object') && (r.type || r.target);
    if (isNoReason || isEventLike) {
      e.preventDefault();
    }
  } catch {}
}, true);

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);
