import asyncio
import json
import time
from collections import deque, defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import jwt  # pyjwt
import websockets

from config.settings import settings
from .engine import RealTimeAlertEngine


@dataclass
class OrderBook:
    bids: Dict[str, float]
    asks: Dict[str, float]


class CoinbaseWebSocketClient:
    """Simple Coinbase (Pro) public websocket client for ticker updates.
    Note: Coinbase Advanced Trade WS differs. This client targets
    ws-feed.exchange.coinbase.com 'ticker' for BTC-USD as a public feed.
    """

    def __init__(self, alert_engine: RealTimeAlertEngine, product_ids: Optional[List[str]] = None):
        self.alert_engine = alert_engine
        self.product_ids = product_ids or ["BTC-USD"]
        # Authenticated Advanced Trade user WS
        self.uri = "wss://advanced-trade-ws-user.coinbase.com"
        self._running = False
        self._message_buffer: deque = deque(maxlen=1000)
        self._order_books: Dict[str, OrderBook] = {pid: OrderBook(bids={}, asks={}) for pid in self.product_ids}
        # Parse CDP key JSON
        try:
            self._key_json = json.loads(settings.COINBASE_KEY_JSON) if settings.COINBASE_KEY_JSON else None
        except Exception:
            self._key_json = None

    def _generate_jwt(self) -> Optional[str]:
        if not self._key_json:
            return None
        name = self._key_json.get("name")
        private_key = self._key_json.get("privateKey")
        if not name or not private_key:
            return None
        now = int(time.time())
        payload = {"sub": name, "iat": now, "exp": now + 120}
        try:
            return jwt.encode(payload, private_key, algorithm="ES256")
        except Exception:
            return None

    def _subscribe_message(self) -> str:
        channels = [
            {"name": "ticker", "product_ids": self.product_ids},
            {"name": "level2", "product_ids": self.product_ids},
            {"name": "heartbeat", "product_ids": self.product_ids},
            {"name": "candles", "product_ids": self.product_ids},
        ]
        return json.dumps({"type": "subscribe", "channels": channels})

    async def _handle_messages(self, ws):
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except Exception:
                continue
            self._message_buffer.append(msg)
            await self._process_message(msg)

    async def _process_message(self, msg: Dict):
        # Parse various Advanced Trade user WS formats
        channel = msg.get("channel") or msg.get("type")
        # Ticker: { channel: 'ticker', events: [{ tickers: [{ product_id, price, volume_24h, time }] }] }
        if msg.get("channel") == "ticker" and msg.get("events"):
            for ev in msg.get("events") or []:
                for t in ev.get("tickers") or []:
                    product = t.get("product_id")
                    price = t.get("price")
                    vol24 = t.get("volume_24h")
                    ts = t.get("time") or t.get("timestamp")
                    price_f = None
                    vol_f = 0.0
                    if price is not None:
                        try:
                            price_f = float(price)
                        except Exception:
                            price_f = None
                    if vol24 is not None:
                        try:
                            vol_f = float(vol24)
                        except Exception:
                            vol_f = 0.0
                    ts_dt: Optional[datetime] = None
                    if ts:
                        try:
                            ts_dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                        except Exception:
                            ts_dt = None
                    if price_f is not None and product in self.product_ids:
                        print(f"[Ticker] {product} price={price_f} vol24h={vol_f}")
                        await self.alert_engine.handle_tick(price_f, vol_f, ts_dt)
            return

        # Level2 updates
        # Example expected: { channel: 'level2', events: [{ updates: [{ product_id, side, price, size }] }] }
        if msg.get("channel") == "level2" and msg.get("events"):
            for ev in msg.get("events") or []:
                for upd in ev.get("updates") or []:
                    product = upd.get("product_id")
                    if product not in self._order_books:
                        continue
                    book = self._order_books[product]
                    side = upd.get("side")
                    price = str(upd.get("price"))
                    size = str(upd.get("size"))
                    if side == "buy":
                        if size == "0" or size == "0.0":
                            book.bids.pop(price, None)
                        else:
                            try:
                                book.bids[price] = float(size)
                            except Exception:
                                pass
                    elif side == "sell":
                        if size == "0" or size == "0.0":
                            book.asks.pop(price, None)
                        else:
                            try:
                                book.asks[price] = float(size)
                            except Exception:
                                pass
                    # Log top of book
                    best_bid = max(book.bids.keys(), default=None)
                    best_ask = min(book.asks.keys(), default=None)
                    if best_bid or best_ask:
                        print(f"[L2] {product} best_bid={best_bid} best_ask={best_ask}")
            return

        # Candles and heartbeat can be logged for verification
        if msg.get("channel") == "candles":
            print("[Candles]", msg)
        if msg.get("channel") == "heartbeat":
            print("[Heartbeat]", msg)

    async def start(self):
        self._running = True
        backoff = 1
        while self._running:
            try:
                token = self._generate_jwt()
                headers = [("Authorization", f"Bearer {token}")] if token else []
                async with websockets.connect(self.uri, extra_headers=headers, ping_interval=20, ping_timeout=20) as ws:
                    print("[Coinbase WS] Connected to Advanced Trade user WS")
                    await ws.send(self._subscribe_message())
                    print("[Coinbase WS] Subscribed to: ticker, level2, heartbeat, candles")

                    # Replay buffered messages (log only)
                    for m in list(self._message_buffer):
                        try:
                            await self._process_message(m)
                        except Exception:
                            pass

                    async def refresh_jwt_task():
                        while True:
                            await asyncio.sleep(110)
                            print("[Coinbase WS] Refreshing JWT and reconnecting...")
                            await ws.close()
                            break

                    await asyncio.gather(self._handle_messages(ws), refresh_jwt_task())
                    backoff = 1
            except Exception as e:
                print("[Coinbase WS] error:", str(e))
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)

    def stop(self):
        self._running = False


