/**
 * 🔀 Merge Engine
 * Syncs and merges remote API responses with local cached data.
 */
export class MergeEngine {
    /**
     * Merges remote items with local items based on a unique key.
     * Remote items overwrite local items if there's a key collision.
     * @param {Array} remoteItems - Data array from server API
     * @param {Array} localItems - Data array from local storage cache
     * @param {string} [uniqueKey='name'] - Property name used for deduplication (e.g. 'name', 'title', 'id')
     * @returns {Array} Unified list of merged items
     */
    merge(remoteItems = [], localItems = [], uniqueKey = 'name') {
        const itemMap = new Map();
        
        // Populate local items first
        if (Array.isArray(localItems)) {
            localItems.forEach(item => {
                if (item && item[uniqueKey]) {
                    itemMap.set(item[uniqueKey], item);
                }
            });
        }

        // Remote items override local ones
        if (Array.isArray(remoteItems)) {
            remoteItems.forEach(item => {
                if (item && item[uniqueKey]) {
                    itemMap.set(item[uniqueKey], item);
                }
            });
        }

        return Array.from(itemMap.values());
    }
}
