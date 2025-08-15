let score = 0;
let listeners = new Set();

const thresholds = { low: 0, medium: 5, high: 12 };

export const bumpEngagement = (delta = 1) => {
  score = Math.max(0, score + delta);
  const level = getEngagementLevel();
  listeners.forEach((cb) => { try { cb(level); } catch {} });
};

export const decayEngagement = () => {
  score = Math.max(0, score - 1);
  const level = getEngagementLevel();
  listeners.forEach((cb) => { try { cb(level); } catch {} });
};

export const getEngagementLevel = () => {
  if (score >= thresholds.high) return 'high';
  if (score >= thresholds.medium) return 'medium';
  return 'low';
};

export const onEngagementChange = (cb) => {
  listeners.add(cb);
  return () => listeners.delete(cb);
};

// Auto-decay every 30s
setInterval(decayEngagement, 30000);


