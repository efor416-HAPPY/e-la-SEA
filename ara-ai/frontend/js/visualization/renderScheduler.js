/**
 * ⏰ Render Scheduler
 * Coordinates visual drawings using requestAnimationFrame loops for canvas operations.
 */
export class RenderScheduler {
    constructor() {
        this.tasks = new Map();
        this.isRunning = false;
        this.frameId = null;
    }

    /**
     * Add a task to the render loop.
     * @param {string} name - Unique name of the task
     * @param {Function} taskFn - Function called every frame: taskFn(timestamp, dt)
     */
    addTask(name, taskFn) {
        this.tasks.set(name, taskFn);
        this.start();
    }

    /**
     * Remove a task from the loop.
     * @param {string} name
     */
    removeTask(name) {
        this.tasks.delete(name);
        if (this.tasks.size === 0) {
            this.stop();
        }
    }

    /**
     * Starts the animation loop.
     */
    start() {
        if (this.isRunning) return;
        this.isRunning = true;
        
        let lastTime = performance.now();
        
        const loop = (timestamp) => {
            if (!this.isRunning) return;
            const dt = (timestamp - lastTime) / 1000;
            lastTime = timestamp;

            this.tasks.forEach((taskFn, name) => {
                try {
                    taskFn(timestamp, dt);
                } catch (e) {
                    console.error(`Error executing render task "${name}":`, e);
                }
            });

            this.frameId = requestAnimationFrame(loop);
        };

        this.frameId = requestAnimationFrame(loop);
    }

    /**
     * Stops the animation loop.
     */
    stop() {
        this.isRunning = false;
        if (this.frameId) {
            cancelAnimationFrame(this.frameId);
            this.frameId = null;
        }
    }
}
