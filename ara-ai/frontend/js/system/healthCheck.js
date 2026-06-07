/**
 * 🩺 Health Check
 * Monitors network connectivity (Online/Offline) and computes server API latency.
 */
export class HealthCheck {
    constructor(apiBase = 'http://localhost:8080') {
        this.apiBase = apiBase;
        this.status = "UNKNOWN";
        this.latency = 0;
    }

    /**
     * Measures response latency of the backend API.
     * Updates internal connectivity status badge.
     * @returns {Promise<Object>} Status and latency metadata
     */
    async measureLatency() {
        const start = performance.now();
        try {
            // Request system metrics endpoint as a lightweight ping
            const res = await fetch(`${this.apiBase}/api/system`, { 
                method: 'GET',
                headers: { 'Cache-Control': 'no-cache' }
            });
            this.latency = Math.round(performance.now() - start);
            this.status = res.ok ? "ONLINE" : "DEGRADED";
        } catch (e) {
            this.latency = Infinity;
            this.status = "OFFLINE";
        }
        return { status: this.status, latency: this.latency };
    }

    getStatus() {
        return this.status;
    }

    getLatency() {
        return this.latency;
    }
}
