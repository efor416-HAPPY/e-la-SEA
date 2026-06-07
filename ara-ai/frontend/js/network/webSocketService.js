import { BackoffManager } from './backoffManager.js';

/**
 * 🔌 WebSocket Service
 * Manages the live connection to the backend `/ws` channel.
 * Handles automatic reconnects using exponential backoff.
 */
export class WebSocketService {
    constructor(wsUrl = 'ws://localhost:8080/ws') {
        this.wsUrl = wsUrl;
        this.ws = null;
        this.listeners = [];
        this.reconnectAttempts = 0;
        this.backoff = new BackoffManager();
        this.isConnecting = false;
        this.onStateChangeCallback = null;
    }

    /**
     * Set a callback to run when the connection state changes.
     * @param {Function} callback - Callback accepting (state)
     */
    onStateChange(callback) {
        this.onStateChangeCallback = callback;
    }

    /**
     * Add a message listener.
     * @param {Function} callback - Callback accepting (data)
     */
    addListener(callback) {
        this.listeners.push(callback);
    }

    /**
     * Remove a message listener.
     * @param {Function} callback
     */
    removeListener(callback) {
        this.listeners = this.listeners.filter(l => l !== callback);
    }

    /**
     * Establishes the WebSocket connection.
     */
    connect() {
        if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
            return;
        }

        this.isConnecting = true;
        this.notifyStateChange("CONNECTING");

        try {
            this.ws = new WebSocket(this.wsUrl);
        } catch (error) {
            this.handleError(error);
            return;
        }

        this.ws.onopen = () => {
            this.reconnectAttempts = 0;
            this.isConnecting = false;
            this.notifyStateChange("OPEN");
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.listeners.forEach(listener => listener(data));
            } catch (e) {
                console.error("Error parsing WebSocket message:", e);
            }
        };

        this.ws.onclose = (event) => {
            this.notifyStateChange("CLOSED");
            this.ws = null;
            this.scheduleReconnect();
        };

        this.ws.onerror = (error) => {
            this.handleError(error);
        };
    }

    /**
     * Fires state change callback.
     * @param {string} state - "CONNECTING", "OPEN", "CLOSED", "ERROR"
     */
    notifyStateChange(state) {
        if (this.onStateChangeCallback) {
            this.onStateChangeCallback(state);
        }
    }

    /**
     * Error logger.
     * @param {Error} error
     */
    handleError(error) {
        console.error("WebSocket error:", error);
        this.notifyStateChange("ERROR");
    }

    /**
     * Schedules a reconnect event.
     */
    scheduleReconnect() {
        this.isConnecting = false;
        this.reconnectAttempts++;
        const delay = this.backoff.getDelay(this.reconnectAttempts);
        console.log(`WebSocket disconnected. Reconnecting in ${delay / 1000}s (Attempt ${this.reconnectAttempts})`);
        
        // Notify of reconnection attempts through state change callback
        this.notifyStateChange(`RECONNECTING_IN_${Math.round(delay/1000)}S`);
        
        setTimeout(() => {
            this.connect();
        }, delay);
    }

    /**
     * Closes the connection.
     */
    disconnect() {
        if (this.ws) {
            this.ws.onclose = null; // Prevent reconnect scheduling
            this.ws.close();
            this.ws = null;
        }
    }
}
