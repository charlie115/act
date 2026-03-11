"""
Hyperliquid WebSocket Client

WebSocket API Documentation: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket

WebSocket URL: wss://api.hyperliquid.xyz/ws

Channels used:
- allMids: Real-time mid prices for all assets (single subscription)
- l2Book: Order book snapshots per coin (depth up to 20 levels)

Key differences from CEX:
- Single WebSocket URL for all data
- Subscribe with JSON: {"method": "subscribe", "subscription": {"type": "...", ...}}
- Symbols are just coin names (BTC, ETH), not pairs
- All perpetuals are USDC-settled

Connection limits:
- Max 100 websocket connections
- Max 1000 subscriptions
- Max 2000 messages per minute
"""

from multiprocessing import Process, Event
from threading import Thread
import pandas as pd
import traceback
import websocket
import json
import time
import _pickle as pickle
import os
import sys

from loggers.logger import InfoCoreLogger
from exchange_websocket.heartbeat import (
    has_recent_market_ready,
    is_process_heartbeat_stale,
    touch_market_ready,
    touch_process_heartbeat,
)
from acw_common.websocket import get_stale_symbol_summary
from exchange_websocket.utils import list_slice
from etc.redis_connector.redis_helper import RedisHelper
from standalone_func.store_exchange_status import fetch_market_servercheck

# Maximum allowed message delay in milliseconds - drop messages older than this
# NOTE: Hyperliquid WebSocket messages don't include server timestamps (unlike CEXs),
# so delay filtering cannot be applied. This constant is included for consistency.
MAX_MESSAGE_DELAY_MS = 100
HYPERLIQUID_TICKER_PROC_NAME = "1th_ticker_proc"


def coin_to_symbol(coin: str) -> str:
    """Convert Hyperliquid coin name to system symbol format."""
    return f"{coin}_USDC"


def symbol_to_coin(symbol: str) -> str:
    """Convert system symbol format to Hyperliquid coin name."""
    return symbol.replace("_USDC", "").replace("_USDT", "")


def hyperliquid_ticker_websocket(symbol_list, error_event, proc_name, market_type, logging_dir, acw_api, admin_id, inactivity_time_secs=120):
    """
    Standalone function for Hyperliquid ticker WebSocket.

    Subscribes to allMids channel for real-time mid prices for all assets.
    This is efficient as it requires only one subscription for all coins.

    Args:
        symbol_list: List of symbols (used for filtering, not subscription)
        error_event: multiprocessing.Event for error signaling
        market_type: Market type ("USD_M")
        logging_dir: Directory for log files
        acw_api: API client for notifications
        admin_id: Admin ID for notifications
        inactivity_time_secs: Seconds before considering connection inactive
    """
    logger = InfoCoreLogger(f"hyperliquid_{market_type.lower()}_ticker_websocket", logging_dir).logger
    logger.info(f"[HYPERLIQUID {market_type}] Ticker websocket started for {len(symbol_list)} symbols...")
    local_redis = RedisHelper()

    last_message_time = time.time()
    ws = None
    market_code = f"HYPERLIQUID_{market_type.upper()}"

    # Hyperliquid WebSocket URL
    ws_url = "wss://api.hyperliquid.xyz/ws"

    # Convert symbol list to coin set for filtering
    coin_set = set(symbol_to_coin(s) for s in symbol_list)

    def on_message(ws, message):
        nonlocal last_message_time
        last_message_time = time.time()

        try:
            if error_event.is_set():
                ws.close()
                return

            msg = json.loads(message)
            channel = msg.get("channel", "")

            # Handle subscription confirmation
            if channel == "subscriptionResponse":
                logger.info(f"hyperliquid_ticker_websocket|Subscription confirmed: {msg.get('data', {})}")
                return

            # Handle allMids updates
            if channel == "allMids":
                data = msg.get("data", {})
                mids = data.get("mids", {})

                for coin, mid_price in mids.items():
                    # Filter to only subscribed symbols
                    if coin not in coin_set:
                        continue

                    symbol = coin_to_symbol(coin)

                    # Normalize data format to match other exchanges
                    # allMids only provides mid price, other data comes from REST API
                    ticker_data = {
                        "s": symbol,
                        "c": mid_price,  # Mid price as last price approximation
                        "h": None,  # Not available from allMids
                        "l": None,  # Not available from allMids
                        "v": None,  # Not available from allMids
                        "q": None,  # Not available from allMids (use REST for atp24h)
                        "P": None,  # Not available from allMids
                        "last_update_timestamp": int(time.time() * 1_000_000)
                    }
                    local_redis.update_exchange_stream_data(
                        "ticker",
                        market_code,
                        symbol,
                        ticker_data
                    )
                    touch_market_ready(local_redis, market_code, "ticker", ticker_data["last_update_timestamp"])
                    touch_process_heartbeat(local_redis, market_code, "ticker", proc_name, ticker_data["last_update_timestamp"])

        except Exception as e:
            logger.error(f"hyperliquid_ticker_websocket|on_message error: {e}, traceback: {traceback.format_exc()}")
            error_event.set()

    def on_error(ws, error):
        logger.error(f"hyperliquid_ticker_websocket|on_error: {error}, traceback: {traceback.format_exc()}")
        acw_api.create_message_thread(admin_id, f"hyperliquid_ticker_websocket_on_error", str(error)[:1000])
        error_event.set()

    def on_close(ws, close_status_code, close_msg):
        logger.info(f"hyperliquid_ticker_websocket|### closed ###\nclose_msg: {close_msg}\nclose_status_code: {close_status_code}")

    def on_open(ws):
        # Subscribe to allMids - single subscription for all coins
        subscribe_msg = {
            "method": "subscribe",
            "subscription": {"type": "allMids"}
        }
        ws.send(json.dumps(subscribe_msg))
        logger.info(f"hyperliquid_ticker_websocket|Sent subscribe for allMids")

    # Inactivity monitoring thread
    def check_inactivity():
        logger.info(f"hyperliquid_ticker_websocket|Started monitoring inactivity...")
        while True:
            if time.time() - last_message_time > inactivity_time_secs:
                logger.error(
                    f"hyperliquid_ticker_websocket|Inactive for {inactivity_time_secs}s. Closing..."
                )
                try:
                    acw_api.create_message_thread(
                        admin_id,
                        f"hyperliquid_{market_type.lower()}_ticker_websocket Inactivity",
                        f"Inactive for {inactivity_time_secs}s. Closing websocket..."
                    )
                except Exception:
                    logger.error(f"hyperliquid_ticker_websocket|check_inactivity|{traceback.format_exc()}")

                try:
                    ws.close()
                except Exception:
                    pass

                error_event.set()
                break

            time.sleep(1)

    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    monitor_thread = Thread(target=check_inactivity, daemon=True)
    monitor_thread.start()

    try:
        ws.run_forever(ping_interval=30, ping_timeout=10)
    except Exception as e:
        logger.error(f"hyperliquid_ticker_websocket|run_forever error: {e}, traceback: {traceback.format_exc()}")

    if error_event.is_set():
        try:
            ws.close()
        except Exception:
            pass
        raise Exception(f"hyperliquid_ticker_websocket|error_event is set. Closing websocket...")


def hyperliquid_orderbook_websocket(symbol_list, error_event, proc_name, market_type, logging_dir, acw_api, admin_id, inactivity_time_secs=60):
    """
    Standalone function for Hyperliquid orderbook WebSocket.

    Subscribes to l2Book channel for each symbol for real-time best bid/ask.

    Args:
        symbol_list: List of symbols to subscribe (e.g., ["BTC_USDC", "ETH_USDC"])
        error_event: multiprocessing.Event for error signaling
        market_type: Market type ("USD_M")
        logging_dir: Directory for log files
        acw_api: API client for notifications
        admin_id: Admin ID for notifications
        inactivity_time_secs: Seconds before considering connection inactive
    """
    logger = InfoCoreLogger(f"hyperliquid_{market_type.lower()}_orderbook_websocket", logging_dir).logger
    logger.info(f"[HYPERLIQUID {market_type}] Orderbook websocket started for {len(symbol_list)} symbols...")
    local_redis = RedisHelper()

    last_message_time = time.time()
    ws = None
    market_code = f"HYPERLIQUID_{market_type.upper()}"

    # Hyperliquid WebSocket URL
    ws_url = "wss://api.hyperliquid.xyz/ws"

    # Convert symbols to coins
    coin_list = [symbol_to_coin(s) for s in symbol_list]

    def on_message(ws, message):
        nonlocal last_message_time
        last_message_time = time.time()

        try:
            if error_event.is_set():
                ws.close()
                return

            msg = json.loads(message)
            channel = msg.get("channel", "")

            # Handle subscription confirmation
            if channel == "subscriptionResponse":
                logger.debug(f"hyperliquid_orderbook_websocket|Subscription confirmed: {msg.get('data', {})}")
                return

            # Handle l2Book updates
            if channel == "l2Book":
                data = msg.get("data", {})
                coin = data.get("coin", "")

                if not coin:
                    return

                symbol = coin_to_symbol(coin)
                levels = data.get("levels", [])

                # levels[0] = bids (sorted desc by price)
                # levels[1] = asks (sorted asc by price)
                bids = levels[0] if len(levels) > 0 else []
                asks = levels[1] if len(levels) > 1 else []

                # Get best bid and ask (first level)
                best_bid = bids[0] if bids else {"px": "0", "sz": "0"}
                best_ask = asks[0] if asks else {"px": "0", "sz": "0"}

                # Normalize data format to match other exchanges (Binance bookTicker format)
                orderbook_data = {
                    "s": symbol,
                    "b": best_bid.get("px", "0"),    # Best bid price
                    "B": best_bid.get("sz", "0"),    # Best bid quantity
                    "a": best_ask.get("px", "0"),    # Best ask price
                    "A": best_ask.get("sz", "0"),    # Best ask quantity
                    "last_update_timestamp": int(time.time() * 1_000_000)
                }
                local_redis.update_exchange_stream_data(
                    "orderbook",
                    market_code,
                    symbol,
                    orderbook_data
                )
                touch_market_ready(local_redis, market_code, "orderbook", orderbook_data["last_update_timestamp"])
                touch_process_heartbeat(local_redis, market_code, "orderbook", proc_name, orderbook_data["last_update_timestamp"])

        except Exception as e:
            logger.error(f"hyperliquid_orderbook_websocket|on_message error: {e}, traceback: {traceback.format_exc()}")
            error_event.set()

    def on_error(ws, error):
        logger.error(f"hyperliquid_orderbook_websocket|on_error: {error}, traceback: {traceback.format_exc()}")
        acw_api.create_message_thread(admin_id, f"hyperliquid_orderbook_websocket_on_error", str(error)[:1000])
        error_event.set()

    def on_close(ws, close_status_code, close_msg):
        logger.info(f"hyperliquid_orderbook_websocket|### closed ###\nclose_msg: {close_msg}\nclose_status_code: {close_status_code}")

    def on_open(ws):
        # Subscribe to l2Book for each coin
        for coin in coin_list:
            subscribe_msg = {
                "method": "subscribe",
                "subscription": {"type": "l2Book", "coin": coin}
            }
            ws.send(json.dumps(subscribe_msg))
            time.sleep(0.02)  # Small delay between subscriptions to avoid rate limiting

        logger.info(f"hyperliquid_orderbook_websocket|Sent subscribe for {len(coin_list)} coins")

    # Inactivity monitoring thread
    def check_inactivity():
        logger.info(f"hyperliquid_orderbook_websocket|Started monitoring inactivity...")
        while True:
            if time.time() - last_message_time > inactivity_time_secs:
                logger.error(
                    f"hyperliquid_orderbook_websocket|Inactive for {inactivity_time_secs}s. Closing..."
                )
                try:
                    acw_api.create_message_thread(
                        admin_id,
                        f"hyperliquid_{market_type.lower()}_orderbook_websocket Inactivity",
                        f"Inactive for {inactivity_time_secs}s. Closing websocket..."
                    )
                except Exception:
                    logger.error(f"hyperliquid_orderbook_websocket|check_inactivity|{traceback.format_exc()}")

                try:
                    ws.close()
                except Exception:
                    pass

                error_event.set()
                break

            time.sleep(1)

    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    monitor_thread = Thread(target=check_inactivity, daemon=True)
    monitor_thread.start()

    try:
        ws.run_forever(ping_interval=30, ping_timeout=10)
    except Exception as e:
        logger.error(f"hyperliquid_orderbook_websocket|run_forever error: {e}, traceback: {traceback.format_exc()}")

    if error_event.is_set():
        try:
            ws.close()
        except Exception:
            pass
        raise Exception(f"hyperliquid_orderbook_websocket|error_event is set. Closing websocket...")


class HyperliquidWebsocket:
    """
    Hyperliquid WebSocket manager class.

    Manages WebSocket processes for ticker and orderbook data.
    Follows the same pattern as GateWebsocket and other exchange managers.

    Key differences from CEX:
    - Ticker uses single allMids subscription (all coins)
    - Orderbook subscribes per coin (l2Book channel)
    - All perpetuals are USDC-settled
    """

    def __init__(self, admin_id, node, proc_n, get_symbol_list, acw_api, market_type, logging_dir=None):
        self.market_type = market_type
        self.admin_id = admin_id
        self.node = node
        self.acw_api = acw_api
        self.get_symbol_list = get_symbol_list
        self.logging_dir = logging_dir
        self.local_redis = RedisHelper()
        self.local_redis.delete_all_exchange_stream_data("ticker", f"HYPERLIQUID_{self.market_type.upper()}")
        self.local_redis.delete_all_exchange_stream_data("orderbook", f"HYPERLIQUID_{self.market_type.upper()}")
        self.websocket_logger = InfoCoreLogger(f"hyperliquid_{self.market_type.lower()}_websocket", logging_dir).logger

        self.proc_n = proc_n
        self.before_symbols_list = self.get_symbol_list()
        self.websocket_logger.info(f"[HYPERLIQUID {self.market_type}] Total symbol list: {len(self.before_symbols_list)} symbols")

        # For orderbook, split symbols across processes if needed
        # Hyperliquid has 1000 subscription limit, so we can handle many symbols per process
        self.sliced_symbols_list = list_slice(self.get_symbol_list(), self.proc_n)
        self.websocket_logger.info(f"[HYPERLIQUID {self.market_type}] Sliced into {len(self.sliced_symbols_list)} groups")

        self.stop_restart_websocket = False
        self.price_proc_event_list = []
        self.websocket_proc_dict = {}
        self.websocket_symbol_dict = {}
        self.partial_stale_strikes = {}

        self._start_websocket()

        # Wait for initial data
        wait_start = time.time()
        while True:
            if not has_recent_market_ready(
                self.local_redis,
                f"HYPERLIQUID_{self.market_type.upper()}",
                ("ticker", "orderbook"),
            ):
                self.websocket_logger.info(f"[HYPERLIQUID {self.market_type}] Waiting for websocket data to be loaded...")
                time.sleep(2)
                # Timeout after 60 seconds
                if time.time() - wait_start > 60:
                    self.websocket_logger.warning(f"[HYPERLIQUID {self.market_type}] Timeout waiting for initial data")
                    break
            else:
                self.websocket_logger.info(f"[HYPERLIQUID {self.market_type}] Initial data loaded")
                break

        # Start monitoring threads
        self.monitor_shared_symbol_change_thread = Thread(target=self.monitor_shared_symbol_change, daemon=True)
        self.monitor_shared_symbol_change_thread.start()
        self.monitor_stale_data_per_proc_thread = Thread(target=self.monitor_stale_data_per_proc, daemon=True)
        self.monitor_stale_data_per_proc_thread.start()

    def __del__(self):
        self.terminate_websocket()

    def _start_websocket(self):
        """Start WebSocket processes for ticker and orderbook data."""

        def handle_price_procs():
            while True:
                try:
                    if not self.stop_restart_websocket:
                        # Check maintenance status
                        quote_asset = "USDC"
                        if fetch_market_servercheck(f"HYPERLIQUID_{self.market_type}/{quote_asset}"):
                            self.websocket_logger.info(
                                f"[HYPERLIQUID_{self.market_type}] In maintenance. Skipping websocket (re)start..."
                            )
                            time.sleep(1)
                            continue

                        # Handle ticker process (single process for allMids)
                        ticker_proc_name = "1th_ticker_proc"
                        ticker_start_proc = False
                        ticker_restarted = False

                        if ticker_proc_name in self.websocket_proc_dict and not self.websocket_proc_dict[ticker_proc_name].is_alive():
                            ticker_start_proc = True
                            ticker_restarted = True
                            self.websocket_proc_dict[ticker_proc_name].terminate()
                            self.websocket_proc_dict[ticker_proc_name].join()
                            self.websocket_logger.info(f"hyperliquid_ticker_websocket|{ticker_proc_name} terminated.")
                        elif ticker_proc_name not in self.websocket_proc_dict:
                            ticker_start_proc = True
                            self.websocket_logger.info(f"[HYPERLIQUID {self.market_type}] {ticker_proc_name} not in dict. Starting...")

                        if ticker_start_proc:
                            error_event = Event()
                            self.price_proc_event_list.append(error_event)
                            # Ticker process gets all symbols (filters internally)
                            all_symbols = self.get_symbol_list()
                            self.websocket_symbol_dict["1th_ticker_symbol"] = all_symbols
                            ticker_proc = Process(
                                target=hyperliquid_ticker_websocket,
                                args=(
                                    all_symbols,
                                    error_event,
                                    HYPERLIQUID_TICKER_PROC_NAME,
                                    self.market_type,
                                    self.logging_dir,
                                    self.acw_api,
                                    self.admin_id
                                ),
                                daemon=True
                            )
                            self.websocket_proc_dict[ticker_proc_name] = ticker_proc
                            ticker_proc.start()
                            if ticker_restarted:
                                content = f"[HYPERLIQUID {self.market_type}] Restarted {ticker_proc_name}. Alive: {ticker_proc.is_alive()}"
                                self.websocket_logger.info(content)
                                self.acw_api.create_message_thread(self.admin_id, f"HYPERLIQUID {self.market_type} ticker restart", content)
                            time.sleep(2)

                        time.sleep(0.5)

                        # Handle orderbook processes (one per symbol slice)
                        for i in range(self.proc_n):
                            index = i + 1

                            orderbook_proc_name = f"{index}th_orderbook_proc"
                            orderbook_start_proc = False
                            orderbook_restarted = False

                            if orderbook_proc_name in self.websocket_proc_dict and not self.websocket_proc_dict[orderbook_proc_name].is_alive():
                                orderbook_start_proc = True
                                orderbook_restarted = True
                                self.websocket_proc_dict[orderbook_proc_name].terminate()
                                self.websocket_proc_dict[orderbook_proc_name].join()
                                self.websocket_logger.info(f"hyperliquid_orderbook_websocket|{orderbook_proc_name} terminated.")
                            elif orderbook_proc_name not in self.websocket_proc_dict:
                                orderbook_start_proc = True
                                self.websocket_logger.info(f"[HYPERLIQUID {self.market_type}] {orderbook_proc_name} not in dict. Starting...")

                            if orderbook_start_proc:
                                error_event = Event()
                                self.price_proc_event_list.append(error_event)
                                self.websocket_symbol_dict[f"{index}th_orderbook_symbol"] = self.sliced_symbols_list[i]
                                orderbook_proc = Process(
                                    target=hyperliquid_orderbook_websocket,
                                    args=(
                                        self.sliced_symbols_list[i],
                                        error_event,
                                        orderbook_proc_name,
                                        self.market_type,
                                        self.logging_dir,
                                        self.acw_api,
                                        self.admin_id
                                    ),
                                    daemon=True
                                )
                                self.websocket_proc_dict[orderbook_proc_name] = orderbook_proc
                                orderbook_proc.start()
                                if orderbook_restarted:
                                    content = f"[HYPERLIQUID {self.market_type}] Restarted {orderbook_proc_name}. Alive: {orderbook_proc.is_alive()}"
                                    self.websocket_logger.info(content)
                                    self.acw_api.create_message_thread(self.admin_id, f"HYPERLIQUID {self.market_type} orderbook restart", content)
                                time.sleep(2)

                            time.sleep(0.5)

                except Exception as e:
                    content = f"handle_price_procs|{traceback.format_exc()}"
                    self.websocket_logger.error(content)
                    self.acw_api.create_message_thread(self.admin_id, f"[HYPERLIQUID {self.market_type}] handle_price_procs", content)
                    time.sleep(1)
                time.sleep(0.5)

        self.handle_price_procs_thread = Thread(target=handle_price_procs, daemon=True)
        self.handle_price_procs_thread.start()

    def terminate_websocket(self):
        """Terminate all WebSocket processes."""
        self.stop_restart_websocket = True
        time.sleep(0.5)
        for each_event in self.price_proc_event_list:
            each_event.set()
        self.websocket_logger.info(f"[HYPERLIQUID {self.market_type}] All websockets' events have been set.")
        self.price_proc_event_list = []

    def restart_websocket(self):
        """Restart all WebSocket processes."""
        self.terminate_websocket()
        time.sleep(3)

        # Refresh symbol list and slices
        self.before_symbols_list = self.get_symbol_list()
        self.sliced_symbols_list = list_slice(self.get_symbol_list(), self.proc_n)

        self.stop_restart_websocket = False
        self._start_websocket()
        self.websocket_logger.info(f"[HYPERLIQUID {self.market_type}] Restarted all websockets")

    def monitor_shared_symbol_change(self, loop_time_secs=60):
        """Monitor for symbol list changes and restart if needed."""
        self.websocket_logger.info(f"[HYPERLIQUID {self.market_type}] Started monitor_shared_symbol_change...")

        while True:
            try:
                time.sleep(loop_time_secs)

                if self.stop_restart_websocket:
                    continue

                # Check if symbol list has changed
                new_symbols_list = self.get_symbol_list()

                if sorted(self.before_symbols_list) != sorted(new_symbols_list):
                    # Find delisted symbols
                    delisted_symbols = set(self.before_symbols_list) - set(new_symbols_list)
                    for symbol in delisted_symbols:
                        self.local_redis.delete_exchange_stream_data("ticker", f"HYPERLIQUID_{self.market_type.upper()}", symbol)
                        self.local_redis.delete_exchange_stream_data("orderbook", f"HYPERLIQUID_{self.market_type.upper()}", symbol)
                        self.websocket_logger.info(f"[HYPERLIQUID {self.market_type}] Deleted data for delisted symbol: {symbol}")

                    # Find new symbols
                    new_symbols = set(new_symbols_list) - set(self.before_symbols_list)
                    if new_symbols:
                        self.websocket_logger.info(f"[HYPERLIQUID {self.market_type}] New symbols detected: {new_symbols}")

                    # Restart websockets with new symbol list
                    content = f"[HYPERLIQUID {self.market_type}] Symbol list changed. Restarting websockets.\nDelisted: {delisted_symbols}\nNew: {new_symbols}"
                    self.websocket_logger.info(content)
                    self.acw_api.create_message_thread(self.admin_id, f"HYPERLIQUID {self.market_type} Symbol Change", content[:1000])

                    self.restart_websocket()

            except Exception as e:
                content = f"monitor_shared_symbol_change|{traceback.format_exc()}"
                self.websocket_logger.error(content)
                self.acw_api.create_message_thread(self.admin_id, f"[HYPERLIQUID {self.market_type}] monitor_shared_symbol_change", content[:1000])

    def monitor_stale_data_per_proc(self, loop_time_secs=60, stale_threshold_secs=90):
        """Monitor for stale data and restart affected processes."""
        self.websocket_logger.info(f"[HYPERLIQUID {self.market_type}] Started monitor_stale_data_per_proc...")

        while True:
            try:
                time.sleep(loop_time_secs)

                if self.stop_restart_websocket:
                    continue

                now_us = int(time.time() * 1_000_000)

                ticker_symbols = self.websocket_symbol_dict.get("1th_ticker_symbol", [])
                if ticker_symbols:
                    ticker_proc = self.websocket_proc_dict.get(HYPERLIQUID_TICKER_PROC_NAME)
                    if ticker_proc and ticker_proc.is_alive():
                        if is_process_heartbeat_stale(
                            self.local_redis,
                            f"HYPERLIQUID_{self.market_type.upper()}",
                            "ticker",
                            HYPERLIQUID_TICKER_PROC_NAME,
                            stale_threshold_secs=stale_threshold_secs,
                            now_us=now_us,
                        ):
                            self.partial_stale_strikes.pop(HYPERLIQUID_TICKER_PROC_NAME, None)
                            self.websocket_logger.warning(f"Killing process: {HYPERLIQUID_TICKER_PROC_NAME}")
                            ticker_proc.terminate()
                            ticker_proc.join()
                            time.sleep(60)
                        else:
                            summary = get_stale_symbol_summary(
                                self.local_redis,
                                f"HYPERLIQUID_{self.market_type.upper()}",
                                "ticker",
                                ticker_symbols,
                                stale_threshold_secs=stale_threshold_secs,
                                now_us=now_us,
                            )
                            stale_count = summary["stale_count"]
                            total_symbols = summary["total_symbols"]
                            if stale_count == 0:
                                self.partial_stale_strikes.pop(HYPERLIQUID_TICKER_PROC_NAME, None)
                            else:
                                strike_count = self.partial_stale_strikes.get(HYPERLIQUID_TICKER_PROC_NAME, 0) + 1
                                self.partial_stale_strikes[HYPERLIQUID_TICKER_PROC_NAME] = strike_count
                                self.websocket_logger.warning(
                                    f"[HYPERLIQUID {self.market_type}] ticker partial stale "
                                    f"{stale_count}/{total_symbols}, strike={strike_count}, "
                                    f"symbols={summary['stale_symbols'][:5]}"
                                )
                                if stale_count == total_symbols or (
                                    strike_count >= 2 and (stale_count >= min(2, total_symbols) or summary["stale_ratio"] >= 0.25)
                                ):
                                    self.websocket_logger.warning(f"Killing process: {HYPERLIQUID_TICKER_PROC_NAME}")
                                    ticker_proc.terminate()
                                    ticker_proc.join()
                                    self.partial_stale_strikes.pop(HYPERLIQUID_TICKER_PROC_NAME, None)
                                    time.sleep(60)

                for i in range(self.proc_n):
                    index = i + 1
                    proc_name = f"{index}th_orderbook_proc"
                    proc = self.websocket_proc_dict.get(proc_name)
                    if not proc or not proc.is_alive():
                        continue
                    proc_symbols = self.websocket_symbol_dict.get(f"{index}th_orderbook_symbol", [])
                    if not proc_symbols:
                        continue

                    if is_process_heartbeat_stale(
                        self.local_redis,
                        f"HYPERLIQUID_{self.market_type.upper()}",
                        "orderbook",
                        proc_name,
                        stale_threshold_secs=stale_threshold_secs,
                        now_us=now_us,
                    ):
                        self.partial_stale_strikes.pop(proc_name, None)
                        self.websocket_logger.warning(f"Killing process: {proc_name}")
                        proc.terminate()
                        proc.join()
                        time.sleep(60)
                        continue

                    summary = get_stale_symbol_summary(
                        self.local_redis,
                        f"HYPERLIQUID_{self.market_type.upper()}",
                        "orderbook",
                        proc_symbols,
                        stale_threshold_secs=stale_threshold_secs,
                        now_us=now_us,
                    )
                    stale_count = summary["stale_count"]
                    total_symbols = summary["total_symbols"]
                    if stale_count == 0:
                        self.partial_stale_strikes.pop(proc_name, None)
                        continue

                    strike_count = self.partial_stale_strikes.get(proc_name, 0) + 1
                    self.partial_stale_strikes[proc_name] = strike_count
                    self.websocket_logger.warning(
                        f"[HYPERLIQUID {self.market_type}] {proc_name} partial stale "
                        f"{stale_count}/{total_symbols}, strike={strike_count}, "
                        f"symbols={summary['stale_symbols'][:5]}"
                    )
                    if stale_count == total_symbols or (
                        strike_count >= 2 and (stale_count >= min(2, total_symbols) or summary["stale_ratio"] >= 0.25)
                    ):
                        self.websocket_logger.warning(f"Killing process: {proc_name}")
                        proc.terminate()
                        proc.join()
                        self.partial_stale_strikes.pop(proc_name, None)
                        time.sleep(60)

            except Exception as e:
                content = f"monitor_stale_data_per_proc|{traceback.format_exc()}"
                self.websocket_logger.error(content)
                self.acw_api.create_message_thread(self.admin_id, f"[HYPERLIQUID {self.market_type}] monitor_stale_data_per_proc", content[:1000])

    def check_status(self, print_result=False, include_text=False):
        """Check WebSocket status."""
        proc_status_list = []
        print_text = ""

        for proc_name, proc in self.websocket_proc_dict.items():
            is_alive = proc.is_alive() if proc else False
            proc_status_list.append(is_alive)
            print_text += f"{proc_name}: {is_alive}\n"

        overall_status = all(proc_status_list) if proc_status_list else False

        if print_result:
            self.websocket_logger.info(f"[HYPERLIQUID {self.market_type}] WebSocket Status:\n{print_text}".rstrip())

        if include_text:
            return (overall_status, print_text)

        return overall_status


class HyperliquidUSDMWebsocket(HyperliquidWebsocket):
    """Hyperliquid USD-M (USDC-margined perpetuals) WebSocket manager."""

    def __init__(self, admin_id, node, proc_n, get_symbol_list, acw_api, logging_dir=None):
        super().__init__(
            admin_id=admin_id,
            node=node,
            proc_n=proc_n,
            get_symbol_list=get_symbol_list,
            acw_api=acw_api,
            market_type="USD_M",
            logging_dir=logging_dir
        )
