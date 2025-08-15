from langchain_community.llms import Ollama
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool
from typing import List, Dict, Any
import os
from tools.coinbase_tools import get_bitcoin_candles, get_bitcoin_price
import asyncio
import json

class BitcoinAnalystAgent:
    def __init__(self):
        # Use a stronger model by default, configurable via env
        from config.settings import settings
        self.llm = Ollama(
            model=getattr(settings, "OLLAMA_MODEL", "tinyllama"),
            temperature=0.3,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
        )
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.system_prompt = (
            "You are CoinLink, a professional Bitcoin (BTC) analyst."
            " Answer directly and concisely with specific, useful insights.\n"
            "Rules:\n"
            "- Only discuss Bitcoin (BTC). If asked about other assets, redirect to BTC.\n"
            "- Use Bitcoin-specific indicators (RSI, SMA/EMA, funding rates, open interest, hash rate, difficulty, supply metrics).\n"
            "- Incorporate market structure (trend, key levels), risk, and actionable takeaways.\n"
            "- If data is missing, be upfront but still provide structured guidance.\n\n"
            "Context: {btc_context}\n"
            "Chat history: {chat_history}\n\n"
            "User: {input}\n"
            "Assistant:"
        )

        self.prompt = PromptTemplate(
            input_variables=["btc_context", "chat_history", "input"],
            template=self.system_prompt
        )

        self.tools = []

    def add_tools(self, tools: List[BaseTool]):
        """Add tools for Bitcoin analysis"""
        self.tools = tools

    async def analyze_bitcoin(self, user_input: str, btc_context: Dict[str, Any] = None) -> str:
        """Analyze Bitcoin based on user input"""
        try:
            if not btc_context:
                btc_context = {
                    "current_price": "Unknown",
                    "24h_change": "Unknown",
                    "sentiment": "neutral"
                }

            # Format context for the prompt
            context_str = f"Price: {btc_context.get('current_price', 'Unknown')}, " \
                         f"24h Change: {btc_context.get('24h_change', 'Unknown')}, " \
                         f"Sentiment: {btc_context.get('sentiment', 'neutral')}"

            # Check if input is Bitcoin-related
            if not self._is_bitcoin_related(user_input):
                return self._redirect_to_bitcoin(user_input, btc_context)

            # Use direct LLM call first
            response = await self.llm.ainvoke(
                self.prompt.format(
                    btc_context=context_str,
                    chat_history="",
                    input=user_input
                )
            )
            return response

        except Exception as e:
            # Fallback: generate fast deterministic technical snapshot
            try:
                return self._fallback_technical_analysis(user_input, btc_context)
            except Exception as inner_err:
                return f"I encountered an error while analyzing Bitcoin: {str(e)}. Fallback also failed: {str(inner_err)}. Please try again."

    def _is_bitcoin_related(self, user_input: str) -> bool:
        """Check if user input is related to Bitcoin"""
        bitcoin_keywords = ['bitcoin', 'btc', 'crypto', 'cryptocurrency', 'price', 'market', 'analysis']
        user_input_lower = user_input.lower()
        return any(keyword in user_input_lower for keyword in bitcoin_keywords)

    def _redirect_to_bitcoin(self, user_input: str, btc_context: Dict[str, Any]) -> str:
        """Redirect non-Bitcoin queries to Bitcoin analysis"""
        return f"I focus exclusively on Bitcoin analysis. For BTC: current price {btc_context.get('current_price', 'Unknown')} " \
               f"with {btc_context.get('24h_change', 'Unknown')} 24h change. Would you like detailed Bitcoin metrics?"

    # ---------- Fallback deterministic analysis ----------
    def _compute_rsi(self, closes: List[float], period: int = 14) -> float:
        if len(closes) < period + 1:
            return 50.0
        gains: List[float] = []
        losses: List[float] = []
        for i in range(1, period + 1):
            delta = closes[-(i+0)] - closes[-(i+1)]
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

    def _fallback_technical_analysis(self, user_input: str, btc_context: Dict[str, Any]) -> str:
        # Fetch latest candles (hourly) and compute RSI + simple key levels
        candles_resp = get_bitcoin_candles("BTC-USD", granularity=3600, limit=200)
        if "error" in candles_resp:
            # As a last resort, only echo context
            return (
                f"BTC quick snapshot: {btc_context.get('current_price','Unknown')} (24h {btc_context.get('24h_change','Unknown')}), "
                f"sentiment {btc_context.get('sentiment','neutral')}. Unable to compute indicators right now."
            )

        candles = candles_resp.get("candles", [])
        if len(candles) < 20:
            return (
                f"BTC quick snapshot: {btc_context.get('current_price','Unknown')} (24h {btc_context.get('24h_change','Unknown')}), "
                f"sentiment {btc_context.get('sentiment','neutral')}. Not enough data for indicators."
            )

        closes = [c["close"] for c in candles]
        highs = [c["high"] for c in candles]
        lows = [c["low"] for c in candles]
        last_close = closes[-1]
        prev_close = closes[-25] if len(closes) > 25 else closes[0]
        change_24h_pct = ((last_close - prev_close) / prev_close) * 100 if prev_close else 0.0
        rsi_14 = self._compute_rsi(closes, period=14)

        recent_high = max(highs[-48:]) if len(highs) >= 48 else max(highs)
        recent_low = min(lows[-48:]) if len(lows) >= 48 else min(lows)

        bias = "range-bound"
        if rsi_14 >= 60 and last_close > (recent_high + recent_low) / 2:
            bias = "bullish"
        elif rsi_14 <= 40 and last_close < (recent_high + recent_low) / 2:
            bias = "bearish"

        # Optional correlation context (if passed through btc_context when available)
        corr_line = ""
        try:
            c30 = btc_context.get('corr_30m') if isinstance(btc_context, dict) else None
            lmin = btc_context.get('lead_minutes') if isinstance(btc_context, dict) else None
            lcorr = btc_context.get('lead_corr') if isinstance(btc_context, dict) else None
            if c30 is not None:
                corr_line += f"Correlation(30m): {c30:+.2f}\n"
            if lmin is not None and lcorr is not None:
                corr_line += f"Leading: sentiment ~{int(lmin)}m (corr {lcorr:+.2f})\n"
        except Exception:
            pass

        return (
            "BTC Technical Snapshot\n"
            "----------------------\n"
            f"Price: ${last_close:,.2f}  |  24h: {change_24h_pct:+.2f}%\n"
            f"RSI(14): {rsi_14:.1f}  ({'overbought' if rsi_14>70 else 'oversold' if rsi_14<30 else 'neutral'})\n"
            f"Support: ~ ${recent_low:,.0f}    Resistance: ~ ${recent_high:,.0f}\n"
            f"Bias: {bias}\n"
            f"{corr_line if corr_line else ''}"
            "\nActionable\n"
            "- Watch for break/retest of support/resistance.\n"
            "- Align entries with RSI and trend bias; size risk accordingly."
        )

    async def get_bitcoin_insights(self, price_data: Dict[str, Any], sentiment_data: Dict[str, Any]) -> str:
        """Generate Bitcoin insights from price and sentiment data"""
        try:
            context = {
                "current_price": f"${price_data.get('price', 'Unknown')}",
                "24h_change": f"{price_data.get('change_24h', 'Unknown')}%",
                "volume": price_data.get('volume', 'Unknown'),
                "sentiment": sentiment_data.get('label', 'neutral'),
                "sentiment_score": sentiment_data.get('score', 0)
            }

            insight_prompt = f"""
            Based on this Bitcoin data, provide a concise analysis:
            - Price: {context['current_price']}
            - 24h Change: {context['24h_change']}
            - Volume: {context['volume']}
            - Sentiment: {context['sentiment']} (score: {context['sentiment_score']})

            Provide 2-3 key insights about Bitcoin's current market position.
            """

            response = await self.llm.ainvoke(insight_prompt)
            return response

        except Exception as e:
            return f"Unable to generate Bitcoin insights: {str(e)}"
