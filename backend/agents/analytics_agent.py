import asyncio
from datetime import datetime
from typing import Dict, List

from sentiment.analyzer import BitcoinSentimentService
from realtime.engine import RealTimeAlertEngine


class AnalyticsAgent:
    """Coordinates and disseminates analytics and market content to the prompt feed.

    - Streams Social Sentiment Update every 5 minutes (highest-ranked item)
    - Streams Social Sentiment Aggregate every 10 minutes (top 3)
    - Streams Market Report every 10 minutes from the Technical Analyst Reporter
    - Streams Market Alerts (via RealTimeAlertEngine existing hooks)
    """

    def __init__(self, rt_engine: RealTimeAlertEngine):
        self.rt_engine = rt_engine
        self.sentiment = BitcoinSentimentService()
        self._running = False

    async def _push_card(self, kind: str, title: str, content: str, priority: str = 'normal'):
        card = {
            'kind': kind,
            'title': title,
            'content': content,
            'timestamp': datetime.utcnow().isoformat(),
            'priority': priority
        }
        await self.rt_engine.push_prompt_card(card)

    def _rank_news(self, news: List[Dict]) -> List[Dict]:
        # Simple ranking: prioritize Reddit/News titles with sentiment score magnitude
        def score_item(item: Dict) -> float:
            s = item.get('sentiment', {})
            label = (s.get('label') or 'neutral').lower()
            conf = float(s.get('score') or 0)
            mag = conf if label == 'positive' else conf if label == 'negative' else conf * 0.25
            # Boost engagement proxies: Reddit or recent timestamps
            src = (item.get('source') or '').lower()
            boost = 0.3 if 'reddit' in src else 0.0
            return mag + boost
        ranked = sorted(news or [], key=score_item, reverse=True)
        return ranked

    async def stream_social_update_5m(self):
        while True:
            try:
                news = await self.sentiment.aggregator.fetch_all(limit=15)
                # Annotate with sentiment quickly
                enriched: List[Dict] = []
                for n in (news or [])[:20]:
                    t = (n.get('title') or '') + ' ' + (n.get('description') or '')
                    s = self.sentiment.analyzer.analyze_bitcoin_news(t)
                    enriched.append({ **n, 'sentiment': s or {} })
                ranked = self._rank_news(enriched)
                if ranked:
                    top = ranked[0]
                    ttl = 'Social Sentiment Update'
                    s = top.get('sentiment', {})
                    lbl = s.get('label', 'neutral')
                    conf = s.get('score', 0)
                    content = f"{top.get('title','')} — {lbl} ({conf:.2f}). {top.get('source','')}"
                    await self._push_card('sentiment_update', ttl, content, 'normal')
            except Exception:
                pass
            await asyncio.sleep(300)

    async def stream_social_aggregate_10m(self):
        while True:
            try:
                news = await self.sentiment.aggregator.fetch_all(limit=20)
                enriched: List[Dict] = []
                for n in (news or [])[:30]:
                    t = (n.get('title') or '') + ' ' + (n.get('description') or '')
                    s = self.sentiment.analyzer.analyze_bitcoin_news(t)
                    enriched.append({ **n, 'sentiment': s or {} })
                ranked = self._rank_news(enriched)[:3]
                if ranked:
                    lines = []
                    for i, it in enumerate(ranked, 1):
                        s = it.get('sentiment', {})
                        lbl = s.get('label', 'neutral')
                        conf = s.get('score', 0)
                        lines.append(f"{i}. {it.get('title','')} — {lbl} ({conf:.2f})")
                    content = "\n".join(lines)
                    await self._push_card('sentiment_aggregate', 'Social Sentiment Aggregate', content, 'normal')
            except Exception:
                pass
            await asyncio.sleep(600)

    async def stream_market_report_10m(self):
        from agents.technical_reporter import TechnicalAnalystReporter, TechnicalSnapshot
        reporter = TechnicalAnalystReporter()
        while True:
            try:
                comp = self.rt_engine.metrics.compute()
                if self.rt_engine.metrics.ticks:
                    snap = TechnicalSnapshot(
                        timestamp=datetime.utcnow(),
                        price=self.rt_engine.metrics.ticks[-1].price,
                        rsi=comp.get('rsi'),
                        change_1m_pct=comp.get('change_1m_pct'),
                        support=comp.get('support'),
                        resistance=comp.get('resistance'),
                    )
                    report = reporter.build_report(snap)
                    await self._push_card('market_report', 'Market Report', report, 'normal')
            except Exception:
                pass
            await asyncio.sleep(600)

    async def bootstrap_once(self):
        """Push initial prompt cards so the feed is not empty on first load."""
        try:
            # Quick market report
            from agents.technical_reporter import TechnicalAnalystReporter, TechnicalSnapshot
            reporter = TechnicalAnalystReporter()
            comp = self.rt_engine.metrics.compute()
            if self.rt_engine.metrics.ticks:
                snap = TechnicalSnapshot(
                    timestamp=datetime.utcnow(),
                    price=self.rt_engine.metrics.ticks[-1].price,
                    rsi=comp.get('rsi'),
                    change_1m_pct=comp.get('change_1m_pct'),
                    support=comp.get('support'),
                    resistance=comp.get('resistance'),
                )
                report = reporter.build_report(snap)
                await self._push_card('report', 'Market Report', report, 'normal')
        except Exception:
            pass
        try:
            # Quick sentiment aggregate (top 1-2)
            news = await self.sentiment.aggregator.fetch_all(limit=10)
            enriched = []
            for n in (news or [])[:10]:
                t = (n.get('title') or '') + ' ' + (n.get('description') or '')
                s = self.sentiment.analyzer.analyze_bitcoin_news(t)
                enriched.append({ **n, 'sentiment': s or {} })
            ranked = self._rank_news(enriched)[:2]
            if ranked:
                lines = []
                for i, it in enumerate(ranked, 1):
                    s = it.get('sentiment', {})
                    lbl = s.get('label', 'neutral')
                    conf = s.get('score', 0)
                    lines.append(f"{i}. {it.get('title','')} — {lbl} ({conf:.2f})")
                await self._push_card('sentiment_aggregate', 'Social Sentiment Aggregate', "\n".join(lines), 'normal')
        except Exception:
            pass

    async def start(self):
        self._running = True
        # Launch background loops
        asyncio.create_task(self.stream_social_update_5m())
        asyncio.create_task(self.stream_social_aggregate_10m())
        asyncio.create_task(self.stream_market_report_10m())
        # Bootstrap immediately
        await self.bootstrap_once()
        # Keep coroutine alive (tasks run in background)
        while self._running:
            await asyncio.sleep(3600)


