import React, { useState, useEffect, useRef } from 'react';
import Chat from './components/Chat';
import TradingViewWidget from './components/TradingViewWidget';
import { WebSocketService } from './services/api';
import './App.css';
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
        if (data && data.type === 'bitcoin_update') {
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
    { symbol: 'BTC', name: 'Bitcoin', price: '$118,413.39', change: '+2.45%' },
    { symbol: 'ETH', name: 'Ethereum', price: '$3,245.67', change: '+1.23%' },
    { symbol: 'BNB', name: 'BNB', price: '$567.89', change: '+3.12%' },
    { symbol: 'SOL', name: 'Solana', price: '$145.67', change: '+5.67%' },
    { symbol: 'USDC', name: 'USD Coin', price: '$1.00', change: '0.00%' },
    { symbol: 'XRP', name: 'XRP', price: '$0.5678', change: '+1.89%' },
    { symbol: 'ADA', name: 'Cardano', price: '$0.4567', change: '+2.34%' },
    { symbol: 'AVAX', name: 'Avalanche', price: '$34.56', change: '+4.56%' },
    { symbol: 'DOGE', name: 'Dogecoin', price: '$0.1234', change: '+1.23%' },
    { symbol: 'TRX', name: 'TRON', price: '$0.0987', change: '+0.87%' },
    { symbol: 'LINK', name: 'Chainlink', price: '$18.90', change: '+3.45%' },
    { symbol: 'DOT', name: 'Polkadot', price: '$7.89', change: '+2.78%' },
    { symbol: 'MATIC', name: 'Polygon', price: '$0.8765', change: '+4.32%' },
    { symbol: 'TON', name: 'Toncoin', price: '$6.78', change: '+1.67%' },
    { symbol: 'SHIB', name: 'Shiba Inu', price: '$0.000023', change: '+2.89%' },
    { symbol: 'DAI', name: 'Dai', price: '$1.00', change: '0.00%' },
    { symbol: 'LTC', name: 'Litecoin', price: '$78.90', change: '+1.45%' },
    { symbol: 'UNI', name: 'Uniswap', price: '$12.34', change: '+3.21%' },
    { symbol: 'BCH', name: 'Bitcoin Cash', price: '$456.78', change: '+2.67%' },
    { symbol: 'XLM', name: 'Stellar', price: '$0.1234', change: '+1.89%' },
    { symbol: 'ATOM', name: 'Cosmos', price: '$9.87', change: '+4.12%' },
    { symbol: 'NEAR', name: 'NEAR Protocol', price: '$5.67', change: '+2.34%' },
    { symbol: 'XMR', name: 'Monero', price: '$234.56', change: '+1.78%' },
    { symbol: 'OP', name: 'Optimism', price: '$3.45', change: '+5.67%' },
    { symbol: 'ARB', name: 'Arbitrum', price: '$1.23', change: '+3.89%' },
    { symbol: 'FIL', name: 'Filecoin', price: '$6.78', change: '+2.45%' },
    { symbol: 'APT', name: 'Aptos', price: '$8.90', change: '+4.23%' },
    { symbol: 'HBAR', name: 'Hedera', price: '$0.0987', change: '+1.67%' },
    { symbol: 'CRO', name: 'Cronos', price: '$0.1234', change: '+2.89%' },
    { symbol: 'VET', name: 'VeChain', price: '$0.0456', change: '+3.12%' },
    { symbol: 'MKR', name: 'Maker', price: '$2,345.67', change: '+1.45%' },
    { symbol: 'KAS', name: 'Kaspa', price: '$0.1234', change: '+5.78%' },
    { symbol: 'INJ', name: 'Injective', price: '$34.56', change: '+2.34%' },
    { symbol: 'RUNE', name: 'THORChain', price: '$7.89', change: '+4.56%' },
    { symbol: 'GRT', name: 'The Graph', price: '$0.2345', change: '+1.89%' },
    { symbol: 'THETA', name: 'Theta Network', price: '$2.34', change: '+3.21%' },
    { symbol: 'FTM', name: 'Fantom', price: '$0.4567', change: '+2.78%' },
    { symbol: 'ALGO', name: 'Algorand', price: '$0.2345', change: '+1.67%' },
    { symbol: 'LDO', name: 'Lido DAO', price: '$2.89', change: '+4.23%' },
    { symbol: 'IMX', name: 'Immutable', price: '$3.45', change: '+2.45%' },
    { symbol: 'SUI', name: 'Sui', price: '$1.67', change: '+3.89%' },
    { symbol: 'SEI', name: 'Sei', price: '$0.5678', change: '+2.12%' },
    { symbol: 'MANTLE', name: 'Mantle', price: '$0.8765', change: '+1.78%' },
    { symbol: 'STRK', name: 'Starknet', price: '$1.23', change: '+4.56%' },
    { symbol: 'ZETA', name: 'ZetaChain', price: '$2.34', change: '+2.89%' },
    { symbol: 'BONK', name: 'Bonk', price: '$0.000045', change: '+6.78%' },
    { symbol: 'JUP', name: 'Jupiter', price: '$0.8765', change: '+3.45%' },
    { symbol: 'WIF', name: 'dogwifhat', price: '$2.34', change: '+5.67%' },
    { symbol: 'PEPE', name: 'Pepe', price: '$0.000012', change: '+2.34%' },
    { symbol: 'FLOKI', name: 'FLOKI', price: '$0.000023', change: '+4.56%' },
    { symbol: 'BOME', name: 'Book of Meme', price: '$0.0123', change: '+3.78%' }
  ]);

  // Bitcoin data state
  const [bitcoinData, setBitcoinData] = useState({
    price: '$0.00',
    change1h: '+0.00%',
    change24h: '+0.00%',
    change7d: '+0.00%',
    change30d: '+0.00%'
  });

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setBitcoinData(prev => ({
        ...prev,
        price: `$${(118000 + Math.random() * 1000).toFixed(2)}`,
        change1h: `${Math.random() > 0.5 ? '+' : '-'}${(Math.random() * 5).toFixed(2)}%`,
        change12h: `${Math.random() > 0.5 ? '+' : '-'}${(Math.random() * 8).toFixed(2)}%`,
        change24h: `${Math.random() > 0.5 ? '+' : '-'}${(Math.random() * 10).toFixed(2)}%`,
        change7d: `${Math.random() > 0.5 ? '+' : '-'}${(Math.random() * 15).toFixed(2)}%`,
        change30d: `${Math.random() > 0.5 ? '+' : '-'}${(Math.random() * 25).toFixed(2)}%`,
        volume24h: (40 + Math.random() * 20) * 1e9
      }));
    }, 2000); // Update every 2 seconds

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const fetchBitcoinData = async () => {
      try {
        const response = await axios.get('/api/bitcoin/price');
        const data = response.data;
        
        // Update flash state based on price change
        if (prevBtcPriceRef.current !== null) {
                  const prevPrice = parseFloat(prevBtcPriceRef.current.replace(/[^0-9.-]/g, ''));
        const currentPrice = parseFloat(data.price.replace(/[^0-9.-]/g, ''));
          setBtcFlash(currentPrice > prevPrice ? 'green' : currentPrice < prevPrice ? 'red' : null);
        }
        
        prevBtcPriceRef.current = data.price;
        setBitcoinData(data);
      } catch (error) {
        console.error('Error fetching Bitcoin data:', error);
      }
    };
    
    // Initial fetch
    fetchBitcoinData();
    
    // Poll every 5 seconds
    const intervalId = setInterval(fetchBitcoinData, 5000);
    
    return () => clearInterval(intervalId);
  }, []);

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

  // Flash only the BTC price value (not the whole bar) when updated
  useEffect(() => {
    const current = parseNumber(bitcoinData.price);
    const prev = prevBtcPriceRef.current;
    if (prev !== null && prev !== undefined && current !== prev) {
      setBtcFlash(current > prev ? 'green' : 'red');
      setTimeout(() => setBtcFlash(null), 200);
    }
    prevBtcPriceRef.current = current;
  }, [bitcoinData.price]);

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
      
      {/* Right Panel with Crypto Feed, Bitcoin Container, and TradingView */}
      <div 
        className="flex flex-col min-w-0"
        style={{ width: `${100 - chatWidth}%` }}
      >
        {/* Tick-by-tick Cryptocurrency Container and Bitcoin Price Container - Same Height */}
        <div className="flex flex-col">
          {/* Tick-by-tick Cryptocurrency Container - At the top */}
          <div className="ticker-container" style={{ backgroundColor: '#0F0F0F', borderBottom: '1px solid #2d3748' }}>
            <div className="ticker-wrapper overflow-hidden h-full">
              <div className="ticker-content animate-ticker flex items-center h-full whitespace-nowrap">
                {cryptoData.filter(crypto => crypto.symbol !== 'USDT' && crypto.symbol !== 'USDC' && crypto.symbol !== 'DAI').map((crypto, index) => (
                  <span key={index} className="inline-flex items-center px-2">
                    <span className="font-semibold text-white">{crypto.symbol}</span>
                    <span className="ml-2 text-white">{crypto.price}</span>
                    <span className="ml-1" style={{ color: crypto.change.startsWith('+') ? '#00D964' : crypto.change.startsWith('-') ? '#FF3737' : '#A0A0A0' }}>({crypto.change})</span>
                    {index < cryptoData.length - 1 && <span className="mx-3" style={{ color: '#4a5568' }}>•</span>}
                  </span>
                ))}
                {/* Duplicate for continuous scroll */}
                {cryptoData.filter(crypto => crypto.symbol !== 'USDT' && crypto.symbol !== 'USDC' && crypto.symbol !== 'DAI').map((crypto, index) => (
                  <span key={`dup-${index}`} className="inline-flex items-center px-2">
                    <span className="font-semibold text-white">{crypto.symbol}</span>
                    <span className="ml-2 text-white">{crypto.price}</span>
                    <span className="ml-1" style={{ color: crypto.change.startsWith('+') ? '#00D964' : crypto.change.startsWith('-') ? '#FF3737' : '#A0A0A0' }}>({crypto.change})</span>
                    {index < cryptoData.length - 1 && <span className="mx-3" style={{ color: '#4a5568' }}>•</span>}
                  </span>
                ))}
              </div>
            </div>
          </div>
          
          {/* Bitcoin Price Container - In the middle, exact same height as crypto feed */}
          <div className="bitcoin-ticker border-b border-gray-700 flex-shrink-0" style={{ backgroundColor: '#0F0F0F', height: '40px' }}>
            <div ref={btcRowRef} className="flex items-center h-full text-sm w-full" style={{ padding: '0 16px' }}>
              {/* Asset Name and Price */}
              <div ref={btcLeftRef} className="flex items-center space-x-2 whitespace-nowrap shrink-0">
                <span className="font-semibold text-white">Bitcoin (BTC)</span>
                <span
                  className="text-white font-normal px-1 rounded"
                  style={{ backgroundColor: btcFlash === 'green' ? '#00D96420' : btcFlash === 'red' ? '#FF373720' : 'transparent', transition: 'background-color 200ms ease' }}
                >
                  {formatDollars(bitcoinData.price)}
                </span>
              </div>
              
              {/* Time-based Changes */}
              <div ref={btcTimeRef} className="ticker-timeframes flex items-center ml-auto">
                <div className="flex items-center gap-1">
                  <span className="text-gray-400">1h</span>
                  <span className="min-w-[56px] text-right tabular-nums" style={{ color: getChangeHex(bitcoinData.change1h) }}>{bitcoinData.change1h}</span>
                </div>
                <span className="mx-2 text-gray-500">•</span>
                <div className="flex items-center gap-1">
                  <span className="text-gray-400">24h</span>
                  <span className="min-w-[56px] text-right tabular-nums" style={{ color: getChangeHex(bitcoinData.change24h) }}>{bitcoinData.change24h}</span>
                </div>
                <span className="mx-2 text-gray-500">•</span>
                <div className="flex items-center gap-1">
                  <span className="text-gray-400">7d</span>
                  <span className="min-w-[56px] text-right tabular-nums" style={{ color: getChangeHex(bitcoinData.change7d) }}>{bitcoinData.change7d}</span>
                </div>
                <span className="mx-2 text-gray-500">•</span>
                <div className="flex items-center gap-1">
                  <span className="text-gray-400 ticker-30d">30d</span>
                  <span className="min-w-[62px] text-right tabular-nums ticker-30d" style={{ color: getChangeHex(bitcoinData.change30d) }}>{bitcoinData.change30d}</span>
                </div>
              </div>

              {/* Last update timestamp */}
              <div className="ml-4 text-xs text-gray-500 shrink-0 hidden lg:block">
                {lastUpdateTs ? `Updated ${lastUpdateTs.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit', second: '2-digit' })}` : ''}
              </div>

            </div>
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
