#!/usr/bin/env python3
"""
Optimization Performance Monitoring Script

This script monitors the performance of the deployed optimization system
and provides real-time statistics on improvements.
"""

import os
import sys
import time
import signal
from datetime import datetime

# Add info_core to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'info_core'))

def monitor_optimization_performance():
    """Monitor optimization performance continuously"""
    
    try:
        from etc.redis_connector.optimized_integration import get_redis_integration
        from dotenv import load_dotenv
        
        # Load config
        load_dotenv('.env')
        
        redis_config = {
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', 6379)),
            'passwd': os.getenv('REDIS_PASS'),
            'db': 0
        }
        
        print("🚀 INFO_CORE OPTIMIZATION MONITORING")
        print("=" * 50)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Redis: {redis_config['host']}:{redis_config['port']}")
        print("Press Ctrl+C to stop monitoring")
        print()
        
        # Get integration instance
        integration = get_redis_integration(redis_config, enable_optimizations=True)
        redis_client = integration.get_redis_client()
        
        # Monitor continuously
        iteration = 0
        while True:
            iteration += 1
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            try:
                # Get optimization stats
                stats = integration.get_integration_stats()
                
                if 'redis_performance' in stats:
                    redis_stats = stats['redis_performance']
                    
                    print(f"[{timestamp}] Optimization Status:")
                    print(f"  ├─ Optimized Operations: {stats['optimized_operations']}")
                    print(f"  ├─ Legacy Operations: {stats['legacy_operations']}")
                    
                    if stats['optimized_operations'] + stats['legacy_operations'] > 0:
                        opt_rate = stats['optimized_operations'] / (stats['optimized_operations'] + stats['legacy_operations']) * 100
                        print(f"  ├─ Optimization Rate: {opt_rate:.1f}%")
                    
                    print(f"  ├─ Cache Hit Rate: {redis_stats['cache_hit_rate_percent']:.1f}%")
                    print(f"  ├─ Cache Size: {redis_stats['cache_size']} items")
                    print(f"  ├─ Redis Operations: {redis_stats['redis_operations']}")
                    print(f"  └─ Active Handlers: {stats['active_websocket_handlers']}")
                else:
                    print(f"[{timestamp}] Optimization Status: Initializing...")
                
                # Test performance every 10 iterations
                if iteration % 10 == 0:
                    print(f"  🧪 Running performance test...")
                    
                    # Quick performance test
                    start_time = time.time()
                    for i in range(100):
                        redis_client.update_ticker_data_optimized('MONITOR_TEST', f'SYM{i}', 100.0 + i, 1000000.0, 2.5)
                    
                    for i in range(100):
                        data = redis_client.get_ticker_data_optimized('MONITOR_TEST', f'SYM{i}')
                    
                    test_time = (time.time() - start_time) * 1000
                    print(f"  ⚡ Performance: {test_time:.1f}ms for 200 operations ({test_time/200:.3f}ms avg)")
                    
                    # Cleanup
                    redis_client.delete_all_exchange_stream_data('ticker', 'MONITOR_TEST')
                
                print()
                
            except Exception as e:
                print(f"[{timestamp}] ❌ Monitoring error: {e}")
                print()
            
            time.sleep(30)  # Monitor every 30 seconds
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
    except Exception as e:
        print(f"\n❌ Monitoring failed: {e}")
        import traceback
        traceback.print_exc()

def show_current_status():
    """Show current optimization status"""
    
    try:
        from etc.redis_connector.optimized_integration import get_redis_integration
        from dotenv import load_dotenv
        
        load_dotenv('.env')
        
        redis_config = {
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', 6379)),
            'passwd': os.getenv('REDIS_PASS'),
            'db': 0
        }
        
        print("📊 CURRENT OPTIMIZATION STATUS")
        print("=" * 40)
        
        integration = get_redis_integration(redis_config)
        stats = integration.get_integration_stats()
        
        print(f"Optimization Enabled: {stats['optimization_enabled']}")
        print(f"Optimized Operations: {stats['optimized_operations']}")
        print(f"Legacy Operations: {stats['legacy_operations']}")
        print(f"Active Websocket Handlers: {stats['active_websocket_handlers']}")
        
        if 'redis_performance' in stats:
            redis_stats = stats['redis_performance']
            print(f"Cache Hit Rate: {redis_stats['cache_hit_rate_percent']:.1f}%")
            print(f"Cache Size: {redis_stats['cache_size']} items")
            print(f"Total Redis Operations: {redis_stats['redis_operations']}")
        
        # Run quick benchmark
        print("\n🧪 Quick Performance Test:")
        results = integration.benchmark_performance(iterations=100)
        print(f"Read Performance Improvement: {results['improvement_percent']:+.1f}%")
        
    except Exception as e:
        print(f"❌ Status check failed: {e}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor optimization performance')
    parser.add_argument('--status', '-s', action='store_true', help='Show current status only')
    parser.add_argument('--monitor', '-m', action='store_true', help='Start continuous monitoring')
    
    args = parser.parse_args()
    
    if args.status:
        show_current_status()
    elif args.monitor or len(sys.argv) == 1:
        monitor_optimization_performance()
    else:
        parser.print_help()