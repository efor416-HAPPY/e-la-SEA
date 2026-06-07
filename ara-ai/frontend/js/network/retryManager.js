import { BackoffManager } from './backoffManager.js';

/**
 * 🔁 Retry Manager
 * Controls connection and operation retries with exponential backoff.
 */
export class RetryManager {
    constructor(maxRetries = Infinity, baseDelay = 1000, maxDelay = 30000) {
        this.maxRetries = maxRetries;
        this.backoff = new BackoffManager(baseDelay, maxDelay);
    }

    /**
     * Executes an async operation, retrying if it fails.
     * @param {Function} operation - Async function to run
     * @param {Function} [onRetry] - Callback invoked when a retry is scheduled
     * @returns {Promise<any>} Result of the operation
     */
    async retry(operation, onRetry = null) {
        let retries = 0;
        while (true) {
            try {
                return await operation();
            } catch (error) {
                retries++;
                if (retries >= this.maxRetries) {
                    throw error;
                }
                const delay = this.backoff.getDelay(retries);
                if (onRetry) {
                    onRetry(retries, delay, error);
                }
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
    }
}
