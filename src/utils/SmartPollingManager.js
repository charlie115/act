/**
 * Smart polling manager to reduce unnecessary API calls
 */
export default class SmartPollingManager {
  constructor() {
    this.intervals = new Map();
    this.lastFetchTimes = new Map();
  }
  
  shouldFetch(key, minInterval = 60000) {
    const lastFetch = this.lastFetchTimes.get(key) || 0;
    const now = Date.now();
    
    if (now - lastFetch >= minInterval) {
      this.lastFetchTimes.set(key, now);
      return true;
    }
    
    return false;
  }
  
  startPolling(key, callback, interval) {
    this.stopPolling(key);
    
    const intervalId = setInterval(() => {
      if (this.shouldFetch(key, interval)) {
        callback();
      }
    }, interval);
    
    this.intervals.set(key, intervalId);
  }
  
  stopPolling(key) {
    const intervalId = this.intervals.get(key);
    if (intervalId) {
      clearInterval(intervalId);
      this.intervals.delete(key);
    }
  }
  
  stopAll() {
    this.intervals.forEach(intervalId => clearInterval(intervalId));
    this.intervals.clear();
    this.lastFetchTimes.clear();
  }
}