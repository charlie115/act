/**
 * Request deduplication for API calls
 */
export default class RequestDeduplicator {
  constructor() {
    this.pendingRequests = new Map();
  }
  
  async deduplicate(key, requestFn) {
    // If request is already pending, return the existing promise
    if (this.pendingRequests.has(key)) {
      return this.pendingRequests.get(key);
    }
    
    // Create new request promise
    const promise = requestFn().finally(() => {
      this.pendingRequests.delete(key);
    });
    
    this.pendingRequests.set(key, promise);
    return promise;
  }
  
  clear() {
    this.pendingRequests.clear();
  }
}