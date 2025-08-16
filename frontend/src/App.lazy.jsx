import React, { lazy, Suspense, useState, useEffect, useRef } from 'react';
import { WebSocketService } from './services/api';
import './App.css';

// Lazy load heavy components for code splitting
const Chat = lazy(() => import('./components/Chat'));
const TradingViewWidget = lazy(() => import('./components/TradingViewWidget'));
const PromptFeed = lazy(() => import('./components/PromptFeed'));

// Loading fallback component
const LoadingFallback = () => (
  <div className="flex items-center justify-center h-full">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
  </div>
);

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [chatWidth, setChatWidth] = useState(60);
  const [isResizing, setIsResizing] = useState(false);
  const resizerRef = useRef(null);
  const prevBtcPriceRef = useRef(null);
  const [btcFlash, setBtcFlash] = useState(null);
  const btcRowRef = useRef(null);
  const btcLeftRef = useRef(null);
  const btcTimeRef = useRef(null);
  const [btcMode, setBtcMode] = useState(0);
  const measureRafRef = useRef(null);
  const [lastUpdateTs, setLastUpdateTs] = useState(null);
  
  const formatNumber = (num) => {
    if (num >= 1000) {
      return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    } else if (num >= 1) {
      return num.toFixed(2);
    } else if (num >= 0.01) {
      return num.toFixed(4);
    } else if (num >= 0.0001) {
      return num.toFixed(6);
    } else {
      return num.toExponential(2);
    }
  };

  useEffect(() => {
    const wsService = new WebSocketService();
    
    console.log('Initializing WebSocket connection...');
    
    wsService.on('connected', () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    });
    
    wsService.on('disconnected', () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    });

    wsService.on('crypto_ticker_update', (ticker) => {
      if (ticker.symbol === 'BTC-USD') {
        const newPrice = ticker.price;
        if (prevBtcPriceRef.current !== null) {
          if (newPrice > prevBtcPriceRef.current) {
            setBtcFlash('green');
            setTimeout(() => setBtcFlash(null), 500);
          } else if (newPrice < prevBtcPriceRef.current) {
            setBtcFlash('red');
            setTimeout(() => setBtcFlash(null), 500);
          }
        }
        prevBtcPriceRef.current = newPrice;
      }
    });

    wsService.connect();

    return () => {
      wsService.disconnect();
    };
  }, []);

  const startResize = () => {
    setIsResizing(true);
  };

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isResizing) return;
      const newWidth = (e.clientX / window.innerWidth) * 100;
      if (newWidth >= 20 && newWidth <= 80) {
        setChatWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  const formatDollars = (v) => {
    const negative = v < 0;
    let vAbs = Math.abs(v);
    
    if (vAbs >= 1000000000) {
      vAbs = vAbs / 1000000000;
      return (negative ? '-' : '') + '$' + vAbs.toFixed(2) + 'B';
    } else if (vAbs >= 1000000) {
      vAbs = vAbs / 1000000;
      return (negative ? '-' : '') + '$' + vAbs.toFixed(2) + 'M';
    } else if (vAbs >= 1000) {
      return (negative ? '-' : '') + '$' + formatNumber(vAbs);
    } else {
      return (negative ? '-' : '') + '$' + vAbs.toFixed(2);
    }
  };

  useEffect(() => {
    const doMeasure = () => {
      if (btcRowRef.current && btcLeftRef.current && btcTimeRef.current) {
        const btcRow = btcRowRef.current;
        const btcLeft = btcLeftRef.current;
        const btcTime = btcTimeRef.current;
        
        const rowW = btcRow.offsetWidth;
        const leftW = btcLeft.offsetWidth;
        const timeW = btcTime.offsetWidth;
        const effectiveWidth = leftW + timeW;
        
        if (rowW < effectiveWidth + 50) {
          if (btcMode === 0) {
            setBtcMode(1);
          } else if (btcMode === 1 && rowW < effectiveWidth) {
            setBtcMode(2);
          } else if (btcMode === 2 && rowW < leftW + 50) {
            setBtcMode(3);
          }
        } else {
          if (btcMode === 3 && rowW >= leftW + 100) {
            setBtcMode(2);
          } else if (btcMode === 2 && rowW >= effectiveWidth + 50) {
            setBtcMode(1);
          } else if (btcMode === 1 && rowW >= effectiveWidth + 100) {
            setBtcMode(0);
          }
        }
      }
      
      measureRafRef.current = requestAnimationFrame(doMeasure);
    };
    
    measureRafRef.current = requestAnimationFrame(doMeasure);
    
    return () => {
      if (measureRafRef.current) {
        cancelAnimationFrame(measureRafRef.current);
      }
    };
  }, [btcMode, formatDollars]);

  return (
    <div className="App h-screen flex flex-col">
      <div className="flex-1 flex">
        <div 
          className="flex flex-col"
          style={{ width: `${chatWidth}%` }}
        >
          <Suspense fallback={<LoadingFallback />}>
            <Chat isConnected={isConnected} />
          </Suspense>
        </div>
        
        <div 
          ref={resizerRef}
          className="w-1 bg-gray-700 cursor-col-resize hover:bg-blue-500 transition-colors"
          onMouseDown={startResize}
        />
        
        <div 
          className="flex flex-col overflow-hidden"
          style={{ width: `${100 - chatWidth}%` }}
        >
          <div className="flex flex-col h-full">
            <div className="flex-1 min-h-0">
              <Suspense fallback={<LoadingFallback />}>
                <TradingViewWidget />
              </Suspense>
            </div>
            <div className="h-48 border-t border-gray-700">
              <Suspense fallback={<LoadingFallback />}>
                <PromptFeed />
              </Suspense>
            </div>
          </div>
        </div>
      </div>
      
      <div className={`status-bar ${isConnected ? 'connected' : 'disconnected'}`}>
        <span className="status-indicator"></span>
        {isConnected ? 'Connected' : 'Disconnected'}
      </div>
    </div>
  );
}

export default App;