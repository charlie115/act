"""
Coinone WebSocket Implementation with Dynamic Subscription System.

Key Features:
- Limited to 20 symbols due to Coinone's WebSocket connection limit (20 per IP)
- Dynamic subscription based on 24h trading volume
- Fast new listing detection (30 second intervals)
- 24-hour minimum hold time before eviction
- Hysteresis buffer (top 25 candidates, evict below rank 25)

Architecture:
- Single WebSocket connection (unlike other exchanges that use multiple processes)
- Dynamic subscribe/unsubscribe without connection restart
- Separate threads for new listing detection, volume refresh, and stale data monitoring
"""

from multiprocessing import Process, Event, Queue
from threading import Thread, Lock
import queue  # For Queue.Empty exception
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple
import pandas as pd
import traceback
import websocket
import json
import time
import datetime
import _pickle as pickle
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from loggers.logger import InfoCoreLogger
from etc.redis_connector.redis_helper import RedisHelper
from standalone_func.store_exchange_status import fetch_market_servercheck
from exchange_plugin.coinone_plug import Coinone

# Maximum allowed message delay in milliseconds - drop messages older than this
MAX_MESSAGE_DELAY_MS = 100

# Constants
MAX_SUBSCRIPTIONS = 20
HOLD_PERIOD_HOURS = 24
NEW_LISTING_CHECK_INTERVAL_SECS = 30
VOLUME_REFRESH_INTERVAL_SECS = 300  # 5 minutes
STALE_DATA_CHECK_INTERVAL_SECS = 60
PING_INTERVAL_SECS = 300  # 5 minutes
INACTIVITY_TIMEOUT_SECS = 120
HYSTERESIS_BUFFER_SIZE = 25  # Top 25 candidates for subscription


@dataclass
class SubscriptionInfo:
    """Information about a subscribed symbol."""
    symbol: str
    subscribed_at: datetime.datetime
    is_new_listing: bool = False
    last_volume_rank: int = 0

    @property
    def hold_period_elapsed(self) -> bool:
        """Check if 24-hour hold period has elapsed."""
        elapsed = datetime.datetime.utcnow() - self.subscribed_at
        return elapsed > datetime.timedelta(hours=HOLD_PERIOD_HOURS)

    @property
    def is_evictable(self) -> bool:
        """Check if this symbol can be evicted (hold period elapsed)."""
        return self.hold_period_elapsed


class CoinoneSubscriptionState:
    """
    Thread-safe subscription state management.
    Handles the 20-symbol limit with dynamic rotation.
    """

    def __init__(self, logger):
        self.logger = logger
        self._lock = Lock()
        self.subscriptions: Dict[str, SubscriptionInfo] = {}
        self.known_markets: Set[str] = set()
        self.volume_cache: Dict[str, float] = {}

    def get_subscribed_symbols(self) -> List[str]:
        """Get list of currently subscribed symbols."""
        with self._lock:
            return list(self.subscriptions.keys())

    def get_subscription_count(self) -> int:
        """Get current number of subscriptions."""
        with self._lock:
            return len(self.subscriptions)

    def is_subscribed(self, symbol: str) -> bool:
        """Check if a symbol is currently subscribed."""
        with self._lock:
            return symbol in self.subscriptions

    def add_subscription(self, symbol: str, is_new_listing: bool = False, volume_rank: int = 0) -> bool:
        """
        Add a new subscription to local state.
        Returns True if subscription was added (symbol wasn't already subscribed).
        Note: Caller is responsible for putting symbol into subscribe_queue for IPC.
        """
        with self._lock:
            if symbol not in self.subscriptions:
                self.subscriptions[symbol] = SubscriptionInfo(
                    symbol=symbol,
                    subscribed_at=datetime.datetime.utcnow(),
                    is_new_listing=is_new_listing,
                    last_volume_rank=volume_rank
                )
                self.logger.info(f"[COINONE] Added subscription to state: {symbol} (new_listing={is_new_listing})")
                return True
            return False

    def remove_subscription(self, symbol: str) -> bool:
        """
        Remove a subscription from local state.
        Returns True if subscription was removed (symbol was subscribed).
        Note: Caller is responsible for putting symbol into unsubscribe_queue for IPC.
        """
        with self._lock:
            if symbol in self.subscriptions:
                del self.subscriptions[symbol]
                self.logger.info(f"[COINONE] Removed subscription from state: {symbol}")
                return True
            return False

    def get_evictable_symbols_sorted_by_volume(self) -> List[Tuple[str, float]]:
        """
        Get symbols that can be evicted, sorted by volume (lowest first).
        Only returns symbols where 24h hold period has elapsed.
        """
        with self._lock:
            evictable = []
            for symbol, info in self.subscriptions.items():
                if info.is_evictable:
                    volume = self.volume_cache.get(symbol, 0)
                    evictable.append((symbol, volume))
            evictable.sort(key=lambda x: x[1])  # Sort by volume ascending
            return evictable

    def get_lowest_priority_symbol(self) -> Optional[str]:
        """
        Get the lowest priority symbol to evict when at capacity.
        Priority order (lowest to highest, first to evict):
        1. Evictable (24h hold elapsed) with lowest volume
        2. In hold period, oldest subscription
        3. New listings, oldest (last resort)
        """
        with self._lock:
            evictable = []
            in_hold = []
            new_listings = []

            for symbol, info in self.subscriptions.items():
                volume = self.volume_cache.get(symbol, 0)

                if info.is_evictable:
                    evictable.append((symbol, volume, info.subscribed_at))
                elif info.is_new_listing:
                    new_listings.append((symbol, volume, info.subscribed_at))
                else:
                    in_hold.append((symbol, volume, info.subscribed_at))

            if evictable:
                evictable.sort(key=lambda x: x[1])  # Lowest volume first
                return evictable[0][0]

            if in_hold:
                in_hold.sort(key=lambda x: x[2])  # Oldest first
                return in_hold[0][0]

            if new_listings:
                new_listings.sort(key=lambda x: x[2])  # Oldest first
                return new_listings[0][0]

            return None

    def update_volume_cache(self, volume_dict: Dict[str, float]):
        """Update the volume cache."""
        with self._lock:
            self.volume_cache = volume_dict.copy()

    def update_known_markets(self, markets: Set[str]):
        """Update known markets and return new/delisted symbols."""
        with self._lock:
            new_listings = markets - self.known_markets
            delistings = self.known_markets - markets
            self.known_markets = markets.copy()
            return new_listings, delistings


def coinone_websocket_process(
    initial_symbols: List[str],
    subscribe_queue: Queue,
    unsubscribe_queue: Queue,
    error_event: Event,
    logging_dir: str,
    acw_api,
    admin_id: int
):
    """
    Main WebSocket process for Coinone.
    Handles connection, message processing, and dynamic subscription changes.

    Uses multiprocessing.Queue for inter-process communication:
    - subscribe_queue: receives symbols to subscribe to from parent process
    - unsubscribe_queue: receives symbols to unsubscribe from parent process
    """
    logger = InfoCoreLogger("coinone_websocket", logging_dir).logger
    logger.info(f"[COINONE] WebSocket process started with {len(initial_symbols)} initial symbols")
    local_redis = RedisHelper()

    ws = None
    last_message_time = time.time()
    connected = False

    def send_subscribe(ws_conn, symbol: str, channel: str):
        """Send subscribe message for a symbol/channel."""
        msg = {
            "request_type": "SUBSCRIBE",
            "channel": channel,
            "topic": {
                "quote_currency": "KRW",
                "target_currency": symbol.replace("_KRW", "")
            }
        }
        try:
            ws_conn.send(json.dumps(msg))
            logger.debug(f"[COINONE] Sent SUBSCRIBE: {symbol} / {channel}")
        except Exception as e:
            logger.error(f"[COINONE] Failed to send subscribe: {e}")

    def send_unsubscribe(ws_conn, symbol: str, channel: str):
        """Send unsubscribe message for a symbol/channel."""
        msg = {
            "request_type": "UNSUBSCRIBE",
            "channel": channel,
            "topic": {
                "quote_currency": "KRW",
                "target_currency": symbol.replace("_KRW", "")
            }
        }
        try:
            ws_conn.send(json.dumps(msg))
            logger.debug(f"[COINONE] Sent UNSUBSCRIBE: {symbol} / {channel}")
        except Exception as e:
            logger.error(f"[COINONE] Failed to send unsubscribe: {e}")

    def send_ping(ws_conn):
        """Send PING to keep connection alive."""
        msg = {"request_type": "PING"}
        try:
            ws_conn.send(json.dumps(msg))
            logger.debug("[COINONE] Sent PING")
        except Exception as e:
            logger.error(f"[COINONE] Failed to send ping: {e}")

    def on_message(ws_conn, message):
        nonlocal last_message_time
        last_message_time = time.time()

        try:
            if error_event.is_set():
                ws_conn.close()
                return

            msg = json.loads(message)
            response_type = msg.get('response_type')

            if response_type == 'DATA':
                channel = msg.get('channel', '').upper()
                data = msg.get('data', {})

                # Check message delay - drop if older than MAX_MESSAGE_DELAY_MS
                msg_ts_ms = data.get('timestamp')
                if msg_ts_ms:
                    current_ts_ms = int(time.time() * 1000)
                    if current_ts_ms - int(msg_ts_ms) > MAX_MESSAGE_DELAY_MS:
                        return  # Drop stale message

                # Extract symbol - normalize to uppercase
                target_currency = data.get('target_currency', '').upper()
                quote_currency = data.get('quote_currency', 'KRW').upper()
                symbol = f"{target_currency}_{quote_currency}"

                if channel == 'TICKER':
                    # Normalize ticker data
                    ticker_data = {
                        'symbol': symbol,
                        'base_asset': target_currency,
                        'quote_asset': quote_currency,
                        'lastPrice': float(data.get('last', 0)),
                        'highPrice': float(data.get('high', 0)),
                        'lowPrice': float(data.get('low', 0)),
                        'openPrice': float(data.get('first', 0)),
                        'volume': float(data.get('target_volume', 0)),
                        'atp24h': float(data.get('quote_volume', 0)),
                        'timestamp': data.get('timestamp', int(time.time() * 1000)),
                        'last_update_timestamp': int(time.time() * 1_000_000)
                    }
                    local_redis.update_exchange_stream_data("ticker", "COINONE_SPOT", symbol, ticker_data)

                elif channel == 'ORDERBOOK':
                    # Normalize orderbook data
                    orderbook_data = {
                        'symbol': symbol,
                        'base_asset': target_currency,
                        'quote_asset': quote_currency,
                        'bids': data.get('bids', []),
                        'asks': data.get('asks', []),
                        'timestamp': data.get('timestamp', int(time.time() * 1000)),
                        'last_update_timestamp': int(time.time() * 1_000_000)
                    }
                    local_redis.update_exchange_stream_data("orderbook", "COINONE_SPOT", symbol, orderbook_data)

            elif response_type == 'PONG':
                logger.debug("[COINONE] Received PONG")

            elif response_type == 'SUBSCRIBED':
                logger.debug(f"[COINONE] Subscription confirmed: {msg}")

            elif response_type == 'UNSUBSCRIBED':
                logger.debug(f"[COINONE] Unsubscription confirmed: {msg}")

            elif response_type == 'ERROR':
                logger.error(f"[COINONE] WebSocket error response: {msg}")

        except Exception as e:
            logger.error(f"[COINONE] on_message error: {e}, {traceback.format_exc()}")

    def on_error(ws_conn, error):
        logger.error(f"[COINONE] WebSocket on_error: {error}")
        acw_api.create_message_thread(admin_id, "[COINONE] WebSocket Error", str(error))
        error_event.set()

    def on_close(ws_conn, close_status_code, close_msg):
        nonlocal connected
        connected = False
        logger.info(f"[COINONE] WebSocket closed: code={close_status_code}, msg={close_msg}")

    def on_open(ws_conn):
        nonlocal connected
        connected = True
        logger.info("[COINONE] WebSocket connected")

        # Subscribe to initial symbols
        for symbol in initial_symbols:
            send_subscribe(ws_conn, symbol, "TICKER")
            send_subscribe(ws_conn, symbol, "ORDERBOOK")
            time.sleep(0.05)  # Small delay between subscriptions

        logger.info(f"[COINONE] Initial subscriptions sent for {len(initial_symbols)} symbols")

    def ping_loop():
        """Periodic PING to keep connection alive."""
        while not error_event.is_set():
            time.sleep(PING_INTERVAL_SECS)
            if connected and ws:
                send_ping(ws)

    def inactivity_monitor():
        """Monitor for connection inactivity."""
        while not error_event.is_set():
            time.sleep(10)
            if time.time() - last_message_time > INACTIVITY_TIMEOUT_SECS:
                logger.error(f"[COINONE] Inactive for {INACTIVITY_TIMEOUT_SECS}s, reconnecting...")
                acw_api.create_message_thread(
                    admin_id,
                    "[COINONE] WebSocket Inactivity",
                    f"No messages for {INACTIVITY_TIMEOUT_SECS} seconds. Forcing reconnect."
                )
                try:
                    ws.close()
                except:
                    pass
                error_event.set()
                break

    def subscription_change_handler():
        """Handle dynamic subscription changes via Queue from parent process."""
        while not error_event.is_set():
            time.sleep(0.1)  # Check frequently since queues are async

            if not connected or not ws:
                continue

            # Process pending subscribes from queue (non-blocking)
            while True:
                try:
                    symbol = subscribe_queue.get_nowait()
                    send_subscribe(ws, symbol, "TICKER")
                    send_subscribe(ws, symbol, "ORDERBOOK")
                    logger.info(f"[COINONE] Subscribed to {symbol} via queue")
                    time.sleep(0.05)
                except queue.Empty:
                    break

            # Process pending unsubscribes from queue (non-blocking)
            while True:
                try:
                    symbol = unsubscribe_queue.get_nowait()
                    send_unsubscribe(ws, symbol, "TICKER")
                    send_unsubscribe(ws, symbol, "ORDERBOOK")
                    # Clean up Redis
                    local_redis.delete_exchange_stream_data("ticker", "COINONE_SPOT", symbol)
                    local_redis.delete_exchange_stream_data("orderbook", "COINONE_SPOT", symbol)
                    logger.info(f"[COINONE] Unsubscribed from {symbol} via queue")
                    time.sleep(0.05)
                except queue.Empty:
                    break

    # Start background threads
    ping_thread = Thread(target=ping_loop, daemon=True)
    ping_thread.start()

    inactivity_thread = Thread(target=inactivity_monitor, daemon=True)
    inactivity_thread.start()

    subscription_thread = Thread(target=subscription_change_handler, daemon=True)
    subscription_thread.start()

    # Main WebSocket connection
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(
        "wss://stream.coinone.co.kr",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    try:
        ws.run_forever(ping_interval=30, ping_timeout=10)
    except Exception as e:
        logger.error(f"[COINONE] run_forever error: {e}, {traceback.format_exc()}")

    if error_event.is_set():
        raise Exception("[COINONE] Error event set, closing websocket process")


class CoinoneWebsocket:
    """
    Coinone WebSocket manager with dynamic subscription system.
    Handles the 20-symbol limit with intelligent rotation based on volume.
    """

    def __init__(self, admin_id, node, proc_n, get_symbol_list, acw_api, logging_dir):
        self.admin_id = admin_id
        self.node = node
        self.acw_api = acw_api
        self.get_symbol_list = get_symbol_list  # Returns shared symbols (Coinone ∩ comparison exchange)
        self.logging_dir = logging_dir
        self.logger = InfoCoreLogger("coinone_websocket", logging_dir).logger
        self.local_redis = RedisHelper()

        # Clean up old Redis data
        self.local_redis.delete_all_exchange_stream_data("ticker", "COINONE_SPOT")
        self.local_redis.delete_all_exchange_stream_data("orderbook", "COINONE_SPOT")

        # REST API client for fetching tickers/markets
        self.coinone_client = Coinone()

        # Subscription state (thread-safe)
        self.subscription_state = CoinoneSubscriptionState(self.logger)

        # WebSocket process management
        self.ws_proc = None
        self.error_event = None
        self.stop_flag = False

        # Inter-process communication queues (created in _start_websocket)
        self.subscribe_queue = None
        self.unsubscribe_queue = None

        # Initialize
        self._initialize_known_markets()
        self._initialize_subscriptions()
        self._start_websocket()

        # Wait for initial data
        self._wait_for_initial_data()

        # Start monitoring threads
        self.detect_new_listings_thread = Thread(
            target=self._detect_new_listings_loop, daemon=True
        )
        self.detect_new_listings_thread.start()

        self.refresh_subscriptions_thread = Thread(
            target=self._refresh_subscriptions_by_volume_loop, daemon=True
        )
        self.refresh_subscriptions_thread.start()

        self.monitor_stale_data_thread = Thread(
            target=self._monitor_stale_data_loop, daemon=True
        )
        self.monitor_stale_data_thread.start()

        self.handle_ws_proc_thread = Thread(
            target=self._handle_ws_proc_loop, daemon=True
        )
        self.handle_ws_proc_thread.start()

        self.logger.info("[COINONE SPOT] CoinoneWebsocket initialized")

    def __del__(self):
        self.terminate_websocket()

    def _initialize_known_markets(self):
        """Initialize the known markets set from REST API."""
        try:
            markets = self.coinone_client.get_markets("KRW")
            known = set(m['target_currency'].upper() for m in markets)
            self.subscription_state.known_markets = known
            self.logger.info(f"[COINONE] Initialized {len(known)} known markets")
        except Exception as e:
            self.logger.error(f"[COINONE] Failed to initialize known markets: {e}")
            self.subscription_state.known_markets = set()

    def _initialize_subscriptions(self):
        """Initialize subscriptions with top 20 symbols by volume."""
        try:
            # Get shared symbols (exist on both Coinone and comparison exchange)
            shared_symbols = self.get_symbol_list()
            self.logger.info(f"[COINONE] Shared symbols count: {len(shared_symbols)}")

            # Get tickers with volume
            ticker_df = self.coinone_client.spot_all_tickers()

            if ticker_df.empty:
                self.logger.error("[COINONE] No ticker data available for initialization")
                return

            # Filter to shared symbols only
            # shared_symbols are in format like "BTC_KRW" for Coinone
            ticker_df = ticker_df[ticker_df['symbol'].isin(shared_symbols)]

            if ticker_df.empty:
                self.logger.warning("[COINONE] No shared symbols found, using top symbols from Coinone")
                ticker_df = self.coinone_client.spot_all_tickers()

            # Sort by volume and get top 20
            ticker_df = ticker_df.sort_values('atp24h', ascending=False)
            top_symbols = ticker_df.head(MAX_SUBSCRIPTIONS)['symbol'].tolist()

            # Add subscriptions
            for i, symbol in enumerate(top_symbols):
                self.subscription_state.subscriptions[symbol] = SubscriptionInfo(
                    symbol=symbol,
                    subscribed_at=datetime.datetime.utcnow(),
                    is_new_listing=False,
                    last_volume_rank=i + 1
                )

            # Update volume cache
            volume_dict = dict(zip(ticker_df['symbol'], ticker_df['atp24h']))
            self.subscription_state.update_volume_cache(volume_dict)

            self.logger.info(f"[COINONE] Initialized {len(self.subscription_state.subscriptions)} subscriptions")
            self.logger.info(f"[COINONE] Top symbols: {top_symbols[:5]}...")

        except Exception as e:
            self.logger.error(f"[COINONE] Failed to initialize subscriptions: {e}, {traceback.format_exc()}")

    def _start_websocket(self):
        """Start the WebSocket process."""
        self.error_event = Event()
        initial_symbols = self.subscription_state.get_subscribed_symbols()

        # Create queues for inter-process communication
        self.subscribe_queue = Queue()
        self.unsubscribe_queue = Queue()

        self.ws_proc = Process(
            target=coinone_websocket_process,
            args=(
                initial_symbols,
                self.subscribe_queue,
                self.unsubscribe_queue,
                self.error_event,
                self.logging_dir,
                self.acw_api,
                self.admin_id
            ),
            daemon=True
        )
        self.ws_proc.start()
        self.logger.info("[COINONE] WebSocket process started with Queue-based IPC")

    def _wait_for_initial_data(self, timeout=60):
        """Wait for initial WebSocket data to be populated."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            ticker_data = self.local_redis.get_all_exchange_stream_data("ticker", "COINONE_SPOT")
            orderbook_data = self.local_redis.get_all_exchange_stream_data("orderbook", "COINONE_SPOT")

            if ticker_data and orderbook_data:
                self.logger.info(f"[COINONE SPOT] Initial data loaded: {len(ticker_data)} tickers, {len(orderbook_data)} orderbooks")
                return

            self.logger.info("[COINONE SPOT] Waiting for WebSocket data to be loaded...")
            time.sleep(2)

        self.logger.warning("[COINONE SPOT] Timeout waiting for initial data")

    def _subscribe_to_symbol(self, symbol: str, is_new_listing: bool = False, volume_rank: int = 0):
        """
        Subscribe to a symbol: update local state AND notify child process via queue.
        """
        if self.subscription_state.add_subscription(symbol, is_new_listing, volume_rank):
            # Put into queue to notify child process
            if hasattr(self, 'subscribe_queue') and self.subscribe_queue:
                self.subscribe_queue.put(symbol)
                self.logger.info(f"[COINONE] Queued subscribe for: {symbol}")

    def _unsubscribe_from_symbol(self, symbol: str):
        """
        Unsubscribe from a symbol: update local state AND notify child process via queue.
        """
        if self.subscription_state.remove_subscription(symbol):
            # Put into queue to notify child process
            if hasattr(self, 'unsubscribe_queue') and self.unsubscribe_queue:
                self.unsubscribe_queue.put(symbol)
                self.logger.info(f"[COINONE] Queued unsubscribe for: {symbol}")

    def _handle_ws_proc_loop(self):
        """Monitor and restart WebSocket process if it dies."""
        self.logger.info("[COINONE SPOT] Started handle_ws_proc_loop")

        while not self.stop_flag:
            try:
                # Check if in maintenance
                if fetch_market_servercheck("COINONE_SPOT/KRW"):
                    self.logger.info("[COINONE SPOT] In maintenance, skipping WebSocket restart")
                    time.sleep(10)
                    continue

                # Check if process is dead
                if self.ws_proc and not self.ws_proc.is_alive():
                    self.logger.error("[COINONE SPOT] WebSocket process died, restarting...")
                    self.acw_api.create_message_thread(
                        self.admin_id,
                        "[COINONE] WebSocket Restart",
                        "WebSocket process died and is being restarted"
                    )

                    # Clean up old process
                    try:
                        self.ws_proc.terminate()
                        self.ws_proc.join(timeout=5)
                    except:
                        pass

                    # Restart
                    self._start_websocket()
                    time.sleep(5)

            except Exception as e:
                self.logger.error(f"[COINONE] handle_ws_proc_loop error: {e}, {traceback.format_exc()}")

            time.sleep(1)

    def _detect_new_listings_loop(self):
        """
        Fast loop to detect new listings (every 30 seconds).
        New listings are immediately subscribed, evicting lowest priority if needed.
        """
        self.logger.info("[COINONE SPOT] Started detect_new_listings_loop")

        while not self.stop_flag:
            time.sleep(NEW_LISTING_CHECK_INTERVAL_SECS)

            try:
                # Check maintenance
                if fetch_market_servercheck("COINONE_SPOT/KRW"):
                    continue

                # Fetch current markets
                current_markets = set(m['target_currency'].upper()
                                     for m in self.coinone_client.get_markets("KRW"))

                # Detect changes
                new_listings, delistings = self.subscription_state.update_known_markets(current_markets)

                # Handle new listings - IMMEDIATE subscription
                if new_listings:
                    for base_asset in new_listings:
                        symbol = f"{base_asset}_KRW"
                        self._handle_new_listing(symbol, base_asset)

                    content = (f"[COINONE SPOT] New listing detected!\n"
                              f"Symbols: {list(new_listings)}\n"
                              f"Action: Immediately subscribed")
                    self.logger.info(content)
                    self.acw_api.create_message_thread(
                        self.admin_id,
                        "[COINONE] New Listing Detected",
                        content
                    )

                # Handle delistings
                if delistings:
                    for base_asset in delistings:
                        symbol = f"{base_asset}_KRW"
                        self._handle_delisting(symbol)

                    content = (f"[COINONE SPOT] Delisting detected!\n"
                              f"Symbols: {list(delistings)}\n"
                              f"Action: Unsubscribed and cleaned up")
                    self.logger.info(content)
                    self.acw_api.create_message_thread(
                        self.admin_id,
                        "[COINONE] Delisting Detected",
                        content
                    )

            except Exception as e:
                content = f"detect_new_listings_loop|{traceback.format_exc()}"
                self.logger.error(content)
                self.acw_api.create_message_thread(
                    self.admin_id,
                    "[COINONE] detect_new_listings Error",
                    content
                )

    def _handle_new_listing(self, symbol: str, base_asset: str):
        """Handle a newly listed symbol - immediate subscription."""
        # Check if already subscribed
        if self.subscription_state.is_subscribed(symbol):
            return

        # Check if we need to evict
        if self.subscription_state.get_subscription_count() >= MAX_SUBSCRIPTIONS:
            evict_symbol = self.subscription_state.get_lowest_priority_symbol()
            if evict_symbol:
                self._unsubscribe_from_symbol(evict_symbol)
                self.logger.info(f"[COINONE] Evicted {evict_symbol} for new listing {symbol}")

        # Subscribe to new listing
        self._subscribe_to_symbol(symbol, is_new_listing=True, volume_rank=0)

    def _handle_delisting(self, symbol: str):
        """Handle a delisted symbol."""
        if self.subscription_state.is_subscribed(symbol):
            self._unsubscribe_from_symbol(symbol)

        # Clean up Redis
        self.local_redis.delete_exchange_stream_data("ticker", "COINONE_SPOT", symbol)
        self.local_redis.delete_exchange_stream_data("orderbook", "COINONE_SPOT", symbol)

    def _refresh_subscriptions_by_volume_loop(self):
        """
        Periodic refresh of subscriptions based on 24h volume.
        Uses hysteresis buffer to prevent oscillation.
        """
        self.logger.info("[COINONE SPOT] Started refresh_subscriptions_by_volume_loop")

        while not self.stop_flag:
            time.sleep(VOLUME_REFRESH_INTERVAL_SECS)

            try:
                # Check maintenance
                if fetch_market_servercheck("COINONE_SPOT/KRW"):
                    continue

                # Get shared symbols
                shared_symbols = self.get_symbol_list()

                # Get current tickers
                ticker_df = self.coinone_client.spot_all_tickers()
                if ticker_df.empty:
                    continue

                # Filter to shared symbols
                ticker_df = ticker_df[ticker_df['symbol'].isin(shared_symbols)]
                if ticker_df.empty:
                    continue

                # Sort by volume
                ticker_df = ticker_df.sort_values('atp24h', ascending=False)

                # Get top candidates (with hysteresis buffer)
                top_25_symbols = set(ticker_df.head(HYSTERESIS_BUFFER_SIZE)['symbol'].tolist())
                top_20_symbols = set(ticker_df.head(MAX_SUBSCRIPTIONS)['symbol'].tolist())

                current_subscriptions = set(self.subscription_state.get_subscribed_symbols())

                # Find candidates to add (in top 20 but not subscribed)
                candidates_to_add = list(top_20_symbols - current_subscriptions)

                # Find evictable symbols (below rank 25 AND hold period elapsed)
                evictable = self.subscription_state.get_evictable_symbols_sorted_by_volume()
                evictable_below_threshold = [(s, v) for s, v in evictable
                                             if f"{s}" not in top_25_symbols]

                # Perform swaps
                swaps_made = []

                for symbol_to_add in candidates_to_add:
                    if self.subscription_state.get_subscription_count() < MAX_SUBSCRIPTIONS:
                        # Have room, just add
                        rank = list(ticker_df['symbol']).index(symbol_to_add) + 1 if symbol_to_add in list(ticker_df['symbol']) else 0
                        self._subscribe_to_symbol(symbol_to_add, is_new_listing=False, volume_rank=rank)
                        swaps_made.append((None, symbol_to_add))

                    elif evictable_below_threshold:
                        # Need to evict
                        symbol_to_evict, _ = evictable_below_threshold.pop(0)
                        self._unsubscribe_from_symbol(symbol_to_evict)

                        rank = list(ticker_df['symbol']).index(symbol_to_add) + 1 if symbol_to_add in list(ticker_df['symbol']) else 0
                        self._subscribe_to_symbol(symbol_to_add, is_new_listing=False, volume_rank=rank)
                        swaps_made.append((symbol_to_evict, symbol_to_add))

                    else:
                        # No evictable symbols below threshold
                        self.logger.debug(f"[COINONE] Cannot add {symbol_to_add} - no evictable symbols below rank 25")

                # Update volume cache
                volume_dict = dict(zip(ticker_df['symbol'], ticker_df['atp24h']))
                self.subscription_state.update_volume_cache(volume_dict)

                if swaps_made:
                    content = (f"[COINONE SPOT] Subscription rotation:\n"
                              f"Swaps: {swaps_made}\n"
                              f"Current count: {self.subscription_state.get_subscription_count()}/{MAX_SUBSCRIPTIONS}")
                    self.logger.info(content)
                    self.acw_api.create_message_thread(
                        self.admin_id,
                        "[COINONE] Subscription Rotation",
                        content
                    )

            except Exception as e:
                content = f"refresh_subscriptions_by_volume_loop|{traceback.format_exc()}"
                self.logger.error(content)
                self.acw_api.create_message_thread(
                    self.admin_id,
                    "[COINONE] refresh_subscriptions Error",
                    content
                )

    def _monitor_stale_data_loop(self, stale_threshold_secs=90):
        """Monitor for stale data and report issues."""
        self.logger.info("[COINONE SPOT] Started monitor_stale_data_loop")

        while not self.stop_flag:
            time.sleep(STALE_DATA_CHECK_INTERVAL_SECS)

            try:
                now_us = int(time.time() * 1_000_000)
                ticker_data = self.local_redis.get_all_exchange_stream_data("ticker", "COINONE_SPOT")

                if not ticker_data:
                    continue

                stale_symbols = []
                for symbol in self.subscription_state.get_subscribed_symbols():
                    symbol_data = ticker_data.get(symbol, {})
                    last_update = symbol_data.get('last_update_timestamp')

                    if last_update is None:
                        stale_symbols.append(symbol)
                        continue

                    diff_secs = (now_us - last_update) / 1_000_000
                    if diff_secs > stale_threshold_secs:
                        stale_symbols.append(symbol)

                if len(stale_symbols) > 0:
                    self.logger.warning(
                        f"[COINONE SPOT] {len(stale_symbols)} symbols stale: {stale_symbols[:5]}..."
                    )

                # If ALL symbols are stale, force reconnect
                subscribed_count = self.subscription_state.get_subscription_count()
                if subscribed_count > 0 and len(stale_symbols) == subscribed_count:
                    content = (f"[COINONE SPOT] All {subscribed_count} symbols are stale!\n"
                              f"Forcing WebSocket reconnect.")
                    self.logger.error(content)
                    self.acw_api.create_message_thread(
                        self.admin_id,
                        "[COINONE] All Data Stale",
                        content
                    )

                    if self.error_event:
                        self.error_event.set()

            except Exception as e:
                self.logger.error(f"[COINONE] monitor_stale_data_loop error: {e}, {traceback.format_exc()}")

    def terminate_websocket(self):
        """Terminate the WebSocket connection."""
        self.stop_flag = True

        if self.error_event:
            self.error_event.set()

        if self.ws_proc:
            try:
                self.ws_proc.terminate()
                self.ws_proc.join(timeout=5)
            except:
                pass

        self.logger.info("[COINONE SPOT] WebSocket terminated")

    def restart_websocket(self):
        """Restart the WebSocket connection."""
        self.terminate_websocket()
        time.sleep(1)
        self.stop_flag = False
        self._start_websocket()

    def check_status(self, print_result=False, include_text=False):
        """Check WebSocket status."""
        if not self.ws_proc:
            proc_status = False
            print_text = "[COINONE SPOT] WebSocket process not initialized"
        else:
            proc_status = self.ws_proc.is_alive()
            sub_count = self.subscription_state.get_subscription_count()
            print_text = (f"[COINONE SPOT] WebSocket alive: {proc_status}, "
                         f"Subscriptions: {sub_count}/{MAX_SUBSCRIPTIONS}")

        if print_result:
            self.logger.info(print_text.rstrip())

        if include_text:
            return (proc_status, print_text)

        return proc_status

    def get_subscription_info(self) -> Dict:
        """Get detailed subscription information."""
        return {
            'subscribed_symbols': self.subscription_state.get_subscribed_symbols(),
            'subscription_count': self.subscription_state.get_subscription_count(),
            'max_subscriptions': MAX_SUBSCRIPTIONS,
            'known_markets_count': len(self.subscription_state.known_markets),
            'websocket_alive': self.ws_proc.is_alive() if self.ws_proc else False
        }
