/**
 * 📊 Chart Manager
 * Renders the neural connection nodes on the `brain-neuron-canvas` and
 * the haptic audio waveforms on the `audio-waveform` canvas.
 */
export class ChartManager {
    /**
     * Draws the neural network network canvas.
     * @param {CanvasRenderingContext2D} ctx - Target 2D rendering context
     * @param {HTMLCanvasElement} canvas - Target canvas element
     * @param {Array} nodes - Array of neural node objects
     * @param {Array} connections - Array of connection link objects
     * @param {Array} pulses - Array of flow signal pulse objects
     */
    drawNeuralNetwork(ctx, canvas, nodes, connections, pulses) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Render branch lines
        connections.forEach(conn => {
            const fromNode = nodes[conn.from];
            const toNode = nodes[conn.to];
            if (!fromNode || !toNode) return;
            ctx.beginPath();
            ctx.moveTo(fromNode.x, fromNode.y);
            ctx.lineTo(toNode.x, toNode.y);
            ctx.strokeStyle = `rgba(61, 102, 78, ${0.1 + (fromNode.glow + toNode.glow) * 0.15})`;
            ctx.lineWidth = 1.0 + (fromNode.glow + toNode.glow) * 1.5;
            ctx.stroke();
        });

        // Render signal pulses
        pulses.forEach(p => {
            const x = p.startX + (p.endX - p.startX) * p.progress;
            const y = p.startY + (p.endY - p.startY) * p.progress;
            ctx.fillStyle = p.color || 'rgba(61, 102, 78, 0.8)';
            ctx.beginPath();
            ctx.arc(x, y, 3, 0, Math.PI * 2);
            ctx.fill();
        });

        // Render neural nodes
        nodes.forEach(node => {
            ctx.fillStyle = node.glow > 0.5 ? '#E4D9C6' : '#86A890';
            ctx.beginPath();
            ctx.arc(node.x, node.y, node.size, 0, Math.PI * 2);
            ctx.fill();

            // Render text label
            ctx.fillStyle = 'rgba(31, 45, 37, 0.85)';
            ctx.font = 'bold 9px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(node.label, node.x, node.y - node.size - 6);
        });
    }

    /**
     * Draws the live sound level audio waveforms.
     * @param {CanvasRenderingContext2D} ctx - Target 2D rendering context
     * @param {HTMLCanvasElement} canvas - Target canvas element
     * @param {Uint8Array} dataArray - Frequency time-domain data
     * @param {number} bufferLength - Length of data buffer
     */
    drawAudioWaveform(ctx, canvas, dataArray, bufferLength) {
        // Auto-fit parent client width
        if (canvas.parentNode) {
            canvas.width = canvas.parentNode.clientWidth || canvas.width;
            canvas.height = canvas.parentNode.clientHeight || canvas.height;
        }

        ctx.fillStyle = '#F2ECE1';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        ctx.lineWidth = 2;
        ctx.strokeStyle = '#3D664E';
        ctx.beginPath();

        const sliceWidth = (canvas.width * 1.0) / bufferLength;
        let x = 0;

        for (let i = 0; i < bufferLength; i++) {
            const v = dataArray[i] / 128.0;
            const y = (v * canvas.height) / 2;

            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
            x += sliceWidth;
        }

        ctx.lineTo(canvas.width, canvas.height / 2);
        ctx.stroke();
    }
}
