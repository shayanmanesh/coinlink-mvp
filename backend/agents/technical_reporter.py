from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


@dataclass
class TechnicalSnapshot:
    timestamp: datetime
    price: Optional[float]
    rsi: Optional[float]
    change_1m_pct: Optional[float]
    support: Optional[float]
    resistance: Optional[float]


class TechnicalAnalystReporter:
    """Generates concise, deterministic BTC technical reports.
    No external model dependencies; safe for production.
    """

    def build_report(self, snap: TechnicalSnapshot) -> str:
        ts = snap.timestamp.strftime('%-I:%M %p') if hasattr(snap.timestamp, 'strftime') else snap.timestamp.isoformat()
        p = f"${snap.price:,.0f}" if isinstance(snap.price, (int, float)) else "—"
        rsi = snap.rsi
        rsi_str = f"{rsi:.1f}" if isinstance(rsi, (int, float)) else "—"
        ch1 = snap.change_1m_pct
        ch1_str = f"{ch1:+.2f}%" if isinstance(ch1, (int, float)) else "—"
        sup = f"${snap.support:,.0f}" if isinstance(snap.support, (int, float)) else "—"
        res = f"${snap.resistance:,.0f}" if isinstance(snap.resistance, (int, float)) else "—"

        bias = "neutral"
        try:
            if rsi is not None and snap.price is not None and snap.support is not None and snap.resistance is not None:
                mid = (snap.support + snap.resistance) / 2.0
                if rsi >= 60 and snap.price >= mid:
                    bias = "bullish"
                elif rsi <= 40 and snap.price <= mid:
                    bias = "bearish"
        except Exception:
            pass

        lines = [
            f"BTC Technical Report ({ts})",
            f"Price {p} | 1m {ch1_str} | RSI(14) {rsi_str}",
            f"Support ~ {sup} | Resistance ~ {res}",
            f"Bias: {bias}. Watch for break/retest of S/R; align entries with RSI and momentum.",
        ]
        return "\n".join(lines)


