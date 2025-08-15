import React, { useState, useEffect, useRef } from 'react';
import Chat from './components/Chat';
import TradingViewWidget from './components/TradingViewWidget';
import { WebSocketService } from './services/api';
// Removed direct client Coinbase WS; rely on backend WS crypto_ticker_update
import './App.css';
import PromptFeed from './components/PromptFeed';
import axios from 'axios'; // Added axios import

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [chatWidth, setChatWidth] = useState(60); // Percentage
  const [isResizing, setIsResizing] = useState(false);
  const resizerRef = useRef(null);
  const prevBtcPriceRef = useRef(null);
  const [btcFlash, setBtcFlash] = useState(null); // 'green' | 'red' | null
  const btcRowRef = useRef(null);
  const btcLeftRef = useRef(null);
  const btcTimeRef = useRef(null);
  const [btcMode, setBtcMode] = useState(0); // 0: full, 1: condensed, 2: hide 1h, 3: hide 1h + ultra condensed
  const measureRafRef = useRef(null);
  const [lastUpdateTs, setLastUpdateTs] = useState(null);
  
  // Helper function to format crypto prices with proper comma separation
  const formatNumber = (num) => {
    if (num >= 1000) {
      // Format with commas and 2 decimal places
      return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    } else if (num >= 1) {
      // Format with 2 decimal places
      return num.toFixed(2);
    } else if (num >= 0.01) {
      // Small values with 4 decimal places
      return num.toFixed(4);
    } else if (num >= 0.0001) {
      // Very small values with 6 decimal places
      return num.toFixed(6);
    } else {
      // Extremely small values in scientific notation
      return num.toExponential(2);
    }
  };

  useEffect(() => {
    // Initialize WebSocket connection using the service
    const wsService = new WebSocketService();
    
    console.log('Initializing WebSocket connection...');
    
    wsService.on('connected', () => {
      console.log('WebSocket connected event received');
      setIsConnected(true);
      console.log('Connected to CoinLink Bitcoin Analysis');
    });
    
    wsService.on('message', (data) => {
      console.log('WebSocket message received:', data);
      try {
        if (data && data.type === 'crypto_ticker_update') {
          // Update crypto ticker data with real-time updates
          if (data.data && Array.isArray(data.data)) {
            setCryptoData(data.data);
          }
        } else if (data && data.type === 'bitcoin_update') {
          const p = data.price || {};
          const nextPrice = p.price ?? p.last ?? p.bid ?? null;
          const next24h = p.change_24h ?? p.change24h ?? null;
          const nextVolume = p.volume ?? null;
          setBitcoinData((prev) => ({
            ...prev,
            price: nextPrice != null ? `$${Number(nextPrice).toFixed(2)}` : prev.price,
            change24h: next24h != null ? `${Number(next24h) >= 0 ? '+' : ''}${Number(next24h).toFixed(2)}%` : prev.change24h,
            volume24h: nextVolume != null ? nextVolume : prev.volume24h,
          }));
          if (nextPrice != null || next24h != null) {
            setCryptoData((prev) => prev.map((c) => c.symbol === 'BTC' ? {
              ...c,
              price: nextPrice != null ? formatDollars(nextPrice) : c.price,
              change: next24h != null ? `${Number(next24h) >= 0 ? '+' : ''}${Number(next24h).toFixed(2)}%` : c.change,
            } : c));
            setLastUpdateTs(new Date());
          }
        }
      } catch (error) {
        console.error('Error processing WebSocket message:', error);
      }
    });
    
    wsService.on('disconnected', (data) => {
      console.log('WebSocket disconnected event received:', data);
      setIsConnected(false);
      console.log('Disconnected from server:', data);
    });
    
    wsService.on('error', (data) => {
      console.log('WebSocket error event received:', data);
      console.error('WebSocket error:', data);
      setIsConnected(false);
    });
    
    // Connect to WebSocket with better error handling
    console.log('Attempting to connect to WebSocket...');
    wsService.connect().then(() => {
      console.log('WebSocket connection promise resolved');
    }).catch(error => {
      console.error('Failed to connect to WebSocket:', error);
      setIsConnected(false);
      // Don't crash the app - just log the error and continue without WebSocket
    });
    
    return () => {
      console.log('Cleaning up WebSocket connection');
      try {
        wsService.disconnect();
      } catch (error) {
        console.error('Error during WebSocket cleanup:', error);
      }
    };
  }, []);

  const handlePointerDown = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsResizing(true);
    try {
      resizerRef.current?.setPointerCapture?.(e.pointerId);
    } catch {}
    window.addEventListener('pointermove', handlePointerMove);
    window.addEventListener('pointerup', handlePointerUp);
    window.addEventListener('pointercancel', handlePointerUp);
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  };

  const handlePointerMove = (e) => {
    if (!isResizing) return;

    const container = resizerRef.current?.parentElement;
    if (!container) return;

    const rect = container.getBoundingClientRect();
    const newChatWidth = ((e.clientX - rect.left) / rect.width) * 100;

    // Clamp chat width between 25% and 75%
    const clamped = Math.max(25, Math.min(75, newChatWidth));
    setChatWidth(clamped);
  };

  const handlePointerUp = (e) => {
    setIsResizing(false);
    window.removeEventListener('pointermove', handlePointerMove);
    window.removeEventListener('pointerup', handlePointerUp);
    window.removeEventListener('pointercancel', handlePointerUp);
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
    try {
      if (e && typeof e.pointerId !== 'undefined') {
        resizerRef.current?.releasePointerCapture?.(e.pointerId);
      }
    } catch {}
    // Snap to helpful breakpoints for easier layout control
    const snapPoints = [25, 33, 40, 50, 60, 67, 75];
    const nearest = snapPoints.reduce((a, b) => Math.abs(b - chatWidth) < Math.abs(a - chatWidth) ? b : a);
    if (Math.abs(nearest - chatWidth) <= 2) setChatWidth(nearest);
  };

  const resetChatWidth = () => setChatWidth(50);

  // Keyboard accessibility for the resizer
  const handleResizerKeyDown = (e) => {
    const step = e.shiftKey ? 5 : 2;
    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      setChatWidth((w) => Math.max(25, Math.min(75, w - step)));
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      setChatWidth((w) => Math.max(25, Math.min(75, w + step)));
    } else if (e.key === 'Home') {
      e.preventDefault();
      setChatWidth(25);
    } else if (e.key === 'End') {
      e.preventDefault();
      setChatWidth(75);
    } else if (e.key.toLowerCase() === 'r') {
      // quick reset
      setChatWidth(50);
    }
  };

  // Cryptocurrency ticker data (top 50 by market cap)
  const [cryptoData, setCryptoData] = useState([
    { symbol: 'BTC', name: 'Bitcoin', price: 0, change_24h: 0, rank: 1, market_cap: 2318000000000 },
    { symbol: 'ETH', name: 'Ethereum', price: 0, change_24h: 0, rank: 2, market_cap: 390000000000 },
    { symbol: 'SOL', name: 'Solana', price: 0, change_24h: 0, rank: 3, market_cap: 64000000000 },
    { symbol: 'BNB', name: 'BNB', price: 567.89, change_24h: 3.12, rank: 4, market_cap: 87000000000 },
    { symbol: 'XRP', name: 'XRP', price: 0.5678, change_24h: 1.89, rank: 5, market_cap: 30900000000 },
    { symbol: 'DOGE', name: 'Dogecoin', price: 0.1234, change_24h: -1.23, rank: 6, market_cap: 17600000000 },
    { symbol: 'ADA', name: 'Cardano', price: 0.4567, change_24h: 2.34, rank: 7, market_cap: 16300000000 },
    { symbol: 'AVAX', name: 'Avalanche', price: 34.56, change_24h: 4.56, rank: 8, market_cap: 13100000000 },
    { symbol: 'TRX', name: 'TRON', price: 0.0987, change_24h: 0.87, rank: 9, market_cap: 8600000000 },
    { symbol: 'LINK', name: 'Chainlink', price: 18.90, change_24h: 3.45, rank: 10, market_cap: 11300000000 },
    { symbol: 'DOT', name: 'Polkadot', price: 7.89, change_24h: 2.78, rank: 11, market_cap: 11000000000 },
    { symbol: 'MATIC', name: 'Polygon', price: 0.8765, change_24h: 4.32, rank: 12, market_cap: 8100000000 },
    { symbol: 'TON', name: 'Toncoin', price: 6.78, change_24h: 1.67, rank: 13, market_cap: 34600000000 },
    { symbol: 'SHIB', name: 'Shiba Inu', price: 0.000023, change_24h: 2.89, rank: 14, market_cap: 13500000000 },
    { symbol: 'LTC', name: 'Litecoin', price: 78.90, change_24h: 1.45, rank: 15, market_cap: 5800000000 },
    { symbol: 'UNI', name: 'Uniswap', price: 12.34, change_24h: 3.21, rank: 16, market_cap: 9200000000 },
    { symbol: 'BCH', name: 'Bitcoin Cash', price: 456.78, change_24h: 2.67, rank: 17, market_cap: 8900000000 },
    { symbol: 'XLM', name: 'Stellar', price: 0.1234, change_24h: 1.89, rank: 18, market_cap: 3500000000 },
    { symbol: 'ATOM', name: 'Cosmos', price: 9.87, change_24h: 4.12, rank: 19, market_cap: 3800000000 },
    { symbol: 'NEAR', name: 'NEAR Protocol', price: 5.67, change_24h: 2.34, rank: 20, market_cap: 6200000000 },
    { symbol: 'XMR', name: 'Monero', price: 234.56, change_24h: 1.78, rank: 21, market_cap: 4300000000 },
    { symbol: 'OP', name: 'Optimism', price: 3.45, change_24h: 5.67, rank: 22, market_cap: 15500000000 },
    { symbol: 'ARB', name: 'Arbitrum', price: 1.23, change_24h: 3.89, rank: 23, market_cap: 12300000000 },
    { symbol: 'FIL', name: 'Filecoin', price: 6.78, change_24h: 2.45, rank: 24, market_cap: 3700000000 },
    { symbol: 'APT', name: 'Aptos', price: 8.90, change_24h: 4.23, rank: 25, market_cap: 8900000000 },
    { symbol: 'HBAR', name: 'Hedera', price: 0.0987, change_24h: 1.67, rank: 26, market_cap: 3300000000 },
    { symbol: 'CRO', name: 'Cronos', price: 0.1234, change_24h: 2.89, rank: 27, market_cap: 3200000000 },
    { symbol: 'VET', name: 'VeChain', price: 0.0456, change_24h: 3.12, rank: 28, market_cap: 3300000000 },
    { symbol: 'MKR', name: 'Maker', price: 2345.67, change_24h: 1.45, rank: 29, market_cap: 2100000000 },
    { symbol: 'KAS', name: 'Kaspa', price: 0.1234, change_24h: 5.78, rank: 30, market_cap: 2900000000 },
    { symbol: 'INJ', name: 'Injective', price: 34.56, change_24h: 2.34, rank: 31, market_cap: 3400000000 },
    { symbol: 'RUNE', name: 'THORChain', price: 7.89, change_24h: 4.56, rank: 32, market_cap: 2600000000 },
    { symbol: 'GRT', name: 'The Graph', price: 0.2345, change_24h: 1.89, rank: 33, market_cap: 2300000000 },
    { symbol: 'THETA', name: 'Theta Network', price: 2.34, change_24h: 3.21, rank: 34, market_cap: 2300000000 },
    { symbol: 'FTM', name: 'Fantom', price: 0.4567, change_24h: 2.78, rank: 35, market_cap: 1200000000 },
    { symbol: 'ALGO', name: 'Algorand', price: 0.2345, change_24h: 1.67, rank: 36, market_cap: 1900000000 },
    { symbol: 'LDO', name: 'Lido DAO', price: 2.89, change_24h: 4.23, rank: 37, market_cap: 2500000000 },
    { symbol: 'IMX', name: 'Immutable', price: 3.45, change_24h: 2.45, rank: 38, market_cap: 6900000000 },
    { symbol: 'SUI', name: 'Sui', price: 1.67, change_24h: 3.89, rank: 39, market_cap: 16700000000 },
    { symbol: 'SEI', name: 'Sei', price: 0.5678, change_24h: 2.12, rank: 40, market_cap: 5600000000 },
    { symbol: 'MANA', name: 'Decentraland', price: 0.8765, change_24h: -1.78, rank: 41, market_cap: 1600000000 },
    { symbol: 'SAND', name: 'The Sandbox', price: 0.4321, change_24h: 4.56, rank: 42, market_cap: 990000000 },
    { symbol: 'AXS', name: 'Axie Infinity', price: 12.34, change_24h: -2.89, rank: 43, market_cap: 1700000000 },
    { symbol: 'AAVE', name: 'Aave', price: 234.56, change_24h: 6.78, rank: 44, market_cap: 3700000000 },
    { symbol: 'EOS', name: 'EOS', price: 0.8765, change_24h: 3.45, rank: 45, market_cap: 1000000000 },
    { symbol: 'QNT', name: 'Quant', price: 123.45, change_24h: -5.67, rank: 46, market_cap: 1800000000 },
    { symbol: 'FLOW', name: 'Flow', price: 2.34, change_24h: 2.34, rank: 47, market_cap: 3200000000 },
    { symbol: 'CHZ', name: 'Chiliz', price: 0.1234, change_24h: 1.56, rank: 48, market_cap: 1000000000 },
    { symbol: 'RNDR', name: 'Render', price: 6.78, change_24h: 3.67, rank: 49, market_cap: 2500000000 },
    { symbol: 'SNX', name: 'Synthetix', price: 3.45, change_24h: -1.23, rank: 50, market_cap: 1100000000 }
  ]);

  // Bitcoin data state
  const [bitcoinData, setBitcoinData] = useState({
    price: 0,
    change1h: 0,
    change24h: 0,
    change7d: 0,
    volume24h: 0
  });

  // Listen to backend WS for real-time crypto ticker updates
  useEffect(() => {
    const wsService = new WebSocketService();
    wsService.on('message', (data) => {
      try {
        if (data && data.type === 'crypto_ticker_update' && Array.isArray(data.data)) {
          const symbolToData = new Map(data.data.map(d => [d.symbol, d]));
          setCryptoData(prev => prev.map(c => {
            const d = symbolToData.get(c.symbol);
            if (!d) return c;
            return {
              ...c,
              price: d.price,
              change_24h: d.change_24h,
            };
          }));
          const btc = symbolToData.get('BTC');
          if (btc) {
            setBitcoinData(prev => ({
              ...prev,
              price: btc.price,
              change24h: btc.change_24h,
            }));
          }
        }
      } catch (e) {}
    });
    wsService.connect().catch(() => {});
    return () => wsService.disconnect();
  }, []);

  // Removed old Bitcoin fetch logic - now handled by Coinbase WebSocket

  const parseNumber = (value) => {
    if (typeof value === 'number') return value;
    const cleaned = String(value).replace(/[^0-9.\-]/g, '');
    const n = parseFloat(cleaned);
    return isNaN(n) ? 0 : n;
  };

  const formatDollars = (value) => {
    const n = parseNumber(value);
    return '$' + n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  const getChangeHex = (change) => {
    const n = typeof change === 'number' ? change : parseFloat(String(change).replace('%', ''));
    if (isNaN(n) || n === 0) return '#A0A0A0';
    return n > 0 ? '#00D964' : '#FF3737';
  };

  // Removed - flash effect now handled in Coinbase WebSocket update

  // Responsively contain time segment to respect right margin and keep 30d visible
  useEffect(() => {
    const time = btcTimeRef.current;
    if (!time) return;

    const measure = () => {
      cancelAnimationFrame(measureRafRef.current);
      measureRafRef.current = requestAnimationFrame(() => {
        const overflow = time.scrollWidth - time.clientWidth;
        let mode = btcMode;
        if (overflow > 8 && mode < 3) mode = mode + 1;
        else if (overflow <= -64 && mode > 0) mode = mode - 1; // hysteresis to prevent flicker
        if (mode !== btcMode) setBtcMode(mode);
      });
    };

    const ro = new ResizeObserver(measure);
    ro.observe(time);
    measure();

    return () => {
      cancelAnimationFrame(measureRafRef.current);
      try { ro.disconnect(); } catch {}
    };
  }, [btcMode, chatWidth]);

  // Re-measure when numbers change (debounced a bit)
  useEffect(() => {
    const id = setTimeout(() => {
      const time = btcTimeRef.current;
      if (!time) return;
      const overflow = time.scrollWidth - time.clientWidth;
      let mode = btcMode;
      if (overflow > 8 && mode < 3) mode = mode + 1;
      else if (overflow <= -64 && mode > 0) mode = mode - 1;
      if (mode !== btcMode) setBtcMode(mode);
    }, 120);
    return () => clearTimeout(id);
  }, [bitcoinData.change1h, bitcoinData.change24h, bitcoinData.change7d, bitcoinData.change30d]);

  return (
    <div className="flex h-screen overflow-hidden" style={{ backgroundColor: '#0F0F0F' }}>
      {/* Chat Panel */}
      <div 
        className="flex flex-col border-r border-gray-700 min-w-0"
        style={{ width: `${chatWidth}%` }}
      >
        <Chat 
          isConnected={isConnected}
        />
      </div>
      
      {/* Resizer */}
      <div
        ref={resizerRef}
        className="relative group w-8 md:w-10 h-full flex-shrink-0 z-20 cursor-col-resize"
        onPointerDown={handlePointerDown}
        onDoubleClick={resetChatWidth}
        onKeyDown={handleResizerKeyDown}
        role="separator"
        aria-orientation="vertical"
        title="Drag to resize. Double-click to split 50/50."
        tabIndex={0}
        aria-valuemin={25}
        aria-valuemax={75}
        aria-valuenow={Math.round(chatWidth)}
        aria-label="Resize chat and chart panes"
        style={{ userSelect: 'none', touchAction: 'none' }}
      >
        {/* Wide invisible hit area with a clear visible handle */}
        <div className="absolute inset-0"></div>
        <div className="absolute inset-y-0 left-1/2 -translate-x-1/2 w-1 bg-[#2A2A2A] group-hover:bg-[#3A3A3A] transition-colors"></div>
        <div className="absolute top-1/2 -translate-y-1/2 left-1/2 -translate-x-1/2 h-16 w-2 rounded-full bg-[#3A3A3A]/60 group-hover:bg-[#3A3A3A] shadow" />
        {/* Helper tooltip while dragging */}
        <div className={`absolute -top-7 left-1/2 -translate-x-1/2 px-2 py-0.5 rounded text-xs text-gray-300 bg-[#1B1B1B] border border-[#2A2A2A] pointer-events-none transition-opacity ${isResizing ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}>
          {Math.round(chatWidth)}%
        </div>
      </div>
      
      {/* Right Panel with Prompt Feed, Crypto Feed, Bitcoin Container, and TradingView */}
      <div 
        className="flex flex-col min-w-0"
        style={{ width: `${100 - chatWidth}%` }}
      >
        {/* Prompt Feed - time-sensitive, no horizontal scroll */}
        <PromptFeed onPromptClick={(text) => {
          try {
            const input = document.querySelector('input[placeholder^="Ask about Bitcoin"]');
            if (input) { input.value = text; input.dispatchEvent(new Event('input', { bubbles: true })); }
          } catch {}
        }} />
        {/* Tick-by-tick Cryptocurrency Container and Bitcoin Price Container - Same Height */}
        <div className="flex flex-col">
          {/* Tick-by-tick Cryptocurrency Container - At the top */}
          <div className="ticker-container" style={{ backgroundColor: '#0F0F0F', borderBottom: '1px solid #2d3748' }}>
            <div className="ticker-wrapper">
              <div className="ticker-content ticker-scroll">
                {/* First set of tickers with exact formatting */}
                {cryptoData
                  .filter(crypto => !['USDT', 'USDC', 'DAI', 'BUSD', 'TUSD'].includes(crypto.symbol))
                  .sort((a, b) => a.rank - b.rank)
                  .slice(0, 50)
                  .map((crypto) => (
                    <span key={`first-${crypto.symbol}`} className="ticker-item">
                      <span className="ticker-symbol">{crypto.symbol}</span>
                      <span className="ticker-price" style={{
                        color: crypto.flash === 'green' ? '#00D964' : crypto.flash === 'red' ? '#FF3737' : '#ffffff',
                        transition: 'color 200ms ease'
                      }}>${formatNumber(crypto.price)}</span>
                      <span className="ticker-change" style={{ 
                        color: crypto.change_24h > 0 ? '#00D964' : crypto.change_24h < 0 ? '#FF3737' : '#A0A0A0' 
                      }}>({crypto.change_24h > 0 ? '+' : ''}{crypto.change_24h ? crypto.change_24h.toFixed(2) : '0.00'}%)</span>
                      <span className="ticker-separator">•</span>
                    </span>
                  ))}
                {/* Duplicate for seamless loop */}
                {cryptoData
                  .filter(crypto => !['USDT', 'USDC', 'DAI', 'BUSD', 'TUSD'].includes(crypto.symbol))
                  .sort((a, b) => a.rank - b.rank)
                  .slice(0, 50)
                  .map((crypto) => (
                    <span key={`second-${crypto.symbol}`} className="ticker-item">
                      <span className="ticker-symbol">{crypto.symbol}</span>
                      <span className="ticker-price" style={{
                        color: crypto.flash === 'green' ? '#00D964' : crypto.flash === 'red' ? '#FF3737' : '#ffffff',
                        transition: 'color 200ms ease'
                      }}>${formatNumber(crypto.price)}</span>
                      <span className="ticker-change" style={{ 
                        color: crypto.change_24h > 0 ? '#00D964' : crypto.change_24h < 0 ? '#FF3737' : '#A0A0A0' 
                      }}>({crypto.change_24h > 0 ? '+' : ''}{crypto.change_24h ? crypto.change_24h.toFixed(2) : '0.00'}%)</span>
                      <span className="ticker-separator">•</span>
                    </span>
                  ))}
              </div>
            </div>
          </div>
          
          {/* Bitcoin Price Container - New Format: Bitcoin (BTC) $97,420.15 (+2.34% 1H) (+5.67% 24H) (+12.89% 7D) */}
          <div className="bitcoin-feed" style={{ 
            backgroundColor: '#0F0F0F', 
            height: '40px',
            fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
            fontSize: '17px',
            lineHeight: '40px',
            padding: '0 20px',
            display: 'flex',
            alignItems: 'center',
            borderBottom: '1px solid #2d3748'
          }}>
            <span className="font-medium text-white">Bitcoin (BTC)</span>
            <span
              className="ml-3 text-white font-normal"
              style={{ 
                color: btcFlash === 'green' ? '#00D964' : btcFlash === 'red' ? '#FF3737' : '#ffffff',
                transition: 'color 200ms ease' 
              }}
            >
              ${formatNumber(bitcoinData.price)}
            </span>
            
            {/* Time-based Changes */}
            <span className="ml-4">
              <span style={{ color: bitcoinData.change1h > 0 ? '#00D964' : bitcoinData.change1h < 0 ? '#FF3737' : '#A0A0A0' }}>
                ({bitcoinData.change1h > 0 ? '+' : ''}{bitcoinData.change1h ? bitcoinData.change1h.toFixed(2) : '0.00'}% 1H)
              </span>
              <span className="ml-3" style={{ color: bitcoinData.change24h > 0 ? '#00D964' : bitcoinData.change24h < 0 ? '#FF3737' : '#A0A0A0' }}>
                ({bitcoinData.change24h > 0 ? '+' : ''}{bitcoinData.change24h ? bitcoinData.change24h.toFixed(2) : '0.00'}% 24H)
              </span>
              <span className="ml-3" style={{ color: bitcoinData.change7d > 0 ? '#00D964' : bitcoinData.change7d < 0 ? '#FF3737' : '#A0A0A0' }}>
                ({bitcoinData.change7d > 0 ? '+' : ''}{bitcoinData.change7d ? bitcoinData.change7d.toFixed(2) : '0.00'}% 7D)
              </span>
            </span>
          </div>
        </div>
        
        {/* TradingView Widget - At the bottom with balanced side margins */}
        <div className="flex-1 min-h-0 chart-wrapper">
          <TradingViewWidget />
        </div>
      </div>
      
    </div>
  );
}

export default App;
