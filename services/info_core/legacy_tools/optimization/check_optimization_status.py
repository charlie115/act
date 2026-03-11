#!/usr/bin/env python3
"""
Optimization Status Checker

This script helps you determine if your system is using the optimized 
components or falling back to legacy systems.
"""

import os
import sys
import time
from datetime import datetime

# Add info_core to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'info_core'))

def check_optimization_status():
    """Check current optimization status and provide detailed feedback"""
    
    print("🔍 OPTIMIZATION STATUS CHECK")
    print("=" * 40)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
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
        
        # Get integration instance
        integration = get_redis_integration(redis_config, enable_optimizations=True)
        
        print("1. INTEGRATION STATUS")
        print("-" * 25)
        
        stats = integration.get_integration_stats()
        print(f"✅ Optimization Enabled: {stats['optimization_enabled']}")
        print(f"📊 Optimized Operations: {stats['optimized_operations']}")
        print(f"🔄 Legacy Operations: {stats['legacy_operations']}")
        print(f"🌐 Active Websocket Handlers: {stats['active_websocket_handlers']}")
        
        # Calculate optimization rate
        total_ops = stats['optimized_operations'] + stats['legacy_operations']
        if total_ops > 0:
            opt_rate = (stats['optimized_operations'] / total_ops) * 100
            print(f"📈 Optimization Rate: {opt_rate:.1f}%")
            
            if opt_rate >= 90:
                print("✅ Status: FULLY OPTIMIZED")
            elif opt_rate >= 50:
                print("⚠️ Status: PARTIALLY OPTIMIZED")
            else:
                print("❌ Status: MOSTLY LEGACY")
        else:
            print("⏳ Status: NO OPERATIONS YET")
        
        print("\n2. REDIS CLIENT CHECK")
        print("-" * 25)
        
        redis_client = integration.get_redis_client()
        client_type = type(redis_client).__name__
        print(f"Redis Client Type: {client_type}")
        
        if client_type == 'OptimizedRedisHelper':
            print("✅ Using OptimizedRedisHelper")
            
            # Check for optimized methods
            optimized_methods = [
                'update_ticker_data_optimized',
                'get_ticker_data_optimized', 
                'update_orderbook_data_optimized',
                'get_performance_stats'
            ]
            
            missing_methods = []
            for method in optimized_methods:
                if not hasattr(redis_client, method):
                    missing_methods.append(method)
            
            if not missing_methods:
                print("✅ All optimized methods available")
            else:
                print(f"⚠️ Missing methods: {missing_methods}")
                
        elif client_type == 'RedisHelper':
            print("⚠️ Using legacy RedisHelper")
            print("💡 Tip: Update to OptimizedRedisHelper for better performance")
        else:
            print(f"❓ Unknown client type: {client_type}")
        
        print("\n3. PERFORMANCE METRICS")
        print("-" * 25)
        
        if 'redis_performance' in stats:
            redis_stats = stats['redis_performance']
            print(f"Cache Hit Rate: {redis_stats['cache_hit_rate_percent']:.1f}%")
            print(f"Cache Size: {redis_stats['cache_size']} items")
            print(f"Total Redis Operations: {redis_stats['redis_operations']}")
            
            # Performance indicators
            hit_rate = redis_stats['cache_hit_rate_percent']
            if hit_rate >= 80:
                print("✅ Excellent cache performance")
            elif hit_rate >= 60:
                print("⚠️ Good cache performance")
            elif hit_rate >= 40:
                print("⚠️ Fair cache performance")
            else:
                print("❌ Poor cache performance")
        else:
            print("⏳ No performance data available yet")
        
        print("\n4. QUICK PERFORMANCE TEST")
        print("-" * 30)
        
        # Run quick benchmark
        print("Running 100-iteration benchmark...")
        start_time = time.time()
        
        try:
            for i in range(100):
                redis_client.update_ticker_data_optimized('TEST_EXCHANGE', f'SYM{i}', 100.0 + i, 1000.0, 1.5)
            
            for i in range(100):
                data = redis_client.get_ticker_data_optimized('TEST_EXCHANGE', f'SYM{i}')
            
            test_time = (time.time() - start_time) * 1000
            print(f"✅ Performance: {test_time:.1f}ms for 200 operations")
            print(f"⚡ Average: {test_time/200:.3f}ms per operation")
            
            if test_time < 50:
                print("✅ Excellent performance")
            elif test_time < 100:
                print("⚠️ Good performance") 
            else:
                print("❌ Slow performance - check system resources")
                
            # Cleanup test data
            redis_client.delete_all_exchange_stream_data('ticker', 'TEST_EXCHANGE')
            
        except AttributeError:
            print("❌ Optimized methods not available - using legacy fallback")
            print("💡 Check if OptimizedRedisHelper is properly imported")
        except Exception as e:
            print(f"❌ Performance test failed: {e}")
        
        print("\n5. HOW TO FORCE OPTIMIZATION")
        print("-" * 35)
        print("To ensure you're using optimized components:")
        print("1. Import: from etc.redis_connector.optimized_redis_helper import OptimizedRedisHelper")
        print("2. Use: redis_client = OptimizedRedisHelper()")
        print("3. Import: from etc.redis_connector.optimized_integration import get_redis_integration")
        print("4. Check logs for 'Using optimized' vs 'Falling back to legacy' messages")
        
        print("\n6. FALLBACK INDICATORS")
        print("-" * 25)
        print("You're using fallbacks if you see:")
        print("❌ 'Legacy Operations' count increasing")
        print("❌ 'RedisHelper' instead of 'OptimizedRedisHelper'")
        print("❌ Missing optimized methods in client")
        print("❌ Low optimization rate (<90%)")
        print("❌ Error messages about missing optimized functions")
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Optimized components may not be installed properly")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def monitor_fallbacks():
    """Monitor for fallback usage in real-time"""
    
    print("🔄 REAL-TIME FALLBACK MONITORING")
    print("=" * 40)
    print("Press Ctrl+C to stop monitoring")
    print()
    
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
        
        integration = get_redis_integration(redis_config)
        
        last_optimized = 0
        last_legacy = 0
        
        while True:
            stats = integration.get_integration_stats()
            current_optimized = stats['optimized_operations']
            current_legacy = stats['legacy_operations']
            
            # Check for changes
            if current_optimized > last_optimized:
                print(f"✅ {datetime.now().strftime('%H:%M:%S')} - Optimized operation detected")
                last_optimized = current_optimized
            
            if current_legacy > last_legacy:
                print(f"⚠️ {datetime.now().strftime('%H:%M:%S')} - Legacy fallback detected!")
                last_legacy = current_legacy
            
            time.sleep(5)  # Check every 5 seconds
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped")
    except Exception as e:
        print(f"❌ Monitoring failed: {e}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Check optimization status')
    parser.add_argument('--monitor', '-m', action='store_true', help='Monitor fallbacks in real-time')
    
    args = parser.parse_args()
    
    if args.monitor:
        monitor_fallbacks()
    else:
        check_optimization_status()