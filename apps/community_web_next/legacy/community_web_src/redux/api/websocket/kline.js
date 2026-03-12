import isEqual from 'lodash/isEqual';
import websocketApi from 'redux/api/websocket';

// import { DateTime } from 'luxon';

// import { DATE_FORMAT_API_QUERY } from 'constants';

const api = websocketApi.injectEndpoints({
  endpoints: (build) => ({
    getRealTimeKline: build.query({
      keepUnusedDataFor: 1,
      queryFn: () => ({ data: {} }),
      onCacheEntryAdded: async (
        args,
        { cacheDataLoaded, cacheEntryRemoved, updateCachedData }
      ) => {
        const url = new URL(`${process.env.REACT_APP_DRF_WS_URL}/kline/`);
        url.searchParams.set('target_market_code', args.targetMarketCode);
        url.searchParams.set('origin_market_code', args.originMarketCode);
        url.searchParams.set('interval', args.interval);
        if (args.baseAsset) {
          url.searchParams.set('base_asset', args.baseAsset);
        }
        
        // Track connection state
        let isConnecting = false;
        let reconnectAttempts = 0;
        let socket = null;
        let heartbeatInterval = null;
        let lastMessageTime = 0;
        let activelyClosing = false;
        
        // Declare connectWebSocket function first (but don't implement it yet)
        let connectWebSocket;
        
        const startHeartbeat = () => {
          // Clear any existing heartbeat interval
          if (heartbeatInterval) {
            clearInterval(heartbeatInterval);
          }
          
          // Record current time as last message time
          lastMessageTime = Date.now();
          
          // Check connection health every 15 seconds
          heartbeatInterval = setInterval(() => {
            const currentTime = Date.now();
            // If no message received for 45 seconds, connection is likely dead
            if (currentTime - lastMessageTime > 45000 && socket && socket.readyState === WebSocket.OPEN) {
              // Force close and reconnect
              activelyClosing = true;
              socket.close();
            }
          }, 15000);
        };
        
        const stopHeartbeat = () => {
          if (heartbeatInterval) {
            clearInterval(heartbeatInterval);
            heartbeatInterval = null;
          }
        };
        
        // Coalesce websocket snapshots so the UI always applies the latest state,
        // instead of trying to replay every full-table snapshot.
        const latestUpdates = new Map();
        let updateTimeout = null;
        const FLUSH_INTERVAL_MS = 100;

        const flushUpdates = () => {
          if (latestUpdates.size === 0) return;
          const updatesToApply = Array.from(latestUpdates.values());
          latestUpdates.clear();
          updateTimeout = null;
          
          updateCachedData((draft) => {
            // Clear the disconnected flag if it exists
            if (draft.disconnected) {
              delete draft.disconnected;
            }
            
            // Apply only the newest snapshot per asset.
            updatesToApply.forEach((item) => {
              if (!(item.base_asset in draft)) draft[item.base_asset] = {};
              if (!isEqual(item, draft[item.base_asset]))
                draft[item.base_asset] = item;
            });
          });
        };
        
        // Message handler with batching
        const onMessage = (event) => {
          // Update last message time on any message
          lastMessageTime = Date.now();
          
          const message = JSON.parse(event.data);
          try {
            if (message.type === 'connect') return;

            const result = JSON.parse(message.result);
            if (!Array.isArray(result)) return;

            result.forEach((item) => {
              // Convert datetime_now from seconds to milliseconds
              if (typeof item.datetime_now === 'number' && item.datetime_now < 1e12) {
                item.datetime_now *= 1000;
              }
              if (item?.base_asset) {
                latestUpdates.set(item.base_asset, item);
              }
            });
            
            // Apply on a fixed cadence so rendering doesn't fall behind.
            if (!updateTimeout) {
              updateTimeout = setTimeout(flushUpdates, FLUSH_INTERVAL_MS);
            }
          } catch {
            /* empty */
          }
        };

        // Handle connection close with reconnection logic
        const onClose = () => {
          isConnecting = false;
          
          // Only set disconnected state if this wasn't a clean close during cleanup
          if (!activelyClosing) {
            // Set disconnected state for UI feedback
            updateCachedData((draft) => {
              Object.keys(draft).forEach((key) => {
                if (key !== 'disconnected') delete draft[key];
              });
              draft.disconnected = true;
            });
            
            // Implement exponential backoff
            const maxReconnectDelay = 30000; // 30 seconds max
            const baseDelay = 500; // Start with 0.5 seconds
            const delay = Math.min(
              maxReconnectDelay,
              baseDelay * (1.5 ** reconnectAttempts)
            );
            
            reconnectAttempts += 1;
            setTimeout(() => connectWebSocket(), delay);
          }
          activelyClosing = false;
        };
        
        const onError = () => {
          if (socket && socket.readyState !== WebSocket.CLOSED) {
            activelyClosing = true;
            socket.close(); // Will trigger the close handler with reconnection logic
          }
        };

        // Handle visibility change
        const handleVisibilityChange = () => {
          if (document.visibilityState === 'hidden') {
            // Store connection state when page becomes hidden
            // Don't close the websocket when page is hidden
          } else if (document.visibilityState === 'visible') {
            // Only reconnect if the connection was actually lost
            // We check if the socket is closed/closing OR if it's been more than 45s since we got a message
            const currentTime = Date.now();
            const needsReconnect = 
              !socket || 
              socket.readyState === WebSocket.CLOSED || 
              socket.readyState === WebSocket.CLOSING ||
              (currentTime - lastMessageTime > 45000);
            
            if (needsReconnect) {
              // If we still have a socket, close it properly first
              if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
                activelyClosing = true;
                socket.close();
              }
              // Then reconnect
              connectWebSocket();
            }
          }
        };

        // Now implement the connectWebSocket function
        connectWebSocket = () => {
          if (isConnecting) return;
          isConnecting = true;
          
          // Clear any "disconnected" state when attempting to connect
          updateCachedData((draft) => {
            if (draft.disconnected) delete draft.disconnected;
          });
          
          // Create new WebSocket connection
          socket = new WebSocket(url.toString());
          
          socket.addEventListener('open', () => {
            isConnecting = false;
            reconnectAttempts = 0; // Reset attempts on successful connection
            startHeartbeat(); // Start heartbeat monitoring when connected
          });
          
          socket.addEventListener('message', onMessage);
          socket.addEventListener('close', onClose);
          socket.addEventListener('error', onError);
        };
        
        // Set up visibility change listener
        document.addEventListener('visibilitychange', handleVisibilityChange);
        
        // Start initial connection
        connectWebSocket();
        
        try {
          await cacheDataLoaded;
        } catch {
          // no-op in case `cacheEntryRemoved` resolves before `cacheDataLoaded`,
          // in which case `cacheDataLoaded` will throw
        }
        
        // Clean up on component unmount or query deactivation
        await cacheEntryRemoved;
        
        // Flush any pending updates before cleanup
        if (updateTimeout) {
          clearTimeout(updateTimeout);
          flushUpdates();
        }
        
        // Remove visibility change listener
        document.removeEventListener('visibilitychange', handleVisibilityChange);
        
        stopHeartbeat(); // Stop heartbeat monitoring
        if (socket) {
          // Set flag to indicate we're actively closing this connection
          activelyClosing = true;
          // Remove event listeners to prevent memory leaks
          socket.removeEventListener('message', onMessage);
          socket.removeEventListener('close', onClose);
          socket.removeEventListener('error', onError);
          socket.close();
          socket = null;
        }
      },
    }),
  }),
});

export default api;
export const { useGetRealTimeKlineQuery } = api;
