/**
 * 💵 Economy Agent
 * Queries financial archives and currency rates.
 */
export class EconomyAgent {
    constructor(fetchService, cacheManager) {
        this.fetchService = fetchService;
        this.cacheManager = cacheManager;
    }

    /**
     * Gets market indicators from wisdom database.
     * @returns {Promise<Array>} Economic indicators
     */
    async getMarketSummary() {
        const cacheKey = 'economy_summary';
        const cached = this.cacheManager.get(cacheKey);
        if (cached) return cached;

        try {
            const items = await this.fetchService.get('/api/brain/wisdom');
            const filtered = items.filter(item => 
                item.source === 'EconomyAgent' || 
                item.source === 'Economy' ||
                item.source === 'Finance'
            );
            this.cacheManager.set(cacheKey, filtered, 180000); // 3 minutes TTL
            return filtered;
        } catch (e) {
            console.error("EconomyAgent: Failed to fetch market summaries", e);
            return [];
        }
    }
}
