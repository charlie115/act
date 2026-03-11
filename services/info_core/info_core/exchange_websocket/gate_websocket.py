"""
Gate.io Futures WebSocket Client

WebSocket API Documentation: https://www.gate.com/docs/developers/futures/ws/en/

WebSocket URL for USDT-margined futures: wss://fx-ws.gateio.ws/v4/ws/usdt

Channels:
- futures.tickers: Real-time ticker data
- futures.book_ticker: Best bid/ask prices
"""

from multiprocessing import Process, Manager, Event
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
from acw_common.websocket import (
    get_process_group_status,
    restart_process_group,
    terminate_process_group,
)
from exchange_websocket.utils import list_slice
from etc.redis_connector.redis_helper import RedisHelper
from standalone_func.store_exchange_status import fetch_market_servercheck

# Maximum allowed message delay in milliseconds - drop messages older than this
MAX_MESSAGE_DELAY_MS = 100


def gate_ticker_websocket(symbol_list, error_event, proc_name, market_type, logging_dir, acw_api, admin_id, inactivity_time_secs=120):
    """
    Standalone function for Gate.io ticker WebSocket.

    Subscribes to futures.tickers channel for real-time ticker updates.

    Args:
        symbol_list: List of symbols to subscribe (e.g., ["BTC_USDT", "ETH_USDT"])
        error_event: multiprocessing.Event for error signaling
        market_type: Market type ("USD_M")
        logging_dir: Directory for log files
        acw_api: API client for notifications
        admin_id: Admin ID for notifications
        inactivity_time_secs: Seconds before considering connection inactive
    """
    logger = InfoCoreLogger(f"gate_{market_type.lower()}_ticker_websocket", logging_dir).logger
    logger.info(f"[GATE {market_type}] Ticker websocket started for {len(symbol_list)} symbols...")
    local_redis = RedisHelper()

    last_message_time = time.time()
    ws = None
    market_code = f"GATE_{market_type.upper()}"

    # Gate.io WebSocket URL for USDT futures
    if market_type == "USD_M":
        ws_url = "wss://fx-ws.gateio.ws/v4/ws/usdt"
    else:
        raise Exception(f"gate_ticker_websocket|market_type should be USD_M, not {market_type}")

    def on_message(ws, message):
        nonlocal last_message_time
        last_message_time = time.time()

        try:
            if error_event.is_set():
                ws.close()
                return

            msg = json.loads(message)

            # Handle subscription confirmation
            if msg.get("event") == "subscribe":
                logger.info(f"gate_ticker_websocket|Subscribed to channel: {msg.get('channel')}")
                return

            # Handle ticker updates
            if msg.get("channel") == "futures.tickers" and msg.get("event") == "update":
                # Check message delay - drop if older than MAX_MESSAGE_DELAY_MS
                # Gate.io uses 'time' field in seconds since epoch
                msg_ts_sec = msg.get("time")
                if msg_ts_sec:
                    current_ts_ms = int(time.time() * 1000)
                    msg_ts_ms = int(msg_ts_sec * 1000)
                    if current_ts_ms - msg_ts_ms > MAX_MESSAGE_DELAY_MS:
                        return  # Drop stale message

                result = msg.get("result", [])
                # Gate.io can return result as a list or dict
                if isinstance(result, dict):
                    result = [result]
                if isinstance(result, list):
                    for item in result:
                        if isinstance(item, dict) and "contract" in item:
                            symbol = item["contract"]
                            # Normalize data format to match other exchanges
                            ticker_data = {
                                "s": symbol,
                                "c": item.get("last"),          # Last price (close)
                                "h": item.get("high_24h"),      # 24h high
                                "l": item.get("low_24h"),       # 24h low
                                "v": item.get("volume_24h"),    # 24h volume
                                "q": item.get("volume_24h_settle"),  # 24h quote volume
                                "P": item.get("change_percentage"),  # Price change %
                                "index_price": item.get("index_price"),
                                "mark_price": item.get("mark_price"),
                                "funding_rate": item.get("funding_rate"),
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
            logger.error(f"gate_ticker_websocket|on_message error: {e}, traceback: {traceback.format_exc()}")
            error_event.set()

    def on_error(ws, error):
        logger.error(f"gate_ticker_websocket|on_error: {error}, traceback: {traceback.format_exc()}")
        acw_api.create_message_thread(admin_id, f"gate_ticker_websocket_on_error", str(error)[:1000])
        error_event.set()

    def on_close(ws, close_status_code, close_msg):
        logger.info(f"gate_ticker_websocket|### closed ###\nclose_msg: {close_msg}\nclose_status_code: {close_status_code}")

    def on_open(ws):
        # Subscribe to ticker channel for all symbols
        subscribe_msg = {
            "time": int(time.time()),
            "channel": "futures.tickers",
            "event": "subscribe",
            "payload": symbol_list
        }
        ws.send(json.dumps(subscribe_msg))
        logger.info(f"gate_ticker_websocket|Sent subscribe for {len(symbol_list)} symbols")

    # Inactivity monitoring thread
    def check_inactivity():
        logger.info(f"gate_ticker_websocket|Started monitoring inactivity...")
        while True:
            if time.time() - last_message_time > inactivity_time_secs:
                logger.error(
                    f"gate_ticker_websocket|Inactive for {inactivity_time_secs}s. Closing..."
                )
                try:
                    acw_api.create_message_thread(
                        admin_id,
                        f"gate_{market_type.lower()}_ticker_websocket Inactivity",
                        f"Inactive for {inactivity_time_secs}s. Closing websocket..."
                    )
                except Exception:
                    logger.error(f"gate_ticker_websocket|check_inactivity|{traceback.format_exc()}")

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
        logger.error(f"gate_ticker_websocket|run_forever error: {e}, traceback: {traceback.format_exc()}")

    if error_event.is_set():
        try:
            ws.close()
        except Exception:
            pass
        raise Exception(f"gate_ticker_websocket|error_event is set. Closing websocket...")


def gate_orderbook_websocket(symbol_list, error_event, proc_name, market_type, logging_dir, acw_api, admin_id, inactivity_time_secs=60):
    """
    Standalone function for Gate.io orderbook (book_ticker) WebSocket.

    Subscribes to futures.book_ticker channel for real-time best bid/ask.

    Args:
        symbol_list: List of symbols to subscribe (e.g., ["BTC_USDT", "ETH_USDT"])
        error_event: multiprocessing.Event for error signaling
        market_type: Market type ("USD_M")
        logging_dir: Directory for log files
        acw_api: API client for notifications
        admin_id: Admin ID for notifications
        inactivity_time_secs: Seconds before considering connection inactive
    """
    logger = InfoCoreLogger(f"gate_{market_type.lower()}_orderbook_websocket", logging_dir).logger
    logger.info(f"[GATE {market_type}] Orderbook websocket started for {len(symbol_list)} symbols...")
    local_redis = RedisHelper()

    last_message_time = time.time()
    ws = None
    market_code = f"GATE_{market_type.upper()}"

    # Gate.io WebSocket URL for USDT futures
    if market_type == "USD_M":
        ws_url = "wss://fx-ws.gateio.ws/v4/ws/usdt"
    else:
        raise Exception(f"gate_orderbook_websocket|market_type should be USD_M, not {market_type}")

    def on_message(ws, message):
        nonlocal last_message_time
        last_message_time = time.time()

        try:
            if error_event.is_set():
                ws.close()
                return

            msg = json.loads(message)

            # Handle subscription confirmation
            if msg.get("event") == "subscribe":
                logger.info(f"gate_orderbook_websocket|Subscribed to channel: {msg.get('channel')}")
                return

            # Handle book ticker updates
            if msg.get("channel") == "futures.book_ticker" and msg.get("event") == "update":
                # Check message delay - drop if older than MAX_MESSAGE_DELAY_MS
                # Gate.io uses 'time' field in seconds since epoch
                msg_ts_sec = msg.get("time")
                if msg_ts_sec:
                    current_ts_ms = int(time.time() * 1000)
                    msg_ts_ms = int(msg_ts_sec * 1000)
                    if current_ts_ms - msg_ts_ms > MAX_MESSAGE_DELAY_MS:
                        return  # Drop stale message

                result = msg.get("result", [])
                # Gate.io can return result as a list or dict
                if isinstance(result, dict):
                    result = [result]
                if isinstance(result, list):
                    for item in result:
                        # Gate.io book_ticker uses 's' for symbol (contract name)
                        symbol = item.get("s") or item.get("contract")
                        if isinstance(item, dict) and symbol:
                            # Normalize data format to match other exchanges (Binance bookTicker format)
                            orderbook_data = {
                                "s": symbol,
                                "b": item.get("b"),    # Best bid price
                                "B": item.get("B"),    # Best bid quantity
                                "a": item.get("a"),    # Best ask price
                                "A": item.get("A"),    # Best ask quantity
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
            logger.error(f"gate_orderbook_websocket|on_message error: {e}, traceback: {traceback.format_exc()}")
            error_event.set()

    def on_error(ws, error):
        logger.error(f"gate_orderbook_websocket|on_error: {error}, traceback: {traceback.format_exc()}")
        acw_api.create_message_thread(admin_id, f"gate_orderbook_websocket_on_error", str(error)[:1000])
        error_event.set()

    def on_close(ws, close_status_code, close_msg):
        logger.info(f"gate_orderbook_websocket|### closed ###\nclose_msg: {close_msg}\nclose_status_code: {close_status_code}")

    def on_open(ws):
        # Subscribe to book_ticker channel for all symbols
        subscribe_msg = {
            "time": int(time.time()),
            "channel": "futures.book_ticker",
            "event": "subscribe",
            "payload": symbol_list
        }
        ws.send(json.dumps(subscribe_msg))
        logger.info(f"gate_orderbook_websocket|Sent subscribe for {len(symbol_list)} symbols")

    # Inactivity monitoring thread
    def check_inactivity():
        logger.info(f"gate_orderbook_websocket|Started monitoring inactivity...")
        while True:
            if time.time() - last_message_time > inactivity_time_secs:
                logger.error(
                    f"gate_orderbook_websocket|Inactive for {inactivity_time_secs}s. Closing..."
                )
                try:
                    acw_api.create_message_thread(
                        admin_id,
                        f"gate_{market_type.lower()}_orderbook_websocket Inactivity",
                        f"Inactive for {inactivity_time_secs}s. Closing websocket..."
                    )
                except Exception:
                    logger.error(f"gate_orderbook_websocket|check_inactivity|{traceback.format_exc()}")

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
        logger.error(f"gate_orderbook_websocket|run_forever error: {e}, traceback: {traceback.format_exc()}")

    if error_event.is_set():
        try:
            ws.close()
        except Exception:
            pass
        raise Exception(f"gate_orderbook_websocket|error_event is set. Closing websocket...")


class GateWebsocket:
    """
    Gate.io WebSocket manager class.

    Manages multiple WebSocket processes for ticker and orderbook data.
    Follows the same pattern as BinanceWebsocket and BybitWebsocket.
    """

    def __init__(self, admin_id, node, proc_n, get_symbol_list, acw_api, market_type, logging_dir=None):
        self.market_type = market_type
        self.admin_id = admin_id
        self.node = node
        self.acw_api = acw_api
        self.get_symbol_list = get_symbol_list
        self.logging_dir = logging_dir
        self.local_redis = RedisHelper()
        self.local_redis.delete_all_exchange_stream_data("ticker", f"GATE_{self.market_type.upper()}")
        self.local_redis.delete_all_exchange_stream_data("orderbook", f"GATE_{self.market_type.upper()}")
        self.websocket_logger = InfoCoreLogger(f"gate_{self.market_type.lower()}_websocket", logging_dir).logger

        self.proc_n = proc_n
        self.before_symbols_list = self.get_symbol_list()
        self.websocket_logger.info(f"[GATE {self.market_type}] Total symbol list: {len(self.before_symbols_list)} symbols")
        self.sliced_symbols_list = list_slice(self.get_symbol_list(), self.proc_n)
        self.websocket_logger.info(f"[GATE {self.market_type}] Sliced into {len(self.sliced_symbols_list)} groups")
        self.stop_restart_websocket = False
        self.price_proc_event_list = []
        self.websocket_proc_dict = {}
        self.websocket_symbol_dict = {}
        self.partial_stale_strikes = {}

        self._start_websocket()

        # Wait for initial data
        while True:
            if not has_recent_market_ready(
                self.local_redis,
                f"GATE_{self.market_type.upper()}",
                ("ticker", "orderbook"),
            ):
                self.websocket_logger.info(f"[GATE {self.market_type}] Waiting for websocket data to be loaded...")
                time.sleep(2)
            else:
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
                        quote_asset = "USDT"
                        if fetch_market_servercheck(f"GATE_{self.market_type}/{quote_asset}"):
                            self.websocket_logger.info(
                                f"[GATE_{self.market_type}] In maintenance. Skipping websocket (re)start..."
                            )
                            time.sleep(1)
                            continue

                        for i in range(self.proc_n):
                            index = i + 1

                            # Handle ticker process
                            ticker_proc_name = f"{index}th_ticker_proc"
                            ticker_start_proc = False
                            ticker_restarted = False

                            if ticker_proc_name in self.websocket_proc_dict and not self.websocket_proc_dict[ticker_proc_name].is_alive():
                                ticker_start_proc = True
                                ticker_restarted = True
                                self.websocket_proc_dict[ticker_proc_name].terminate()
                                self.websocket_proc_dict[ticker_proc_name].join()
                                self.websocket_logger.info(f"gate_ticker_websocket|{ticker_proc_name} terminated.")
                            elif ticker_proc_name not in self.websocket_proc_dict:
                                ticker_start_proc = True
                                self.websocket_logger.info(f"[GATE {self.market_type}] {ticker_proc_name} not in dict. Starting...")

                            if ticker_start_proc:
                                error_event = Event()
                                self.price_proc_event_list.append(error_event)
                                self.websocket_symbol_dict[f"{index}th_ticker_symbol"] = self.sliced_symbols_list[i]
                                ticker_proc = Process(
                                    target=gate_ticker_websocket,
                                    args=(
                                        self.sliced_symbols_list[i],
                                        error_event,
                                        ticker_proc_name,
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
                                    content = f"[GATE {self.market_type}] Restarted {ticker_proc_name}. Alive: {ticker_proc.is_alive()}"
                                    self.websocket_logger.info(content)
                                    self.acw_api.create_message_thread(self.admin_id, f"GATE {self.market_type} ticker restart", content)
                                time.sleep(2)

                            time.sleep(0.5)

                            # Handle orderbook process
                            orderbook_proc_name = f"{index}th_orderbook_proc"
                            orderbook_start_proc = False
                            orderbook_restarted = False

                            if orderbook_proc_name in self.websocket_proc_dict and not self.websocket_proc_dict[orderbook_proc_name].is_alive():
                                orderbook_start_proc = True
                                orderbook_restarted = True
                                self.websocket_proc_dict[orderbook_proc_name].terminate()
                                self.websocket_proc_dict[orderbook_proc_name].join()
                                self.websocket_logger.info(f"gate_orderbook_websocket|{orderbook_proc_name} terminated.")
                            elif orderbook_proc_name not in self.websocket_proc_dict:
                                orderbook_start_proc = True
                                self.websocket_logger.info(f"[GATE {self.market_type}] {orderbook_proc_name} not in dict. Starting...")

                            if orderbook_start_proc:
                                error_event = Event()
                                self.price_proc_event_list.append(error_event)
                                self.websocket_symbol_dict[f"{index}th_orderbook_symbol"] = self.sliced_symbols_list[i]
                                orderbook_proc = Process(
                                    target=gate_orderbook_websocket,
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
                                    content = f"[GATE {self.market_type}] Restarted {orderbook_proc_name}. Alive: {orderbook_proc.is_alive()}"
                                    self.websocket_logger.info(content)
                                    self.acw_api.create_message_thread(self.admin_id, f"GATE {self.market_type} orderbook restart", content)
                                time.sleep(2)

                            time.sleep(0.5)

                except Exception as e:
                    content = f"handle_price_procs|{traceback.format_exc()}"
                    self.websocket_logger.error(content)
                    self.acw_api.create_message_thread(self.admin_id, f"[GATE {self.market_type}] handle_price_procs", content)
                    time.sleep(1)
                time.sleep(0.5)

        self.handle_price_procs_thread = Thread(target=handle_price_procs, daemon=True)
        self.handle_price_procs_thread.start()

    def terminate_websocket(self):
        """Terminate all WebSocket processes."""
        terminate_process_group(
            self,
            self.websocket_logger,
            f"[GATE {self.market_type}] All websockets' events have been set.",
        )

    def restart_websocket(self):
        """Restart all WebSocket processes."""
        restart_process_group(
            self,
            self.websocket_logger,
            f"[GATE {self.market_type}] All websockets' events have been set.",
        )

    def check_status(self, print_result=False, include_text=False):
        """Check status of all WebSocket processes."""
        return get_process_group_status(
            self.websocket_proc_dict,
            self.websocket_logger,
            f"[GATE {self.market_type}] ",
            print_result=print_result,
            include_text=include_text,
        )

    def monitor_shared_symbol_change(self, loop_time_secs=60):
        """Monitor for symbol list changes and restart websockets if needed."""
        self.websocket_logger.info(f"[GATE {self.market_type}] Started monitor_shared_symbol_change...")
        monitor_count = 0
        while True:
            time.sleep(loop_time_secs)
            try:
                new_symbols_list = self.get_symbol_list()

                if sorted(self.before_symbols_list) != sorted(new_symbols_list):
                    monitor_count += 1
                    if monitor_count > 5:
                        deleted_symbols = [x for x in self.before_symbols_list if x not in new_symbols_list]
                        added_symbols = [x for x in new_symbols_list if x not in self.before_symbols_list]
                        content = f"monitor_shared_symbol_change|[GATE {self.market_type}] Symbol changed. Deleted: {deleted_symbols}, Added: {added_symbols}"
                        self.websocket_logger.info(content)
                        self.acw_api.create_message_thread(self.admin_id, "monitor_shared_symbol_change", content)

                        self.before_symbols_list = new_symbols_list
                        self.sliced_symbols_list = list_slice(self.get_symbol_list(), self.proc_n)
                        self.restart_websocket()

                        for each_symbol in deleted_symbols:
                            try:
                                self.websocket_logger.info(f"monitor_shared_symbol_change|Deleting {each_symbol} from redis...")
                                self.local_redis.delete_exchange_stream_data("ticker", f"GATE_{self.market_type.upper()}", each_symbol)
                            except Exception:
                                self.websocket_logger.error(f"monitor_shared_symbol_change|{traceback.format_exc()}")
                            try:
                                self.local_redis.delete_exchange_stream_data("orderbook", f"GATE_{self.market_type.upper()}", each_symbol)
                            except Exception:
                                self.websocket_logger.error(f"monitor_shared_symbol_change|{traceback.format_exc()}")
                        monitor_count = 0
                else:
                    monitor_count = 0

            except Exception as e:
                content = f"monitor_shared_symbol_change|{traceback.format_exc()}"
                self.websocket_logger.error(content)
                self.acw_api.create_message_thread(self.admin_id, f"[GATE {self.market_type}] monitor_shared_symbol_change", content)

    def monitor_stale_data_per_proc(self, loop_time_secs=60, stale_threshold_secs=90):
        """
        Monitor for stale data and restart individual processes if all symbols are stale.
        """
        self.websocket_logger.info(f"[GATE {self.market_type}] Started monitor_stale_data_per_proc...")
        while True:
            time.sleep(loop_time_secs)
            now_us = int(time.time() * 1_000_000)

            try:
                for proc_name, proc in list(self.websocket_proc_dict.items()):
                    if not proc.is_alive():
                        continue

                    # Determine symbol list key and redis stream type
                    if "ticker_proc" in proc_name:
                        symbol_list_key = proc_name.replace("proc", "symbol")
                        redis_stream_type = "ticker"
                    elif "orderbook_proc" in proc_name:
                        symbol_list_key = proc_name.replace("proc", "symbol")
                        redis_stream_type = "orderbook"
                    else:
                        continue

                    symbol_list = self.websocket_symbol_dict.get(symbol_list_key, [])
                    if not symbol_list:
                        continue

                    if is_process_heartbeat_stale(
                        self.local_redis,
                        f"GATE_{self.market_type.upper()}",
                        redis_stream_type,
                        proc_name,
                        stale_threshold_secs=stale_threshold_secs,
                        now_us=now_us,
                    ):
                        self.partial_stale_strikes.pop(proc_name, None)
                        content = (
                            f"[GATE {self.market_type}] {proc_name} => "
                            f"Heartbeat stale for > {stale_threshold_secs}s. "
                            f"Forcing process restart."
                        )
                        self.websocket_logger.error(content)
                        self.acw_api.create_message_thread(self.admin_id, "monitor_stale_data_per_proc", content)

                        self.websocket_logger.warning(f"Killing process: {proc_name}")
                        proc.terminate()
                        proc.join()
                        self.partial_stale_strikes.pop(proc_name, None)
                        time.sleep(60)
                        continue

                    summary = get_stale_symbol_summary(
                        self.local_redis,
                        f"GATE_{self.market_type.upper()}",
                        redis_stream_type,
                        symbol_list,
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
                    stale_symbols_preview = summary["stale_symbols"][:5]

                    if stale_count == total_symbols:
                        content = (
                            f"[GATE {self.market_type}] {proc_name} => "
                            f"All {stale_count}/{total_symbols} symbols are stale for > {stale_threshold_secs}s. "
                            f"Forcing process restart."
                        )
                        self.websocket_logger.error(content)
                        self.acw_api.create_message_thread(self.admin_id, "monitor_stale_data_per_proc", content)
                        self.websocket_logger.warning(f"Killing process: {proc_name}")
                        proc.terminate()
                        proc.join()
                        self.partial_stale_strikes.pop(proc_name, None)
                        time.sleep(60)
                        continue

                    self.websocket_logger.warning(
                        f"[GATE {self.market_type}] {proc_name} partial stale "
                        f"{stale_count}/{total_symbols}, strike={strike_count}, "
                        f"symbols={stale_symbols_preview}"
                    )
                    if strike_count >= 2 and (stale_count >= min(2, total_symbols) or summary["stale_ratio"] >= 0.25):
                        content = (
                            f"[GATE {self.market_type}] {proc_name} => "
                            f"Partial stale persisted ({stale_count}/{total_symbols}, strike={strike_count}). "
                            f"Forcing process restart."
                        )
                        self.websocket_logger.error(content)
                        self.acw_api.create_message_thread(self.admin_id, "monitor_stale_data_per_proc", content)
                        self.websocket_logger.warning(f"Killing process: {proc_name}")
                        proc.terminate()
                        proc.join()
                        self.partial_stale_strikes.pop(proc_name, None)
                        time.sleep(60)

            except Exception as e:
                content = f"monitor_stale_data_per_proc|{traceback.format_exc()}"
                self.websocket_logger.error(content)
                self.acw_api.create_message_thread(self.admin_id, f"[GATE {self.market_type}] monitor_stale_data_per_proc", content)


class GateUSDMWebsocket(GateWebsocket):
    """Gate.io USD-M Futures WebSocket class."""

    def __init__(self, admin_id, node, proc_n, get_symbol_list, acw_api, market_type, logging_dir):
        super().__init__(admin_id, node, proc_n, get_symbol_list, acw_api, market_type, logging_dir)
