/**
 * Optimized data structure for fast lookups and updates
 */
export default class OptimizedDataStore {
  constructor() {
    this.data = new Map();
    this.sortedKeys = [];
    this.isDirty = false;
  }
  
  update(key, value) {
    const existing = this.data.get(key);
    
    // Only update if value actually changed
    if (JSON.stringify(existing) !== JSON.stringify(value)) {
      this.data.set(key, value);
      this.isDirty = true;
    }
  }
  
  batchUpdate(updates) {
    updates.forEach(({ key, value }) => this.update(key, value));
  }
  
  getSortedArray(sortKey = 'atp24h', order = 'desc') {
    if (this.isDirty) {
      const array = Array.from(this.data.values());
      array.sort((a, b) => {
        const aVal = a[sortKey] || 0;
        const bVal = b[sortKey] || 0;
        return order === 'desc' ? bVal - aVal : aVal - bVal;
      });
      this.sortedKeys = array.map(item => item.base_asset);
      this.isDirty = false;
      return array;
    }
    
    // Return cached sorted array
    return this.sortedKeys.map(key => this.data.get(key));
  }
  
  get(key) {
    return this.data.get(key);
  }
  
  has(key) {
    return this.data.has(key);
  }
  
  get size() {
    return this.data.size;
  }
  
  clear() {
    this.data.clear();
    this.sortedKeys = [];
    this.isDirty = false;
  }
}