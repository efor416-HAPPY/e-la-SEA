/**
 * 📈 Backoff Manager
 * Computes exponential backoff intervals for reconnects to prevent network spam.
 */
export class BackoffManager {
    constructor(baseDelay = 1000, maxDelay = 30000) {
        this.baseDelay = baseDelay;
        this.maxDelay = maxDelay;
    }

    /**
     * Calculates delay in milliseconds based on current retries.
     * Formula: min(2^retries * baseDelay, maxDelay)
     * @param {number} retries - Number of current retry attempts
     * @returns {number} Delay in milliseconds
     */
    getDelay(retries) {
        const delay = Math.pow(2, retries) * this.baseDelay;
        return Math.min(delay, this.maxDelay);
    }
}
