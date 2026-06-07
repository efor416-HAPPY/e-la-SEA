/**
 * 📰 News Agent
 * Manages technology and environmental news feed fetches, utilizing local caching.
 */
export class NewsAgent {
    constructor(fetchService, cacheManager) {
        this.fetchService = fetchService;
        this.cacheManager = cacheManager;
    }

    /**
     * Gets news archives, filtering and caching responses.
     * @returns {Promise<Array>} News feed items
     */
    async getNewsFeeds() {
        const cacheKey = 'wisdom_news';
        const cached = this.cacheManager.get(cacheKey);
        if (cached) return cached;

        try {
            const items = await this.fetchService.get('/api/brain/wisdom');
            // Filter news-related or RSS entries
            const filtered = items.filter(item => 
                item.source === 'NewsAgent' || 
                item.source === 'RSS' || 
                item.source === 'NaverBlog' ||
                item.source === 'NASA APOD'
            );
            this.cacheManager.set(cacheKey, filtered, 120000); // 2 minutes cache TTL
            return filtered;
        } catch (e) {
            console.error("NewsAgent: Failed to load news feeds", e);
            return [];
        }
    }
}
