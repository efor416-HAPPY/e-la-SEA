/**
 * 🌐 Fetch Service
 * Wraps asynchronous HTTP requests (GET, POST) to the FastAPI backend.
 */
export class FetchService {
    constructor(apiBase = 'http://localhost:8080') {
        this.apiBase = apiBase;
    }

    /**
     * Common request handler
     * @param {string} endpoint - API path (e.g. '/api/system')
     * @param {Object} [options] - Fetch configurations
     * @returns {Promise<any>} Response JSON data
     */
    async request(endpoint, options = {}) {
        const url = `${this.apiBase}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        const config = {
            ...options,
            headers
        };

        const response = await fetch(url, config);
        if (!response.ok) {
            throw new Error(`HTTP Error: ${response.status} ${response.statusText}`);
        }
        return await response.json();
    }

    /**
     * Send GET request
     * @param {string} endpoint - API path
     * @returns {Promise<any>}
     */
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    /**
     * Send POST request
     * @param {string} endpoint - API path
     * @param {Object} body - Request body payload
     * @returns {Promise<any>}
     */
    async post(endpoint, body) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(body)
        });
    }
}
