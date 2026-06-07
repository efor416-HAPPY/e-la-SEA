/**
 * 🎥 YouTube Agent
 * Manages media playlists and constructs embedded iframe URLs.
 */
export class YouTubeAgent {
    constructor(fetchService, cacheManager) {
        this.fetchService = fetchService;
        this.cacheManager = cacheManager;
    }

    /**
     * Retrieves YouTube archives from brain wisdom database.
     * @returns {Promise<Array>} YouTube playlist items
     */
    async getPlaylists() {
        const cacheKey = 'youtube_playlists';
        const cached = this.cacheManager.get(cacheKey);
        if (cached) return cached;

        try {
            const items = await this.fetchService.get('/api/brain/wisdom');
            const filtered = items.filter(item => 
                item.source === 'YoutubeAgent' || 
                item.source === 'YouTube' ||
                item.title.toLowerCase().includes('youtube')
            );
            this.cacheManager.set(cacheKey, filtered, 300000); // 5 minutes TTL
            return filtered;
        } catch (e) {
            console.error("YouTubeAgent: Failed to fetch playlist archives", e);
            return [];
        }
    }

    /**
     * Constructs iframe embed URL.
     * @param {string} videoId 
     * @returns {string} Embed URL
     */
    createEmbedUrl(videoId) {
        return `https://www.youtube.com/embed/${videoId}`;
    }
}
