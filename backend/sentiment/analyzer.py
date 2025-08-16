from transformers import pipeline
import httpx
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import xml.etree.ElementTree as ET
from config.settings import settings
import time
import hashlib

class BitcoinSentimentAnalyzer:
    def __init__(self):
        # Initialize classifier defensively to avoid startup crashes if HF token is missing/invalid
        self.classifier = None
        self.bitcoin_keywords = settings.BTC_KEYWORDS
        self._cache = {}
        self._cache_ttl_seconds = 300  # 5 minutes
        try:
            hf_token = settings.HF_TOKEN
            # Only pass token if it looks non-placeholder
            if hf_token and isinstance(hf_token, str) and not hf_token.lower().startswith("your_"):
                try:
                    self.classifier = pipeline(
                        "sentiment-analysis",
                        model=getattr(settings, "SENTIMENT_MODEL", "ProsusAI/finbert"),
                        token=hf_token
                    )
                except Exception:
                    # Retry anonymously
                    self.classifier = pipeline(
                        "sentiment-analysis",
                        model=getattr(settings, "SENTIMENT_MODEL", "ProsusAI/finbert")
                    )
            else:
                # No token provided – try anonymous access
                self.classifier = pipeline(
                    "sentiment-analysis",
                    model=getattr(settings, "SENTIMENT_MODEL", "ProsusAI/finbert")
                )
        except Exception:
            # Leave classifier as None; call sites will handle gracefully
            self.classifier = None
        
    def analyze_bitcoin_news(self, text: str) -> Optional[Dict[str, Any]]:
        """Analyze sentiment of Bitcoin-related news"""
        try:
            # Check if text contains Bitcoin-related keywords
            if not self._is_bitcoin_related(text):
                return None
            
            # Cache lookup (5 minutes)
            norm = (text or '').strip().lower()
            key = hashlib.sha256(norm.encode('utf-8')).hexdigest()
            now = time.time()
            cached = self._cache.get(key)
            if cached and (now - cached[0]) < self._cache_ttl_seconds:
                return cached[1]

            # Analyze sentiment
            if not self.classifier:
                return None
            result = self.classifier(text)[0]
            
            out = {
                "label": result["label"],  # positive/negative/neutral
                "score": result["score"],
                "asset": "BTC",
                "text_preview": text[:100] + "..." if len(text) > 100 else text
            }
            self._cache[key] = (now, out)
            return out
        except Exception as e:
            print(f"Error analyzing sentiment: {str(e)}")
            return None
    
    def analyze_multiple_news(self, news_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sentiment of multiple Bitcoin news articles"""
        try:
            if not self.classifier:
                # Neutral fallback when classifier unavailable
                return {
                    "overall_sentiment": "neutral",
                    "average_score": 0,
                    "total_articles": 0,
                    "positive_count": 0,
                    "negative_count": 0,
                    "neutral_count": 0,
                    "bitcoin_news": []
                }
            bitcoin_news = []
            total_sentiment_score = 0
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            
            for news in news_list:
                title = news.get('title', '') or ''
                description = news.get('description', '') or ''
                combined_text = f"{title} {description}".strip()
                
                if self._is_bitcoin_related(combined_text):
                    sentiment = self.analyze_bitcoin_news(combined_text)
                    if sentiment:
                        bitcoin_news.append({
                            **news,
                            'sentiment': sentiment
                        })
                        
                        # Aggregate sentiment scores
                        if sentiment['label'] == 'positive':
                            positive_count += 1
                            total_sentiment_score += sentiment['score']
                        elif sentiment['label'] == 'negative':
                            negative_count += 1
                            total_sentiment_score -= sentiment['score']
                        else:
                            neutral_count += 1
            
            # Calculate overall sentiment
            total_articles = len(bitcoin_news)
            if total_articles > 0:
                avg_sentiment_score = total_sentiment_score / total_articles
                
                if positive_count > negative_count:
                    overall_sentiment = "positive"
                elif negative_count > positive_count:
                    overall_sentiment = "negative"
                else:
                    overall_sentiment = "neutral"
            else:
                overall_sentiment = "neutral"
                avg_sentiment_score = 0
            
            return {
                "overall_sentiment": overall_sentiment,
                "average_score": avg_sentiment_score,
                "total_articles": total_articles,
                "positive_count": positive_count,
                "negative_count": negative_count,
                "neutral_count": neutral_count,
                "bitcoin_news": bitcoin_news
            }
            
        except Exception as e:
            print(f"Error analyzing multiple news: {str(e)}")
            return {
                "overall_sentiment": "neutral",
                "average_score": 0,
                "total_articles": 0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "bitcoin_news": []
            }
    
    def _is_bitcoin_related(self, text: str) -> bool:
        """Check if text is related to Bitcoin"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.bitcoin_keywords)
    
    def get_sentiment_emoji(self, sentiment: str) -> str:
        """Get emoji representation of sentiment"""
        sentiment_map = {
            "positive": "🟢",
            "negative": "🔴", 
            "neutral": "⚪"
        }
        return sentiment_map.get(sentiment, "⚪")

class BitcoinNewsFetcher:
    def __init__(self):
        self.newsapi_key = settings.NEWSAPI_API_KEY
        
    async def get_bitcoin_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch Bitcoin-related news from NewsAPI"""
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": "bitcoin OR BTC",
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": limit,
                "apiKey": self.newsapi_key
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                articles = []
                for article in data.get('articles', []):
                    articles.append({
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'url': article.get('url', ''),
                        'publishedAt': article.get('publishedAt', ''),
                        'source': article.get('source', {}).get('name', '')
                    })
                
                return articles
                
        except Exception as e:
            print(f"Error fetching Bitcoin news: {str(e)}")
            return []
    
    async def get_crypto_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch general crypto news and filter for Bitcoin"""
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": "cryptocurrency OR crypto",
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": limit,
                "apiKey": self.newsapi_key
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                bitcoin_articles = []
                for article in data.get('articles', []):
                    title = article.get('title', '') or ''
                    description = article.get('description', '') or ''
                    title_desc = f"{title} {description}".strip()
                    if any(keyword in title_desc.lower() for keyword in ['bitcoin', 'btc']):
                        bitcoin_articles.append({
                            'title': article.get('title', ''),
                            'description': article.get('description', ''),
                            'url': article.get('url', ''),
                            'publishedAt': article.get('publishedAt', ''),
                            'source': article.get('source', {}).get('name', '')
                        })
                
                return bitcoin_articles[:limit]
                
        except Exception as e:
            print(f"Error fetching crypto news: {str(e)}")
            return []


class RedditNewsFetcher:
    def __init__(self):
        # Public JSON endpoints, low rate limits; set UA
        self.headers = {"User-Agent": "coinlink-mvp/1.0"}

    async def _fetch_subreddit(self, subreddit: str, limit: int = 20) -> List[Dict[str, Any]]:
        url = f"https://www.reddit.com/r/{subreddit}/search.json"
        params = {
            "q": "bitcoin OR BTC",
            "sort": "new",
            "restrict_sr": 1,
            "t": "day",
            "limit": limit,
        }
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=10) as client:
                r = await client.get(url, params=params)
                r.raise_for_status()
                data = r.json()
                out: List[Dict[str, Any]] = []
                for child in (data.get("data", {}).get("children", []) or []):
                    post = child.get("data", {})
                    title = post.get("title", "") or ""
                    selftext = post.get("selftext", "") or ""
                    created_utc = post.get("created_utc")
                    published = datetime.utcfromtimestamp(created_utc).isoformat() if created_utc else ""
                    url_post = post.get("url") or f"https://www.reddit.com{post.get('permalink','')}"
                    out.append({
                        "title": title,
                        "description": selftext[:280],
                        "url": url_post,
                        "publishedAt": published,
                        "source": f"reddit/{subreddit}",
                    })
                return out
        except Exception:
            return []

    async def get_bitcoin_posts(self, limit: int = 20) -> List[Dict[str, Any]]:
        subs = ["Bitcoin", "BitcoinMarkets", "CryptoCurrency"]
        results: List[Dict[str, Any]] = []
        for s in subs:
            items = await self._fetch_subreddit(s, limit=limit)
            results.extend(items)
        return results[: limit * len(subs)]


class CoinbaseBlogFetcher:
    def __init__(self):
        self.urls = [
            "https://blog.coinbase.com/feed",
            "https://blog.coinbase.com/rss",
        ]

    async def get_blog_posts(self, limit: int = 20) -> List[Dict[str, Any]]:
        for url in self.urls:
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    r = await client.get(url)
                    r.raise_for_status()
                    xml_text = r.text
                    # Parse RSS/Atom defensively
                    root = ET.fromstring(xml_text)
                    items = []
                    # Try RSS 'item'
                    for item in root.findall('.//item'):
                        title = (item.findtext('title') or '').strip()
                        link = (item.findtext('link') or '').strip()
                        pub = (item.findtext('pubDate') or '').strip()
                        desc = (item.findtext('description') or '').strip()
                        items.append({
                            'title': title,
                            'description': desc,
                            'url': link,
                            'publishedAt': pub,
                            'source': 'coinbase-blog'
                        })
                    if not items:
                        # Try Atom 'entry'
                        for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry'):
                            title = (entry.findtext('{http://www.w3.org/2005/Atom}title') or '').strip()
                            link_el = entry.find('{http://www.w3.org/2005/Atom}link')
                            link = link_el.get('href') if link_el is not None else ''
                            pub = (entry.findtext('{http://www.w3.org/2005/Atom}updated') or '').strip()
                            summary = (entry.findtext('{http://www.w3.org/2005/Atom}summary') or '').strip()
                            items.append({
                                'title': title,
                                'description': summary,
                                'url': link,
                                'publishedAt': pub,
                                'source': 'coinbase-blog'
                            })
                    return items[:limit]
            except Exception:
                continue
        return []


class MultiSourceNewsAggregator:
    def __init__(self):
        self.newsapi = BitcoinNewsFetcher()
        self.reddit = RedditNewsFetcher()
        self.coinbase_blog = CoinbaseBlogFetcher()

    async def fetch_all(self, limit: int = 20) -> List[Dict[str, Any]]:
        try:
            newsapi_btc, newsapi_crypto, reddit_posts, blog_posts = await asyncio.gather(
                self.newsapi.get_bitcoin_news(limit),
                self.newsapi.get_crypto_news(limit),
                self.reddit.get_bitcoin_posts(limit),
                self.coinbase_blog.get_blog_posts(limit),
            )
            combined: List[Dict[str, Any]] = []
            seen: set[Tuple[str, str]] = set()
            for lst in [newsapi_btc, newsapi_crypto, reddit_posts, blog_posts]:
                for a in lst or []:
                    key = ((a.get('title') or '').strip(), (a.get('url') or '').strip())
                    if key in seen:
                        continue
                    seen.add(key)
                    combined.append(a)
            # Prefer more recent first if publishedAt present
            def parse_dt(s: str) -> float:
                try:
                    return datetime.fromisoformat(s.replace('Z', '+00:00')).timestamp()
                except Exception:
                    return 0.0
            combined.sort(key=lambda x: parse_dt(str(x.get('publishedAt', ''))), reverse=True)
            return combined[: max(20, limit * 2)]
        except Exception:
            return []

class BitcoinSentimentService:
    def __init__(self):
        self.analyzer = BitcoinSentimentAnalyzer()
        self.news_fetcher = BitcoinNewsFetcher()
        self.aggregator = MultiSourceNewsAggregator()
    
    async def get_bitcoin_sentiment_summary(self) -> Dict[str, Any]:
        """Get comprehensive Bitcoin sentiment analysis"""
        try:
            # Fetch recent multi-source items (NewsAPI BTC/crypto, Reddit BTC, Coinbase blog)
            news = await self.aggregator.fetch_all(limit=15)
            
            # Analyze sentiment
            sentiment_analysis = self.analyzer.analyze_multiple_news(news)
            
            # Add emoji representation
            sentiment_analysis['sentiment_emoji'] = self.analyzer.get_sentiment_emoji(
                sentiment_analysis['overall_sentiment']
            )
            
            return sentiment_analysis
            
        except Exception as e:
            print(f"Error getting Bitcoin sentiment summary: {str(e)}")
            return {
                "overall_sentiment": "neutral",
                "sentiment_emoji": "⚪",
                "average_score": 0,
                "total_articles": 0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "bitcoin_news": []
            }
    
    async def analyze_single_news(self, text: str) -> Optional[Dict[str, Any]]:
        """Analyze sentiment of a single news text"""
        return self.analyzer.analyze_bitcoin_news(text)
