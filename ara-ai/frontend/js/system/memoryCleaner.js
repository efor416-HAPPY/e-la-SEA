/**
 * 🧹 Memory Cleaner
 * Prunes large arrays (sensory buffers, chat logs) and cleans hardware stream references to prevent page crashes.
 */
export class MemoryCleaner {
    constructor(auditLog) {
        this.auditLog = auditLog;
    }

    /**
     * Cleans up media stream track references.
     * @param {MediaStream} stream - Target media stream to release
     * @returns {null}
     */
    cleanStream(stream) {
        if (stream) {
            try {
                stream.getTracks().forEach(track => {
                    track.stop();
                    this.auditLog.log("MEMORY_CLEANER", `Stopped media stream track: ${track.label}`, "INFO");
                });
                this.auditLog.log("MEMORY_CLEANER", "Hardware stream references successfully released.", "SUCCESS");
            } catch (e) {
                console.error("Error closing stream tracks:", e);
            }
        }
        return null;
    }

    /**
     * Trims arrays to maintain low browser RAM usage.
     * @param {Array} array - Target array to trim
     * @param {number} [maxSize=50] - Threshold count
     * @returns {Array} Trimmed array reference
     */
    pruneArray(array, maxSize = 50) {
        if (array && array.length > maxSize) {
            const evictedCount = array.length - maxSize;
            array.splice(0, evictedCount);
            this.auditLog.log("MEMORY_CLEANER", `Evicted ${evictedCount} memory records to prevent memory overflow.`, "INFO");
        }
        return array;
    }
}
