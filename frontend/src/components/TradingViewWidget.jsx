import React, { useEffect, useMemo, useRef } from 'react';

const TradingViewWidget = () => {
  const containerRef = useRef(null);

  // Build config via useMemo so any change re-initializes the widget
  const config = useMemo(() => ({
    allow_symbol_change: false,
    calendar: false,
    details: false,
    hide_side_toolbar: true,
    hide_top_toolbar: true,
    hide_legend: true,
    hide_volume: false,
    hotlist: false,
    interval: '60',
    locale: 'en',
    save_image: false,
    style: '1',
    symbol: 'COINBASE:BTCUSD',
    theme: 'dark',
    timezone: 'exchange',
    backgroundColor: '#0F0F0F',
    gridColor: 'rgba(0, 0, 0, 0)',
    watchlist: [],
    withdateranges: true,
    compareSymbols: [],
    studies: [
      {
        id: 'RSI',
        inputs: { length: 14 },
      }
    ],
    autosize: true,
  }), []);
  const configString = useMemo(() => JSON.stringify(config), [config]);

  useEffect(() => {
    // Create the script element
    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
    script.async = true;
    script.type = 'text/javascript';
    script.crossOrigin = 'anonymous';
    script.onerror = (e) => {
      try { console.error('TradingView script failed to load'); } catch {}
      // Prevent bubbling generic error overlays from third-party script
      try { if (e && e.preventDefault) e.preventDefault(); } catch {}
    };
    
    // Ensure container exists before loading widget
    const container = containerRef.current;
    if (!container) {
      return () => {};
    }
    // Set the widget configuration
    script.innerHTML = configString;

    // Clear container and append script
    if (container) {
      container.innerHTML = '';
      try {
        // Guard against missing inner widget div
        const target = container.querySelector('.tradingview-widget-container__widget') || container;
        target.appendChild(script);
      } catch (_) {
        // Ignore DOM exceptions from double-mounts
      }
    }

    // Cleanup function
    return () => {
      try {
        if (containerRef.current) {
          containerRef.current.innerHTML = '';
        }
      } catch (e) {}
    };
  }, [configString]);

  return (
    <div className="tradingview-widget-container" style={{height: '100%', width: '100%', backgroundColor: '#0F0F0F'}}>
      <div className="tradingview-widget-container__widget" style={{height: '100%', width: '100%', backgroundColor: '#0F0F0F'}} ref={containerRef}></div>
    </div>
  );
};

export default TradingViewWidget;

