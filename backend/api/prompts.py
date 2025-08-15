from typing import Dict, List


def get_contextual_prompts(market_data: Dict) -> List[str]:
    """Generate dynamic prompts for the preloaded prompt container."""
    prompts: List[str] = [
        "What's Bitcoin doing?",
        "BTC analysis",
    ]

    rsi = market_data.get('rsi')
    if isinstance(rsi, (int, float)):
        if rsi > 70:
            prompts.append("Is Bitcoin overbought?")
        elif rsi < 30:
            prompts.append("Good entry point?")

    price_change_1h = market_data.get('price_change_1h', 0)
    price_change_24h = market_data.get('price_change_24h', 0)
    try:
        if abs(float(price_change_1h)) > 5:
            prompts.append("Why the sudden move?")
        elif abs(float(price_change_24h)) > 10:
            prompts.append("What caused today's volatility?")
    except Exception:
        pass

    if market_data.get('near_resistance') and market_data.get('sentiment') == 'bullish':
        prompts.append("Will BTC break resistance?")
    elif market_data.get('near_support'):
        prompts.append("Will support hold?")

    sentiment_conf = market_data.get('sentiment_confidence', 0)
    sentiment = market_data.get('sentiment', 'neutral')
    try:
        if float(sentiment_conf) > 0.8:
            if sentiment == 'bullish' or sentiment == 'positive':
                prompts.append("Why so bullish?")
            elif sentiment == 'bearish' or sentiment == 'negative':
                prompts.append("Why the bearish sentiment?")
    except Exception:
        pass

    # Ensure uniqueness and cap length
    unique_prompts = []
    for p in prompts:
        if p not in unique_prompts:
            unique_prompts.append(p)
    return unique_prompts[:6]


