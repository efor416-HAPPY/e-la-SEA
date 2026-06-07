/**
 * 📥 Queue Manager
 * Manages message and sensory queues (FIFO buffers) to throttle rendering/processing rates.
 */
export class QueueManager {
    constructor() {
        this.queue = [];
    }

    /**
     * Pushes an item to the end of the queue.
     * @param {any} item
     */
    enqueue(item) {
        this.queue.push(item);
    }

    /**
     * Removes and returns the first item from the queue.
     * @returns {any}
     */
    dequeue() {
        return this.queue.shift();
    }

    /**
     * Returns the first item without removing it.
     * @returns {any}
     */
    peek() {
        return this.queue[0];
    }

    /**
     * Checks if the queue is empty.
     * @returns {boolean}
     */
    isEmpty() {
        return this.queue.length === 0;
    }

    /**
     * Returns the number of items in the queue.
     * @returns {number}
     */
    size() {
        return this.queue.length;
    }

    /**
     * Clears all items in the queue.
     */
    clear() {
        this.queue = [];
    }
}
