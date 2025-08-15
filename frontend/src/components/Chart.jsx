import React, { useEffect, useRef, useState } from 'react';

const Chart = ({ symbol = "BTCUSD", interval = "5" }) => {
  const chartContainerRef = useRef(null);
  const [bitcoinData, setBitcoinData] = useState({
    price: '$118,413.39',
    change1h: '+1.23%',
    change12h: '+2.45%',
    change24h: '+3.67%',
    change7d: '+8.90%',
    change30d: '+15.67%',
    volume24h: '$45.2B'
  });

  // Cryptocurrency ticker data (top 50 by market cap)
  const cryptoData = [
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
  ];

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
        volume24h: `$${(40 + Math.random() * 20).toFixed(1)}B`
      }));
    }, 2000); // Update every 2 seconds

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Load TradingView widget script
    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
    script.async = true;
    script.innerHTML = JSON.stringify({
      "autosize": true,
      "symbol": "BINANCE:BTCUSD",
      "interval": interval,
      "timezone": "Etc/UTC",
      "theme": "dark",
      "style": "1",
      "locale": "en",
      "enable_publishing": false,
      "hide_top_toolbar": false,
      "hide_legend": false,
      "save_image": false,
      "backgroundColor": "#121212",
      "gridColor": "rgba(240, 243, 250, 0.07)",
      "width": "100%",
      "height": "100%",
      "support_host": "https://www.tradingview.com"
    });

    const container = chartContainerRef.current;
    if (container) {
      container.innerHTML = '';
      const widgetContainer = document.createElement('div');
      widgetContainer.className = 'tradingview-widget-container';
      container.appendChild(widgetContainer);
      widgetContainer.appendChild(script);
    }

    return () => {
      if (container) {
        container.innerHTML = '';
      }
    };
  }, [symbol, interval]);

  const getChangeColor = (change) => {
    if (change.startsWith('+')) return 'text-green-400';
    if (change.startsWith('-')) return 'text-red-400';
    return 'text-gray-400';
  };

  return (
    <div className="h-full w-full flex flex-col">
      {/* Tick-by-tick Cryptocurrency Container - Now Above Bitcoin Price */}
      <div className="content-wide border-b border-gray-700 flex-shrink-0" style={{ backgroundColor: '#0F0F0F' }}>
        <div className="flex space-x-8 animate-ticker text-sm truncate-line">
          {cryptoData.map((crypto, index) => (
            <div key={index} className="flex items-center space-x-2 text-green-400 text-sm whitespace-nowrap">
              <span className="font-bold">{crypto.symbol}</span>
              <span className="text-gray-300">{crypto.price}</span>
              <span className={crypto.change.startsWith('+') ? 'text-green-400' : 'text-red-400'}>
                {crypto.change}
              </span>
            </div>
          ))}
        </div>
      </div>
      
      {/* Bitcoin Price Container - Now Below Crypto Container, Inline with Same Height */}
      <div className="content-wide border-b border-gray-700 flex-shrink-0" style={{ backgroundColor: '#121212' }}>
        <div className="flex items-stretch space-x-4 h-20">
          {/* Asset Name and Price */}
          <div className="flex-1 rounded-lg p-3 flex flex-col justify-center" style={{ backgroundColor: '#121212' }}>
            <div className="text-lg font-bold text-orange-400">Bitcoin (BTC)</div>
            <div className="text-2xl font-bold text-white">{bitcoinData.price}</div>
          </div>
          
          {/* Time-based Changes */}
          <div className="flex-1 rounded-lg p-3 flex flex-col justify-center" style={{ backgroundColor: '#121212' }}>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">1h:</span>
                <span className={getChangeColor(bitcoinData.change1h)}>{bitcoinData.change1h}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">12h:</span>
                <span className={getChangeColor(bitcoinData.change12h)}>{bitcoinData.change12h}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">24h:</span>
                <span className={getChangeColor(bitcoinData.change24h)}>{bitcoinData.change24h}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">7d:</span>
                <span className={getChangeColor(bitcoinData.change7d)}>{bitcoinData.change7d}</span>
              </div>
            </div>
          </div>
          
          {/* 30d Change and Volume */}
          <div className="flex-1 rounded-lg p-3 flex flex-col justify-center" style={{ backgroundColor: '#121212' }}>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-400">30d:</span>
                <span className={getChangeColor(bitcoinData.change30d)}>{bitcoinData.change30d}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Volume:</span>
                <span className="text-blue-400">{bitcoinData.volume24h}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* TradingView Chart */}
      <div className="flex-1 min-h-0">
        <div 
          ref={chartContainerRef}
          className="tradingview-widget-container h-full w-full content-wide"
        >
          <div className="tradingview-widget-container__widget h-full w-full"></div>
        </div>
      </div>
    </div>
  );
};

export default Chart;
