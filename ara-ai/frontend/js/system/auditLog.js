/**
 * 📝 Audit Log
 * Standardizes log entries, categorizing system operations to console streams and logs.
 */
export class AuditLog {
    constructor(maxEntries = 100) {
        this.maxEntries = maxEntries;
        this.logs = [];
    }

    /**
     * Records a system event.
     * @param {string} type - Event category (e.g. 'NETWORK', 'SECURITY', 'DATA')
     * @param {string} detail - Detailed explanation of the event
     * @param {'INFO'|'WARN'|'ERROR'|'SUCCESS'} [status='INFO'] - Log status level
     */
    log(type, detail, status = "INFO") {
        const logEntry = {
            timestamp: new Date().toISOString(),
            type,
            detail,
            status
        };
        this.logs.push(logEntry);
        
        // Evict oldest logs if max size is exceeded
        if (this.logs.length > this.maxEntries) {
            this.logs.shift();
        }

        // Print to console using a standard format
        console.log(`[AUDIT] [${logEntry.timestamp}] [${status}] [${type}] ${detail}`);
    }

    /**
     * Retrieve all active log entries.
     * @returns {Array}
     */
    getLogs() {
        return this.logs;
    }

    /**
     * Clears local log store.
     */
    clear() {
        this.logs = [];
    }
}
