import asyncio
from collections import deque, defaultdict
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Deque, Dict, Optional, Tuple, List, Any
import uuid
import math
import numpy as np

from api.websocket import manager, websocket_handler
from sentiment.analyzer import BitcoinSentimentService
from tools.coinbase_tools import get_bitcoin_price, get_bitcoin_candles
from config.settings import settings


@dataclass
class Tick:
    ts: datetime
    price: float
    volume24h: float


class RealTimeMetrics:
    def __init__(self, window_minutes: int = 60):
        self.ticks: Deque[Tick] = deque(maxlen=window_minutes * 120)  # assume up to 2 ticks/sec
        self.prev_rsi: Optional[float] = None
        self.last_volume24h: Optional[float] = None

    def add_tick(self, price: float, volume24h: float, ts: Optional[datetime] = None) -> Dict[str, float]:
        now = ts or datetime.utcnow()
        self.ticks.append(Tick(ts=now, price=price, volume24h=volume24h))
        return self.compute(now)

    def _compute_rsi(self, closes: List[float], period: int = 14) -> float:
        if len(closes) < period + 1:
            return 50.0
        gains: List[float] = []
        losses: List[float] = []
        for i in range(1, period + 1):
            delta = closes[-i] - closes[-(i + 1)]
            if delta > 0:
                gains.append(delta)
                losses.append(0.0)
            else:
                gains.append(0.0)
                losses.append(-delta)
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period if sum(losses) > 0 else 0.0
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return max(0.0, min(100.0, rsi))

    def compute(self, now: Optional[datetime] = None) -> Dict[str, float]:
        if not self.ticks:
            return {}
        now = now or datetime.utcnow()
        prices = [t.price for t in self.ticks]
        rsi = self._compute_rsi(prices, 14)
        # Expose latest RSI on the instance for quick access
        self.prev_rsi = rsi
        # 1-min change
        one_min_ago = now - timedelta(seconds=60)
        older = [t for t in self.ticks if t.ts <= one_min_ago]
        if older:
            base = older[-1].price
            change_1m = (prices[-1] - base) / base * 100 if base else 0.0
        else:
            # Fallback for short test sequences: compare to previous tick
            if len(self.ticks) >= 2:
                prev_price = self.ticks[-2].price
                base = prev_price
                change_1m = (prices[-1] - base) / base * 100 if base else 0.0
            else:
                change_1m = 0.0
        # Support/Resistance from last ~48 minutes
        recent = [t.price for t in self.ticks if t.ts >= now - timedelta(minutes=48)] or prices
        support = min(recent)
        resistance = max(recent)
        # Volume spike (approx using 24h volume deltas)
        # Compute last 1-min volume and 5-min avg
        vols: List[Tuple[datetime, float]] = [(t.ts, t.volume24h) for t in self.ticks if t.volume24h]
        vol_1m = 0.0
        vol_5m_avg = 0.0
        if len(vols) >= 2:
            v_now = vols[-1]
            v_1m = next((v for v in reversed(vols) if v[0] <= now - timedelta(minutes=1)), vols[0])
            vol_1m = max(0.0, v_now[1] - v_1m[1])
            buckets = []
            for i in range(1, 6):
                t_edge = now - timedelta(minutes=i)
                v_edge = next((v for v in reversed(vols) if v[0] <= t_edge), vols[0])
                v_prev_edge = next((v for v in reversed(vols) if v[0] <= t_edge - timedelta(minutes=1)), vols[0])
                buckets.append(max(0.0, v_edge[1] - v_prev_edge[1]))
            if buckets:
                vol_5m_avg = sum(buckets) / len(buckets)

        return {
            'rsi': rsi,
            'change_1m_pct': change_1m,
            'support': support,
            'resistance': resistance,
            'vol_1m': vol_1m,
            'vol_5m_avg': vol_5m_avg,
        }


class RealTimeAlertEngine:
    def __init__(self):
        self.metrics = RealTimeMetrics()
        self.sentiment_service = BitcoinSentimentService()
        self.last_sentiment: Optional[str] = None
        self.last_sentiment_conf: float = 0.0
        # Rolling series for correlation (30 minutes by default)
        self.sentiment_points: Deque[Tuple[datetime, float]] = deque(maxlen=240)  # ~4 points/min if needed
        self.corr_window_minutes: int = 30
        self.last_corr: Optional[float] = None
        self.logger = logging.getLogger("coinlink.alerts")
        # Cooldowns to prevent alert spam
        self.last_alert_times: Dict[str, float] = {
            'volume_spike': 0.0,
            'rsi_cross': 0.0,
            'price_move': 0.0,
            'resistance_breach': 0.0,
            'support_breach': 0.0,
            'correlation_break': 0.0,
            'sentiment_leading': 0.0,
        }
        self.alert_cooldown: float = float(getattr(settings, 'ALERT_COOLDOWN_SECONDS', 300.0))
        # Simple duplicate content suppression window
        self._last_agent_message_text: Optional[str] = None
        self._last_agent_message_ts: float = 0.0
        # Signature-based dedup by alert content (ignores timestamps)
        self._recent_alert_signatures: Dict[str, float] = {}
        # Prompt feed buffer (rolling)
        self._prompt_feed: Deque[Dict] = deque(maxlen=50)
        # Streaming market report state
        self._market_report_id: Optional[str] = None
        self._market_report_created_at: Optional[datetime] = None
        self._hist_returns_cache: Dict[str, Any] = {
            'last_fetch': 0.0,
            'data': {'d5': None, 'w1': None, 'm1': None}
        }

    async def push_prompt_card(self, card: Dict) -> None:
        """Append a prompt card to the feed and broadcast, with lightweight dedup."""
        try:
            # Simple dedup by title+content signature within the current buffer
            sig = f"{card.get('title','')}|{card.get('content','')}|{card.get('kind','')}"
            for c in list(self._prompt_feed)[:10]:
                csig = f"{c.get('title','')}|{c.get('content','')}|{c.get('kind','')}"
                if csig == sig:
                    return
            self._prompt_feed.appendleft(card)
            await manager.broadcast({'type': 'prompt_feed', 'data': list(self._prompt_feed)})
        except Exception:
            pass

    # --- Streaming Market Report ---
    def _format_triangle(self, pct: Optional[float]) -> str:
        try:
            if pct is None:
                return "0.00%"
            arrow = '▲' if pct >= 0 else '▼'
            return f"{arrow}{abs(pct):.2f}%"
        except Exception:
            return "0.00%"

    def _find_tick_at_or_before(self, target: datetime) -> Optional[Tick]:
        try:
            for t in reversed(self.metrics.ticks):
                if t.ts <= target:
                    return t
            return self.metrics.ticks[0] if self.metrics.ticks else None
        except Exception:
            return None

    def _compute_price_change_pct(self, minutes: int, now: Optional[datetime] = None) -> Optional[float]:
        if not self.metrics.ticks:
            return None
        now_dt = now or datetime.utcnow()
        base_tick = self._find_tick_at_or_before(now_dt - timedelta(minutes=minutes))
        if not base_tick:
            return None
        last_price = self.metrics.ticks[-1].price
        if not base_tick.price:
            return 0.0
        return ((last_price - base_tick.price) / base_tick.price) * 100.0

    def _compute_volume_in_window(self, minutes: int, now: Optional[datetime] = None) -> Optional[float]:
        if not self.metrics.ticks:
            return None
        now_dt = now or datetime.utcnow()
        end_tick = self._find_tick_at_or_before(now_dt)
        start_tick = self._find_tick_at_or_before(now_dt - timedelta(minutes=minutes))
        if not end_tick or not start_tick:
            return None
        try:
            vol = max(0.0, (end_tick.volume24h or 0.0) - (start_tick.volume24h or 0.0))
            return vol
        except Exception:
            return None

    def _compute_prev_window_volume(self, minutes: int, now: Optional[datetime] = None) -> Optional[float]:
        now_dt = now or datetime.utcnow()
        start_prev = now_dt - timedelta(minutes=minutes * 2)
        end_prev = now_dt - timedelta(minutes=minutes)
        end_prev_tick = self._find_tick_at_or_before(end_prev)
        start_prev_tick = self._find_tick_at_or_before(start_prev)
        if not end_prev_tick or not start_prev_tick:
            return None
        try:
            return max(0.0, (end_prev_tick.volume24h or 0.0) - (start_prev_tick.volume24h or 0.0))
        except Exception:
            return None

    def _compute_historical_returns(self, current_price: float) -> Dict[str, Optional[float]]:
        # Cached for 5 minutes to avoid rate limits
        try:
            now_ts = time.time()
            cache_age = now_ts - float(self._hist_returns_cache.get('last_fetch', 0.0))
            if cache_age < 300 and self._hist_returns_cache.get('data'):
                return dict(self._hist_returns_cache['data'])
            data = get_bitcoin_candles("BTC-USD", granularity=86400, limit=60)
            vals = {'d5': None, 'w1': None, 'm1': None}
            if data and not data.get('error'):
                candles = data.get('candles', [])
                closes = [c.get('close') for c in candles]
                if closes:
                    # Use current price vs historical closes at offsets
                    def pct_vs_offset(days: int) -> Optional[float]:
                        try:
                            if len(closes) > days:
                                base = float(closes[-(days + 1)])
                                if base:
                                    return ((current_price - base) / base) * 100.0
                        except Exception:
                            return None
                        return None
                    vals['d5'] = pct_vs_offset(5)
                    vals['w1'] = pct_vs_offset(7)
                    vals['m1'] = pct_vs_offset(30)
            self._hist_returns_cache = {'last_fetch': now_ts, 'data': vals}
            return vals
        except Exception:
            return {'d5': None, 'w1': None, 'm1': None}

    def _format_age(self, created_at: Optional[datetime]) -> str:
        if not created_at:
            return ""
        delta = datetime.utcnow() - created_at
        total_s = int(delta.total_seconds())
        m, s = divmod(total_s, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h}h {m}m {s}s"
        if m > 0:
            return f"{m}m {s}s"
        return f"{s}s"

    def _build_market_report_snapshot(self) -> Optional[Dict[str, Any]]:
        if not self.metrics.ticks:
            return None
        now = datetime.utcnow()
        last_tick = self.metrics.ticks[-1]
        price = float(last_tick.price)
        comp = self.metrics.compute(now)
        # Price changes
        chg_10m = self._compute_price_change_pct(10, now) or 0.0
        chg_30m = self._compute_price_change_pct(30, now) or 0.0
        chg_1h = self._compute_price_change_pct(60, now) or 0.0
        # Volumes
        vol_10m = self._compute_volume_in_window(10, now) or 0.0
        vol_30m = self._compute_volume_in_window(30, now) or 0.0
        vol_1h = self._compute_volume_in_window(60, now) or 0.0
        # Volume change vs previous window
        prev_vol_10m = self._compute_prev_window_volume(10, now) or 0.0
        vol_10m_change_pct = ((vol_10m / prev_vol_10m) - 1.0) * 100.0 if prev_vol_10m > 0 else 0.0
        # Historical returns
        hist = self._compute_historical_returns(price)
        rsi_val = comp.get('rsi') if comp else None
        support = comp.get('support') if comp else None
        resistance = comp.get('resistance') if comp else None
        # Title with dynamic age
        age = self._format_age(self._market_report_created_at)
        title = f"Bitcoin (BTC) ${price:,.2f} {self._format_triangle(chg_10m)} {age}"
        # Body content
        lines: List[str] = []
        lines.append(
            (
                f"Bitcoin (BTC) now selling at ${price:,.2f} {self._format_triangle(chg_10m)} "
                f"with ${vol_10m:,.2f} {self._format_triangle(vol_10m_change_pct)} volume traded in the last 10 minutes, "
                f"{self._format_triangle(hist.get('d5'))}5D {self._format_triangle(hist.get('w1'))}1W {self._format_triangle(hist.get('m1'))}M"
            )
        )
        lines.append("")
        lines.append("Bitcoin (BTC) Price & Volume Performance")
        lines.append(
            f"Bitcoin Price ${price:,.2f} ({self._format_triangle(chg_10m)} 10MIN) • "
            f"{self._format_triangle(chg_30m)} 30MIN • {self._format_triangle(chg_1h)} 1H"
        )
        lines.append(
            f"Bitcoin Volume ${vol_10m:,.2f} (10MIN) • ${vol_30m:,.2f} (30MIN) • ${vol_1h:,.2f} (1H)"
        )
        # Technical analysis concise line
        ta_bits: List[str] = []
        if isinstance(rsi_val, (int, float)):
            ta_bits.append(f"RSI(14): {rsi_val:.1f}")
            if rsi_val >= 70:
                ta_bits.append("overbought")
            elif rsi_val <= 30:
                ta_bits.append("oversold")
        if isinstance(support, (int, float)) and isinstance(resistance, (int, float)):
            ta_bits.append(f"S/R: {support:,.0f}/{resistance:,.0f}")
        ta_bits.append("momentum: " + ("positive" if chg_10m >= 0 else "negative"))
        lines.append("")
        lines.append("Technical Analysis:")
        lines.append(" ")
        lines.append(" ".join(ta_bits))

        content = "\n".join(lines)
        snapshot = {
            'report_id': self._market_report_id,
            'created_at': self._market_report_created_at.isoformat() if self._market_report_created_at else None,
            'title': title,
            'content': content,
            'price': price,
            'chg_10m_pct': chg_10m,
            'vol_10m': vol_10m,
            'timestamp': datetime.utcnow().isoformat(),
        }
        return snapshot

    async def _upsert_report_card(self, snapshot: Dict[str, Any]):
        try:
            updated_card = {
                'kind': 'report',
                'subtype': 'market',
                'report_id': snapshot.get('report_id'),
                'title': snapshot.get('title'),
                'content': snapshot.get('content'),
                'timestamp': snapshot.get('timestamp'),
                'priority': 'high'
            }
            # Replace existing market report card or insert at front
            existing_idx = None
            buf_list = list(self._prompt_feed)
            for i, c in enumerate(buf_list):
                if c.get('kind') == 'report' and c.get('subtype') == 'market' and c.get('report_id') == self._market_report_id:
                    existing_idx = i
                    break
            if existing_idx is not None:
                buf_list[existing_idx] = updated_card
                self._prompt_feed = deque(buf_list, maxlen=self._prompt_feed.maxlen)
            else:
                self._prompt_feed.appendleft(updated_card)
            await manager.broadcast({'type': 'prompt_feed', 'data': list(self._prompt_feed)})
        except Exception:
            pass

    async def start_market_report_stream(self):
        """Continuously emit an updating market report card every ~2 seconds."""
        # Initialize report session
        if not self._market_report_id:
            self._market_report_id = str(uuid.uuid4())
            self._market_report_created_at = datetime.utcnow()
        while True:
            try:
                snap = self._build_market_report_snapshot()
                if snap:
                    await self._upsert_report_card(snap)
            except Exception:
                pass
            await asyncio.sleep(2)

    def _should_send_alert(self, alert_type: str) -> bool:
        now = time.time()
        last = self.last_alert_times.get(alert_type, 0.0)
        if (now - last) < self.alert_cooldown:
            try:
                self.logger.info("Suppressed alert '%s' due to cooldown (%.1fs left)", alert_type, self.alert_cooldown - (now - last))
            except Exception:
                pass
            return False
        self.last_alert_times[alert_type] = now
        return True

    async def handle_tick(self, price: float, volume24h: float, ts: Optional[datetime] = None):
        computed = self.metrics.add_tick(price, volume24h, ts)
        if not computed:
            return
        rsi = computed['rsi']
        change_1m_pct = computed['change_1m_pct']
        support = computed['support']
        resistance = computed['resistance']
        vol_1m = computed['vol_1m']
        vol_5m_avg = computed['vol_5m_avg']
        # Debug log for alert evaluation
        try:
            print(f"[Tick] ts={ (ts or datetime.utcnow()).isoformat() } price={price} change_1m_pct={change_1m_pct:.4f} rsi={rsi:.2f} support={support:.2f} resistance={resistance:.2f}")
        except Exception:
            pass

        # Broadcast price update
        await manager.broadcast({
            'type': 'price_update',
            'data': {
                'price': price,
                'timestamp': (ts or datetime.utcnow()).isoformat(),
                'rsi': rsi,
                'volume': vol_1m,
            },
            'priority': 'normal'
        })

        # Triggers
        # 1) Price move: volatility-aware threshold using rolling 1m return sigma
        # Estimate sigma from last 30 minutes of 1m returns
        returns_window: List[float] = []
        try:
            # Build per-minute returns retrospectively from ticks
            times, price_returns, _ = self._build_minute_series()
            if price_returns:
                # Recent 30 values or all if fewer
                sample = price_returns[-30:] if len(price_returns) >= 30 else price_returns
                mu = float(np.mean(sample)) if sample else 0.0
                sigma = float(np.std(sample)) if sample else 0.0
            else:
                mu = 0.0
                sigma = 0.0
        except Exception:
            mu = 0.0
            sigma = 0.0
        k = getattr(settings, 'PRICE_SIGMA_K', 2.5)
        dynamic_threshold = (abs(mu) + k * max(sigma, 0.1))  # guard against tiny sigma
        if abs(change_1m_pct) > max(2.0, dynamic_threshold):
            try:
                print(f"[AlertCheck] TRIGGER price move: {change_1m_pct:.2f}% (>max(2%, {dynamic_threshold:.2f}%))")
            except Exception:
                pass
            if self._should_send_alert('price_move'):
                await self._alert('Significant price move', {
                    'price': price, 'change_1m_pct': change_1m_pct
                })

        # 2) RSI crosses 70/30
        crossed = False
        prev = self.metrics.prev_rsi
        if prev is not None:
            if prev <= 70 < rsi or prev >= 30 > rsi:
                crossed = True
        self.metrics.prev_rsi = rsi
        if crossed:
            try:
                print(f"[AlertCheck] TRIGGER RSI cross: prev={prev:.2f} now={rsi:.2f}")
            except Exception:
                pass
            if self._should_send_alert('rsi_cross'):
                await self._alert('RSI threshold crossed', {'rsi': rsi})

        # 3) Support/resistance breach with hysteresis
        res_hyst = 1.0 + float(getattr(settings, 'RESISTANCE_HYSTERESIS_PCT', 0.005))
        sup_hyst = 1.0 - float(getattr(settings, 'SUPPORT_HYSTERESIS_PCT', 0.005))
        if resistance and price > resistance * res_hyst:
            try:
                print(f"[AlertCheck] TRIGGER Resistance breach: price={price:.2f} res={resistance:.2f}")
            except Exception:
                pass
            if self._should_send_alert('resistance_breach'):
                await self._alert('Resistance breach', {'price': price, 'resistance': resistance})
                # Removed: resistance-breach engagement prompt
        if support and price < support * sup_hyst:
            try:
                print(f"[AlertCheck] TRIGGER Support breach: price={price:.2f} sup={support:.2f}")
            except Exception:
                pass
            if self._should_send_alert('support_breach'):
                await self._alert('Support breach', {'price': price, 'support': support})

        # 4) Volume spike > N x 5-minute average
        vol_mult = float(getattr(settings, 'VOL_SPIKE_MULTIPLIER', 3.0))
        if vol_5m_avg and vol_1m > vol_mult * vol_5m_avg:
            try:
                print(f"[AlertCheck] TRIGGER Volume spike: vol_1m={vol_1m:.4f} avg5m={vol_5m_avg:.4f}")
            except Exception:
                pass
            if self._should_send_alert('volume_spike'):
                await self._alert('Volume spike', {'vol_1m': vol_1m, 'vol_5m_avg': vol_5m_avg})

    async def _alert(self, title: str, payload: Dict):
        # Log alert payload before broadcasting (chat only to avoid duplicates)
        try:
            self.logger.info("Broadcasting alert payload: title=%s payload=%s", title, payload)
        except Exception:
            pass
        # Push as agent-initiated chat inline (single channel for UI)
        try:
            price = payload.get('price') or ''
            ts = datetime.utcnow().strftime('%-I:%M %p') if hasattr(datetime.now(), 'strftime') else datetime.utcnow().isoformat()
            if title.lower().startswith('significant price move'):
                change = payload.get('change_1m_pct')
                severity = '🚨' if abs(change or 0) >= 5 else '📈' if (change or 0) > 0 else '📉'
                content = f"{severity} **ALERT**: Bitcoin {'surged' if (change or 0) > 0 else 'dropped'} {abs(change or 0):.1f}% in 1 minute - Price: ${price:,.0f} ({ts})"
            elif title.lower().startswith('rsi'):
                rsi = payload.get('rsi')
                content = f"⚠️ RSI crossed threshold ({rsi:.1f}) ({ts})"
            elif title.lower().startswith('resistance breach'):
                content = f"⚠️ Resistance breach - Price: ${price:,.0f} ({ts})"
            elif title.lower().startswith('support breach'):
                content = f"⚠️ Support breach - Price: ${price:,.0f} ({ts})"
            elif title.lower().startswith('volume spike'):
                content = f"⚠️ Volume spike detected ({ts})"
            elif title.lower().startswith('correlation break'):
                corr = payload.get('corr_30m')
                content = f"ℹ️ Correlation break: 30m |corr| < 0.3 (now {corr}) ({ts})"
            elif title.lower().startswith('sentiment leading price'):
                lag = payload.get('lead_minutes')
                corr = payload.get('corr')
                content = f"🧭 Sentiment leading price by ~{lag}m (corr={corr}) ({ts})"
            else:
                content = f"ℹ️ {title} ({ts})"
            # Deduplicate identical alerts within configured window (timestamp-agnostic)
            now_ts = time.time()
            # Build signature from title and rounded payload values
            try:
                sig_parts: List[str] = [title.lower()]
                for k in sorted(payload.keys()):
                    v = payload.get(k)
                    if isinstance(v, (int, float)):
                        sig_parts.append(f"{k}:{round(float(v), 2)}")
                    else:
                        if k in ("timestamp",):
                            continue
                        sig_parts.append(f"{k}:{str(v)}")
                signature = "|".join(sig_parts)
            except Exception:
                signature = title.lower()
            window_s = float(getattr(settings, 'ALERT_DEDUP_WINDOW_SECONDS', 120))
            last_sig_ts = self._recent_alert_signatures.get(signature, 0.0)
            if (now_ts - last_sig_ts) < window_s:
                try:
                    self.logger.info("Suppressed duplicate alert signature within window: %s", signature)
                except Exception:
                    pass
                return
            self._last_agent_message_text = content
            self._last_agent_message_ts = now_ts
            self._recent_alert_signatures[signature] = now_ts
            try:
                self.logger.info("Broadcasting agent chat: %s", content)
            except Exception:
                pass
            await websocket_handler.send_agent_message(content)
            # Also push into intelligent prompt feed as a high-signal card
            try:
                card = {
                    'kind': 'alert',
                    'title': title,
                    'content': content,
                    'timestamp': datetime.utcnow().isoformat(),
                    'priority': 'high'
                }
                self._prompt_feed.appendleft(card)
                await manager.broadcast({'type': 'prompt_feed', 'data': list(self._prompt_feed)})
            except Exception:
                pass
        except Exception:
            pass

    async def poll_sentiment(self):
        """Poll sentiment every few minutes and broadcast shifts."""
        while True:
            try:
                summary = await self.sentiment_service.get_bitcoin_sentiment_summary()
                sentiment = summary.get('overall_sentiment', 'neutral')
                conf = summary.get('average_score', 0)
                # Track signed sentiment for correlation: positive=+score, negative=-score, neutral=0
                signed_score = 0.0
                if sentiment == 'positive':
                    signed_score = float(conf or 0)
                elif sentiment == 'negative':
                    signed_score = -float(conf or 0)
                else:
                    signed_score = 0.0
                self.sentiment_points.append((datetime.utcnow(), signed_score))
                if self.last_sentiment is not None and sentiment != self.last_sentiment and conf > 0.8:
                    await manager.broadcast({
                        'type': 'sentiment_shift',
                        'data': {
                            'sentiment': sentiment,
                            'confidence': conf,
                            'timestamp': datetime.utcnow().isoformat(),
                        },
                        'priority': 'high'
                    })
                self.last_sentiment = sentiment
                self.last_sentiment_conf = conf
            except Exception:
                pass
            await asyncio.sleep(180)

    def _floor_minute(self, ts: datetime) -> datetime:
        return ts.replace(second=0, microsecond=0)

    def _build_minute_series(self) -> Tuple[List[datetime], List[float], List[float]]:
        """Return aligned per-minute series for last window: times, price returns, sentiment deltas.
        - price returns: pct change minute-over-minute
        - sentiment deltas: difference minute-over-minute of signed score
        """
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=self.corr_window_minutes + 1)
        # Price per-minute last value
        minute_to_price: Dict[datetime, float] = {}
        for t in self.metrics.ticks:
            if t.ts < window_start:
                continue
            minute_key = self._floor_minute(t.ts)
            minute_to_price[minute_key] = t.price  # last wins
        if not minute_to_price:
            return [], [], []
        # Forward fill to ensure continuity
        all_minutes: List[datetime] = []
        cur = self._floor_minute(window_start)
        end = self._floor_minute(now)
        last_price: Optional[float] = None
        while cur <= end:
            if cur in minute_to_price:
                last_price = minute_to_price[cur]
            if last_price is not None:
                minute_to_price[cur] = last_price
                all_minutes.append(cur)
            cur += timedelta(minutes=1)
        # Sentiment per-minute last value
        minute_to_sent: Dict[datetime, float] = {}
        for ts, s in list(self.sentiment_points):
            if ts < window_start:
                continue
            minute_key = self._floor_minute(ts)
            minute_to_sent[minute_key] = s
        # Forward fill sentiment
        last_s: float = 0.0
        for m in all_minutes:
            if m in minute_to_sent:
                last_s = minute_to_sent[m]
            minute_to_sent[m] = last_s
        # Build aligned arrays and compute returns/deltas
        prices: List[float] = [minute_to_price[m] for m in all_minutes if m in minute_to_price]
        s_vals: List[float] = [minute_to_sent.get(m, 0.0) for m in all_minutes]
        if len(prices) < 3 or len(s_vals) < 3:
            return [], [], []
        price_returns: List[float] = []
        sent_deltas: List[float] = []
        for i in range(1, len(all_minutes)):
            p0 = prices[i - 1]
            p1 = prices[i]
            r = ((p1 - p0) / p0) * 100 if p0 else 0.0
            price_returns.append(r)
            sd = s_vals[i] - s_vals[i - 1]
            sent_deltas.append(sd)
        # align timestamps to returns (skip the first minute)
        times = all_minutes[1:]
        return times, price_returns, sent_deltas

    def _pearson(self, a: List[float], b: List[float]) -> Optional[float]:
        try:
            if len(a) != len(b) or len(a) < 5:
                return None
            av = np.array(a)
            bv = np.array(b)
            if np.all(av == av[0]) or np.all(bv == bv[0]):
                return 0.0
            c = float(np.corrcoef(av, bv)[0, 1])
            if math.isnan(c):
                return None
            return c
        except Exception:
            return None

    def _compute_rolling_correlation(self) -> Optional[float]:
        times, price_returns, sent_deltas = self._build_minute_series()
        if not times:
            return None
        return self._pearson(price_returns, sent_deltas)

    def get_correlation_snapshot(self) -> Dict[str, Optional[float]]:
        """Return current 30m correlation and best leading signal (lag and corr)."""
        corr = self._compute_rolling_correlation()
        lead = self._detect_leading()
        lead_minutes = lead[0] if lead else None
        lead_corr = lead[1] if lead else None
        return {
            'corr_30m': corr,
            'lead_minutes': lead_minutes,
            'lead_corr': lead_corr,
        }

    def get_current_rsi(self) -> Optional[float]:
        """Return the most recent RSI computed from live ticks, if available."""
        try:
            comp = self.metrics.compute()
            rsi = comp.get('rsi') if comp else None
            return float(rsi) if rsi is not None else None
        except Exception:
            return None

    def _detect_leading(self) -> Optional[Tuple[int, float]]:
        """Detect if sentiment change leads price returns by 5-30 minutes.
        Returns (lag_minutes, corr) when correlation exceeds threshold, else None.
        """
        times, price_returns, sent_deltas = self._build_minute_series()
        if not times:
            return None
        best_corr = None
        best_lag = None
        # Try lags 5..30 minutes (sentiment leads price)
        for lag in range(5, 31):
            if len(price_returns) - lag <= 5:
                break
            pr = price_returns[lag:]
            sd = sent_deltas[:-lag]
            corr = self._pearson(pr, sd)
            if corr is None:
                continue
            if (best_corr is None) or (abs(corr) > abs(best_corr)):
                best_corr = corr
                best_lag = lag
        if best_corr is not None and best_lag is not None and abs(best_corr) >= 0.5:
            return best_lag, best_corr
        return None

    async def monitor_correlation(self):
        """Periodically compute 30m correlation and detect leading indicator."""
        while True:
            try:
                corr = self._compute_rolling_correlation()
                if corr is not None:
                    # Alert on correlation break below 0.3 (from previously >= 0.3)
                    prev = self.last_corr
                    if prev is not None and abs(prev) >= 0.3 and abs(corr) < 0.3:
                        if self._should_send_alert('correlation_break'):
                            await self._alert('Correlation break (<0.3)', {
                                'corr_30m': round(corr, 3),
                            })
                    self.last_corr = corr
                # Leading indicator detection
                lead = self._detect_leading()
                if lead is not None:
                    lag_min, lcorr = lead
                    if self._should_send_alert('sentiment_leading'):
                        await self._alert('Sentiment leading price', {
                            'lead_minutes': lag_min,
                            'corr': round(lcorr, 3),
                        })
            except Exception:
                pass
            await asyncio.sleep(60)

    async def push_market_insights(self):
        """Scheduled push every 5 minutes."""
        while True:
            try:
                # Build quick snapshot from last metrics
                if self.metrics.ticks:
                    now_price = self.metrics.ticks[-1].price
                    comp = self.metrics.compute()
                    await manager.broadcast({
                        'type': 'price_update',
                        'data': {
                            'price': now_price,
                            'timestamp': datetime.utcnow().isoformat(),
                            'rsi': comp.get('rsi'),
                            'volume': comp.get('vol_1m'),
                        },
                        'priority': 'normal'
                    })
                    # Feed a concise prompt card every 5 minutes
                    try:
                        rsi = comp.get('rsi')
                        card = {
                            'kind': 'insight',
                            'title': 'Market snapshot',
                            'content': f"BTC ${now_price:,.0f} | RSI {rsi:.1f}" if isinstance(rsi, (int,float)) else f"BTC ${now_price:,.0f}",
                            'timestamp': datetime.utcnow().isoformat(),
                            'priority': 'normal'
                        }
                        await self.push_prompt_card(card)
                    except Exception:
                        pass
            except Exception:
                pass
            await asyncio.sleep(300)

    async def push_technical_reports(self):
        """Every 30 minutes, generate a concise technical report and push to prompt feed."""
        from agents.technical_reporter import TechnicalAnalystReporter, TechnicalSnapshot
        reporter = TechnicalAnalystReporter()
        while True:
            try:
                comp = self.metrics.compute()
                if self.metrics.ticks:
                    snap = TechnicalSnapshot(
                        timestamp=datetime.utcnow(),
                        price=self.metrics.ticks[-1].price,
                        rsi=comp.get('rsi'),
                        change_1m_pct=comp.get('change_1m_pct'),
                        support=comp.get('support'),
                        resistance=comp.get('resistance'),
                    )
                    report = reporter.build_report(snap)
                    card = {
                        'kind': 'report',
                        'title': '30m Technical Report',
                        'content': report,
                        'timestamp': datetime.utcnow().isoformat(),
                        'priority': 'normal'
                    }
                    self._prompt_feed.appendleft(card)
                    await manager.broadcast({'type': 'prompt_feed', 'data': list(self._prompt_feed)})
            except Exception:
                pass
            await asyncio.sleep(1800)


class MarketDataPoller:
    """Fallback polling of Coinbase ticker if WS unavailable."""
    def __init__(self, alert_engine: RealTimeAlertEngine):
        self.alert_engine = alert_engine
        self.running = False

    async def start(self):
        self.running = True
        while self.running:
            try:
                data = get_bitcoin_price("BTC-USD")
                if 'error' not in data:
                    price = float(data.get('price', 0) or 0)
                    volume24h = float(data.get('volume', 0) or 0)
                    await self.alert_engine.handle_tick(price, volume24h)
            except Exception:
                pass
            await asyncio.sleep(1)


