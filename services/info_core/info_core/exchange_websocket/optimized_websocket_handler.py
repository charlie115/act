import json
import time
import struct
from typing import Dict, Any, Optional
from etc.redis_connector.optimized_redis_helper import OptimizedRedisHelper

class OptimizedWebsocketHandler:
    """
    Optimized websocket message handler that processes exchange data
    and stores it efficiently using binary formats and memory caching.
    """
    
    def __init__(self, redis_client: OptimizedRedisHelper, market_code: str):
        self.redis_client = redis_client
        self.market_code = market_code
        self.stats = {
            'messages_processed': 0,
            'processing_time_total': 0.0,
            'errors': 0
        }
    
    def process_binance_message(self, message: str, stream_data_type: str) -> bool:
        """Process Binance websocket message with optimized storage"""
        try:
            start_time = time.time()
            msg = json.loads(message)
            
            if 's' not in msg:
                return False
            
            symbol = msg['s']
            timestamp = int(time.time() * 1_000_000)
            
            if stream_data_type == "ticker":
                # Extract ticker data
                price = float(msg.get('c', 0))  # close price
                volume = float(msg.get('q', 0))  # quote volume
                change = float(msg.get('P', 0))  # price change percent
                
                # Store using optimized method
                self.redis_client.update_ticker_data_optimized(
                    self.market_code, symbol, price, volume, change, timestamp
                )
            
            elif stream_data_type == "orderbook":
                # Extract orderbook data
                bid_price = float(msg.get('b', 0))
                ask_price = float(msg.get('a', 0))
                bid_qty = float(msg.get('B', 0))
                ask_qty = float(msg.get('A', 0))
                
                # Store using optimized method
                self.redis_client.update_orderbook_data_optimized(
                    self.market_code, symbol, bid_price, ask_price, bid_qty, ask_qty, timestamp
                )
            
            # Also store original message for compatibility
            self.redis_client.update_exchange_stream_data(
                stream_data_type, self.market_code, symbol, 
                {**msg, "last_update_timestamp": timestamp}
            )
            
            # Update stats
            self.stats['messages_processed'] += 1
            self.stats['processing_time_total'] += time.time() - start_time
            return True
            
        except Exception as e:
            self.stats['errors'] += 1
            # Fallback to legacy method for compatibility
            try:
                # Re-parse message for fallback to ensure we have valid JSON
                msg = json.loads(message)
                timestamp = int(time.time() * 1_000_000)
                self.redis_client.update_exchange_stream_data(
                    stream_data_type, self.market_code, msg['s'], 
                    {**msg, "last_update_timestamp": timestamp}
                )
                return True
            except:
                return False

    def process_okx_message(self, message: str, stream_data_type: str) -> bool:
        """Process OKX websocket message with optimized storage"""
        try:
            start_time = time.time()
            msg = json.loads(message)
            
            # OKX sends data in 'data' array
            if 'data' not in msg:
                return False
            
            for data_item in msg['data']:
                if 'instId' not in data_item:
                    continue
                
                symbol = data_item['instId']
                timestamp = int(time.time() * 1_000_000)
                
                if stream_data_type == "ticker":
                    # Extract OKX ticker data
                    price = float(data_item.get('last', 0))
                    volume = float(data_item.get('volCcy24h', 0))
                    
                    # Calculate change from open price
                    last_price = float(data_item.get('last', 0))
                    open_price = float(data_item.get('open24h', last_price))
                    change = ((last_price - open_price) / open_price * 100) if open_price > 0 else 0
                    
                    # Store ticker data
                    self.redis_client.update_ticker_data_optimized(
                        self.market_code, symbol, price, volume, change, timestamp
                    )
                    
                    # Also store ask/bid if available (OKX includes in ticker)
                    if 'askPx' in data_item and 'bidPx' in data_item:
                        bid_price = float(data_item.get('bidPx', 0))
                        ask_price = float(data_item.get('askPx', 0))
                        bid_qty = float(data_item.get('bidSz', 0))
                        ask_qty = float(data_item.get('askSz', 0))
                        
                        self.redis_client.update_orderbook_data_optimized(
                            self.market_code, symbol, bid_price, ask_price, bid_qty, ask_qty, timestamp
                        )
            
            # Also store original message for compatibility (for each data item)
            for data_item in msg['data']:
                if 'instId' in data_item:
                    symbol = data_item['instId']
                    self.redis_client.update_exchange_stream_data(
                        stream_data_type, self.market_code, symbol, 
                        {**data_item, "last_update_timestamp": timestamp}
                    )
            
            self.stats['messages_processed'] += 1
            self.stats['processing_time_total'] += time.time() - start_time
            return True
            
        except Exception as e:
            self.stats['errors'] += 1
            return False

    def process_upbit_message(self, message: str, stream_data_type: str) -> bool:
        """Process Upbit websocket message with optimized storage"""
        try:
            start_time = time.time()
            msg = json.loads(message)
            
            symbol = msg.get('cd')  # Upbit uses 'cd' for symbol
            if not symbol:
                return False
            
            timestamp = int(time.time() * 1_000_000)
            
            if stream_data_type == "ticker" and 'tp' in msg:
                # Extract Upbit ticker data
                price = float(msg.get('tp', 0))  # trade price
                volume = float(msg.get('atp24h', 0))  # accumulated trade price 24h
                change = float(msg.get('scr', 0))  # signed change rate
                
                self.redis_client.update_ticker_data_optimized(
                    self.market_code, symbol, price, volume, change, timestamp
                )
            
            elif stream_data_type == "orderbook" and 'obu' in msg:
                # Extract Upbit orderbook data
                orderbook_units = msg['obu']
                if orderbook_units and len(orderbook_units) > 0:
                    best_level = orderbook_units[0]
                    bid_price = float(best_level.get('bp', 0))
                    ask_price = float(best_level.get('ap', 0))
                    bid_qty = float(best_level.get('bs', 0))
                    ask_qty = float(best_level.get('as', 0))
                    
                    self.redis_client.update_orderbook_data_optimized(
                        self.market_code, symbol, bid_price, ask_price, bid_qty, ask_qty, timestamp
                    )
            
            # Also store original message for compatibility
            self.redis_client.update_exchange_stream_data(
                stream_data_type, self.market_code, symbol, 
                {**msg, "last_update_timestamp": timestamp}
            )
            
            self.stats['messages_processed'] += 1
            self.stats['processing_time_total'] += time.time() - start_time
            return True
            
        except Exception as e:
            self.stats['errors'] += 1
            return False

    def process_bybit_message(self, message: str, stream_data_type: str) -> bool:
        """Process Bybit websocket message with optimized storage"""
        try:
            start_time = time.time()
            msg = json.loads(message)
            
            # Bybit sends data in 'data' array
            if 'data' not in msg:
                return False
            
            for data_item in msg['data']:
                symbol = data_item.get('symbol')
                if not symbol:
                    continue
                
                timestamp = int(time.time() * 1_000_000)
                
                if stream_data_type == "ticker":
                    # Extract Bybit ticker data
                    price = float(data_item.get('lastPrice', 0))
                    volume = float(data_item.get('turnover24h', 0))  # for USD-M, volume24h for COIN-M
                    change = float(data_item.get('price24hPcnt', 0))
                    
                    self.redis_client.update_ticker_data_optimized(
                        self.market_code, symbol, price, volume, change, timestamp
                    )
                
                elif stream_data_type == "orderbook":
                    # Extract Bybit orderbook data
                    if 'b' in data_item and 'a' in data_item:
                        bids = data_item['b']
                        asks = data_item['a']
                        
                        if bids and asks and len(bids) > 0 and len(asks) > 0:
                            bid_price = float(bids[0][0])
                            bid_qty = float(bids[0][1])
                            ask_price = float(asks[0][0])
                            ask_qty = float(asks[0][1])
                            
                            self.redis_client.update_orderbook_data_optimized(
                                self.market_code, symbol, bid_price, ask_price, bid_qty, ask_qty, timestamp
                            )
            
            # Also store original message for compatibility (for each data item)
            for data_item in msg['data']:
                symbol = data_item.get('symbol')
                if symbol:
                    self.redis_client.update_exchange_stream_data(
                        stream_data_type, self.market_code, symbol, 
                        {**data_item, "last_update_timestamp": timestamp}
                    )
            
            self.stats['messages_processed'] += 1
            self.stats['processing_time_total'] += time.time() - start_time
            return True
            
        except Exception as e:
            self.stats['errors'] += 1
            return False

    def process_bithumb_message(self, message: str, stream_data_type: str) -> bool:
        """Process Bithumb websocket message with optimized storage"""
        try:
            start_time = time.time()
            msg = json.loads(message)
            
            # Bithumb has special message format with 'content' wrapper
            if 'content' in msg:
                data = msg['content']
                symbol = data.get('symbol')
            else:
                symbol = msg.get('symbol')
                data = msg
            
            if not symbol:
                return False
            
            timestamp = int(time.time() * 1_000_000)
            
            if stream_data_type == "ticker":
                # Extract Bithumb ticker data
                price = float(data.get('closePrice', 0))
                volume = float(data.get('value', 0))  # KRW volume
                change = float(data.get('chgRate', 0))
                
                self.redis_client.update_ticker_data_optimized(
                    self.market_code, symbol, price, volume, change, timestamp
                )
            
            elif stream_data_type == "orderbook":
                # Extract Bithumb orderbook data
                if 'bids' in data and 'asks' in data:
                    bids = data['bids']
                    asks = data['asks']
                    
                    if bids and asks and len(bids) > 0 and len(asks) > 0:
                        bid_price = float(bids[0][0])
                        bid_qty = float(bids[0][1])
                        ask_price = float(asks[0][0])
                        ask_qty = float(asks[0][1])
                        
                        self.redis_client.update_orderbook_data_optimized(
                            self.market_code, symbol, bid_price, ask_price, bid_qty, ask_qty, timestamp
                        )
            
            # Also store original message for compatibility
            # Use the data from 'content' field for Bithumb
            original_data = data if 'content' in msg else msg
            self.redis_client.update_exchange_stream_data(
                stream_data_type, self.market_code, symbol, 
                {**original_data, "last_update_timestamp": timestamp}
            )
            
            self.stats['messages_processed'] += 1
            self.stats['processing_time_total'] += time.time() - start_time
            return True
            
        except Exception as e:
            self.stats['errors'] += 1
            return False

    def get_average_processing_time(self) -> float:
        """Get average message processing time in seconds"""
        if self.stats['messages_processed'] == 0:
            return 0.0
        return self.stats['processing_time_total'] / self.stats['messages_processed']

    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            **self.stats,
            'average_processing_time_ms': self.get_average_processing_time() * 1000,
            'error_rate_percent': (self.stats['errors'] / max(1, self.stats['messages_processed'])) * 100
        }

def create_optimized_websocket_handler(redis_client: OptimizedRedisHelper, market_code: str) -> OptimizedWebsocketHandler:
    """Factory function to create optimized websocket handler"""
    return OptimizedWebsocketHandler(redis_client, market_code)

# Handler mapping for different exchanges
EXCHANGE_MESSAGE_HANDLERS = {
    'BINANCE': lambda handler, message, stream_type: handler.process_binance_message(message, stream_type),
    'OKX': lambda handler, message, stream_type: handler.process_okx_message(message, stream_type),
    'UPBIT': lambda handler, message, stream_type: handler.process_upbit_message(message, stream_type),
    'BYBIT': lambda handler, message, stream_type: handler.process_bybit_message(message, stream_type),
    'BITHUMB': lambda handler, message, stream_type: handler.process_bithumb_message(message, stream_type),
}

def process_exchange_message(handler: OptimizedWebsocketHandler, exchange: str, message: str, stream_data_type: str) -> bool:
    """Process message using appropriate exchange handler"""
    exchange_handler = EXCHANGE_MESSAGE_HANDLERS.get(exchange.upper())
    if exchange_handler:
        return exchange_handler(handler, message, stream_data_type)
    return False