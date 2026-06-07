/**
 * 💾 Cache Manager
 * Manages local storage caching for directory lists, search results, and agent responses.
 */
export class CacheManager {
    constructor(prefix = 'ara_cache_') {
        this.prefix = prefix;
    }

    /**
     * Store item in cache.
     * @param {string} key - Cache identifier
     * @param {any} value - Data to cache
     * @param {number} [ttlMs=600000] - Time to live in milliseconds (default: 10 mins)
     */
    set(key, value, ttlMs = 600000) {
        const cacheEntry = {
            value,
            expiry: Date.now() + ttlMs
        };
        try {
            localStorage.setItem(this.prefix + key, JSON.stringify(cacheEntry));
        } catch (e) {
            console.warn("Storage quota exceeded, unable to cache item:", key);
        }
    }

    /**
     * Retrieve item from cache. Returns null if expired or missing.
     * @param {string} key
     * @returns {any|null}
     */
    get(key) {
        const fullKey = this.prefix + key;
        const data = localStorage.getItem(fullKey);
        if (!data) return null;

        try {
            const cacheEntry = JSON.parse(data);
            if (Date.now() > cacheEntry.expiry) {
                localStorage.removeItem(fullKey);
                return null;
            }
            return cacheEntry.value;
        } catch (e) {
            localStorage.removeItem(fullKey);
            return null;
        }
    }

    /**
     * Remove cache key.
     * @param {string} key
     */
    remove(key) {
        localStorage.removeItem(this.prefix + key);
    }

    /**
     * Clear all cached items matching this prefix.
     */
    clear() {
        Object.keys(localStorage).forEach(key => {
            if (key.startsWith(this.prefix)) {
                localStorage.removeItem(key);
            }
        });
    }
}
