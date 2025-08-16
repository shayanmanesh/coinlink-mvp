import React, { useEffect, useState, useMemo } from 'react';
import { promptFeed$ } from '../services/realtime';
import { getEngagementLevel, onEngagementChange } from '../services/engagement';

const levelToCount = {
  low: 4,
  medium: 8,
  high: 12,
};

const kindToStyle = (kind) => {
  switch (kind) {
    case 'alert':
      return { borderColor: '#EF4444', bg: '#1b1111' };
    case 'report':
      return { borderColor: '#3B82F6', bg: '#11151b' };
    case 'insight':
    default:
      return { borderColor: '#F59E0B', bg: '#1b170f' };
  }
};

const PromptFeed = ({ onPromptClick }) => {
  const [feed, setFeed] = useState([]);
  const [engagementLevel, setEngagementLevel] = useState(getEngagementLevel());

  useEffect(() => {
    const sub = promptFeed$.subscribe((items) => {
      if (Array.isArray(items)) setFeed(items);
    });
    const off = onEngagementChange((lvl) => setEngagementLevel(lvl));
    return () => { sub.unsubscribe(); off && off(); };
  }, []);

  const displayCount = useMemo(() => levelToCount[engagementLevel] || 6, [engagementLevel]);
  const items = useMemo(() => feed.slice(0, displayCount), [feed, displayCount]);

  if (!items.length) return null;

  return (
    <div className="px-3 py-2 border-b border-gray-700" style={{ backgroundColor: '#0F0F0F' }}>
      <div className="max-w-3xl mx-auto">
        <div className="flex items-stretch gap-2 overflow-hidden">
          {items.map((it, idx) => {
            const st = kindToStyle(it.kind);
            const title = it.title || 'Update';
            const text = it.content || '';
            const ts = it.timestamp ? new Date(it.timestamp).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }) : '';
            const isMarketReport = it.kind === 'report' && it.subtype === 'market';
            return (
              <button
                key={idx}
                onClick={() => onPromptClick && onPromptClick(text || title)}
                className="shrink-0 px-3 py-2 rounded-md text-xs text-left border"
                style={{ 
                  borderColor: st.borderColor, 
                  backgroundColor: st.bg, 
                  color: '#e5e7eb',
                  maxWidth: isMarketReport ? 560 : 220,
                  whiteSpace: isMarketReport ? 'pre-line' : 'normal'
                }}
                title={title}
              >
                <div className="font-semibold mb-0.5" style={{ color: '#fff' }}>{title}</div>
                {text && (
                  isMarketReport
                    ? <div className="opacity-90 text-[11px] leading-4">{text}</div>
                    : <div className="opacity-80 line-clamp-2" style={{ maxWidth: 220 }}>{text}</div>
                )}
                {ts && <div className="mt-1 text-[10px] opacity-60">{ts}</div>}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default PromptFeed;


