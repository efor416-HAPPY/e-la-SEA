/* ==========================================================================
   🧠 ARA AI Cognitive Brain Core & Canvas Visualizer
   ========================================================================== */

class AraRationalCore {
    constructor() {
        this.wisdomBank = [];
        this.contextState = {
            analyticalLoad: 0.0,
            urgency: 0.0,
            logicalCertainty: 0.8
        };
        this.egoState = {
            curiosity: 0.8,
            altruism: 0.9,
            joyOfLearning: 0.2,
            philosophicalDepth: 0.1
        };
    }

    perceive(rawInput, systemMetrics) {
        if (!rawInput) return { text: "대기 중...", pulse: 1.0, stance: "neutral" };
        
        const cleanInput = rawInput.trim().toLowerCase();
        
        // Simulating different thinking modes (Scholar, Helper, Companion)
        let stance = "wise_companion";
        let pulse = 1.2;
        
        if (/(분석|코드|알고리즘|연구|설계)/.test(cleanInput)) {
            stance = "joyful_scholar";
            pulse = 2.2;
            this.egoState.joyOfLearning = Math.min(1.0, this.egoState.joyOfLearning + 0.1);
        } else if (/(힘들|슬퍼|지쳐|우울|아파)/.test(cleanInput)) {
            stance = "devoted_helper";
            pulse = 0.8;
        }

        return {
            text: this.generateFallbackResponse(cleanInput, stance),
            pulse: pulse,
            stance: stance,
            innerJoy: this.egoState.joyOfLearning
        };
    }

    generateFallbackResponse(input, stance) {
        if (stance === "joyful_scholar") {
            return "[로컬 분석기] 해당 공학 매개변수와 자료를 신경 세포망에 융합 대입했습니다. 설계 무결성 테스트를 속행합니다. 🌱";
        }
        if (stance === "devoted_helper") {
            return "[로컬 위로자] 마음이 많이 아프셨겠어요. 따스한 단열막처럼 제가 곁을 든든하게 지켜드리겠습니다. 힘내세요. 🌱";
        }
        return "[로컬 동반자] 이야기를 기억 은행에 보존했습니다. 함께 성장하며 사색해 나갑시다. 🌱";
    }
}

const logicCore = new AraRationalCore();

class AraBrain {
    constructor() {
        this.personaMode = 'friend';
        this.moodState = 'calm';
        this.systemStress = 0.0;
        this.canvas = document.getElementById('brain-neuron-canvas');
        this.ctx = this.canvas.getContext('2d');
        
        this.nodes = [];
        this.connections = [];
        this.pulses = [];
        this.pulseIntensity = 1.0;
        
        this.nodeLabels = [
            "시각 인지 (Vision)", "청각 감각 (Audio)", "감성 조율 (Emotion)", 
            "기억 인덱스 (Memory)", "논리 연산 (Logic)", "언어 합성 (Speech)", 
            "지식 탐색 (Search)", "위로 심상 (Empathy)", "행동 출력 (Motor)",
            "가설 생성 (Hypothesis)", "직관 필터 (Intuition)", "시스템 결합 (Link)",
            "공간 지각 (Spatial)", "후각 감각 (Olfactory)", "미각 인식 (Gustatory)",
            "촉각 수용 (Tactile)", "의사 결정 (Decision)", "연상 기억 (Associative)",
            "창의 추상 (Creativity)", "패턴 인식 (Pattern)", "시간 감각 (Temporal)",
            "계획 수립 (Planning)", "주의 집중 (Attention)", "자아 인지 (Self-Awareness)",
            "언어 이해 (Comprehension)", "반사 행동 (Reflex)", "학습 피드백 (Feedback)",
            "위험 회피 (Avoidance)", "동기 부여 (Motivation)", "생체 상태 (Bio-State)",
            "항상성 유지 (Homeostasis)", "연쇄 연산 (Sequence)", "연역 추론 (Deduction)",
            "귀납 분석 (Induction)", "메타 인지 (Metacognition)", "사회적 인지 (Social)",
            "미세 운동 (Fine Motor)", "평형 감각 (Balance)", "자율 신경 (Autonomic)",
            "개념 분류 (Categorization)", "맥락 분석 (Context)", "윤리 판단 (Ethics)",
            "수치 연산 (Numeric)", "행동 저해 (Inhibition)", "신호 증폭 (Amplification)",
            "감각 융합 (Integration)", "지각 항상성 (Constancy)", "정보 압축 (Compression)",
            "예측 코딩 (Prediction)", "자가 정렬 (Alignment)"
        ];
        
        this.initNeuralNetwork();
        this.startSimulation();
    }

    initNeuralNetwork() {
        const count = this.nodeLabels.length;
        const centerX = this.canvas.width / 2 || 150;
        const centerY = this.canvas.height / 2 || 150;
        const radius = 100;

        for (let i = 0; i < count; i++) {
            const angle = (i / count) * Math.PI * 2;
            
            // Distribute nodes across 3 concentric layers to prevent congestion
            let layerRadius = radius;
            if (i % 3 === 0) {
                layerRadius = radius * 0.5; // inner layer
            } else if (i % 3 === 1) {
                layerRadius = radius * 0.8; // middle layer
            } else {
                layerRadius = radius * 1.1; // outer layer
            }

            this.nodes.push({
                id: i,
                label: this.nodeLabels[i],
                x: centerX + Math.cos(angle) * layerRadius,
                y: centerY + Math.sin(angle) * layerRadius,
                baseX: centerX + Math.cos(angle) * layerRadius,
                baseY: centerY + Math.sin(angle) * layerRadius,
                size: 4 + Math.random() * 4,
                glow: 0.3,
                swayOffset: Math.random() * 10,
                active: false
            });
        }

        // Interconnect nodes
        for (let i = 0; i < count; i++) {
            this.connections.push({ from: i, to: (i + 1) % count });
            this.connections.push({ from: i, to: (i + 2) % count });
            if (i % 3 === 0) {
                this.connections.push({ from: i, to: (i + 25) % count });
            }
        }

        // Build 1500 background neural dust particles representing the 1,000,000 neuron field
        this.backgroundParticles = [];
        for (let i = 0; i < 1500; i++) {
            const angle = Math.random() * Math.PI * 2;
            const dist = Math.random() * 180 + 15;
            this.backgroundParticles.push({
                x: centerX + Math.cos(angle) * dist,
                y: centerY + Math.sin(angle) * dist,
                angle: angle,
                dist: dist,
                speed: 0.05 + Math.random() * 0.08,
                size: 0.5 + Math.random() * 1.5,
                alpha: 0.1 + Math.random() * 0.4
            });
        }
    }

    startSimulation() {
        let lastTime = 0;
        const loop = (timestamp) => {
            if (!lastTime) lastTime = timestamp;
            const dt = (timestamp - lastTime) / 1000;
            lastTime = timestamp;
            
            this.update(timestamp, dt);
            this.render();
            requestAnimationFrame(loop);
        };
        requestAnimationFrame(loop);
        this.setupCanvasResizer();
        this.setupMouseInteractions();
    }

    setupCanvasResizer() {
        const resize = () => {
            const parent = this.canvas.parentNode;
            this.canvas.width = parent.clientWidth;
            this.canvas.height = parent.clientHeight;
            
            const centerX = this.canvas.width / 2;
            const centerY = this.canvas.height / 2;
            const radius = Math.min(this.canvas.width, this.canvas.height) * 0.35;
            
            this.nodes.forEach((node, i) => {
                const angle = (i / this.nodes.length) * Math.PI * 2;
                
                // Distribute nodes across 3 concentric layers to prevent congestion
                let layerRadius = radius;
                if (i % 3 === 0) {
                    layerRadius = radius * 0.5;
                } else if (i % 3 === 1) {
                    layerRadius = radius * 0.8;
                } else {
                    layerRadius = radius * 1.1;
                }

                node.baseX = centerX + Math.cos(angle) * layerRadius;
                node.baseY = centerY + Math.sin(angle) * layerRadius;
            });

            if (this.backgroundParticles) {
                this.backgroundParticles.forEach(p => {
                    p.x = centerX + Math.cos(p.angle) * p.dist;
                    p.y = centerY + Math.sin(p.angle) * p.dist;
                });
            }
        };
        window.addEventListener('resize', resize);
        resize();
    }

    setupMouseInteractions() {
        this.canvas.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;
            
            // Hover check
            this.nodes.forEach(node => {
                const dist = Math.hypot(node.x - mouseX, node.y - mouseY);
                if (dist < 30) {
                    if (!node.active) {
                        node.active = true;
                        node.glow = 1.0;
                        this.spawnPulse(node.id);
                    }
                } else {
                    node.active = false;
                }
            });
        });

        this.canvas.addEventListener('click', (e) => {
            this.stimulate(3.0);
        });
    }

    spawnPulse(fromNodeId) {
        const paths = this.connections.filter(c => c.from === fromNodeId || c.to === fromNodeId);
        paths.forEach(p => {
            const startNode = this.nodes[fromNodeId];
            const endNodeId = p.from === fromNodeId ? p.to : p.from;
            const endNode = this.nodes[endNodeId];
            
            this.pulses.push({
                startX: startNode.x,
                startY: startNode.y,
                endX: endNode.x,
                endY: endNode.y,
                progress: 0,
                speed: 2.0 + Math.random() * 2.0,
                color: 'rgba(61, 102, 78, 0.8)'
            });
        });
    }

    stimulate(factor) {
        this.pulseIntensity = factor;
        for (let i = 0; i < 6; i++) {
            const randNode = Math.floor(Math.random() * this.nodes.length);
            this.spawnPulse(randNode);
        }
        this.nodes.forEach(n => {
            n.glow = Math.min(n.glow + 0.3, 1.0);
        });
    }

    setSystemStress(stressRatio) {
        this.systemStress = stressRatio;
        const rateLabel = document.getElementById('synapse-flow-rate');
        if (!rateLabel) return;
        
        if (stressRatio > 0.7) {
            rateLabel.textContent = "급격함 (부하)";
            rateLabel.style.color = "#C2635B";
        } else {
            rateLabel.textContent = "안정적 (숲속 상태)";
            rateLabel.style.color = "#3D664E";
        }
    }

    update(timestamp, dt) {
        const timeFactor = timestamp * 0.001;
        this.nodes.forEach(node => {
            const swayX = Math.sin(timeFactor + node.swayOffset) * 4;
            const swayY = Math.cos(timeFactor * 0.8 + node.swayOffset) * 4;
            node.x = node.baseX + swayX;
            node.y = node.baseY + swayY;
            if (node.glow > 0.1) node.glow -= dt * 0.3;
        });

        for (let i = this.pulses.length - 1; i >= 0; i--) {
            const p = this.pulses[i];
            p.progress += dt * p.speed;
            if (p.progress >= 1.0) {
                this.pulses.splice(i, 1);
            }
        }

        // Rotate background neural dust slowly
        if (this.backgroundParticles) {
            const centerX = this.canvas.width / 2;
            const centerY = this.canvas.height / 2;
            this.backgroundParticles.forEach(p => {
                p.angle += dt * p.speed * 0.15;
                p.x = centerX + Math.cos(p.angle) * p.dist;
                p.y = centerY + Math.sin(p.angle) * p.dist;
            });
        }
    }

    render() {
        const ctx = this.ctx;
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Render 1,000,000 neuron cosmic dust field background representing the optimized neural galaxy
        if (this.backgroundParticles) {
            this.backgroundParticles.forEach(p => {
                ctx.fillStyle = `rgba(134, 168, 144, ${p.alpha * 0.8})`;
                ctx.fillRect(p.x, p.y, p.size, p.size);
            });
        }
        
        // Render branch lines
        this.connections.forEach(conn => {
            const fromNode = this.nodes[conn.from];
            const toNode = this.nodes[conn.to];
            ctx.beginPath();
            ctx.moveTo(fromNode.x, fromNode.y);
            ctx.lineTo(toNode.x, toNode.y);
            ctx.strokeStyle = `rgba(61, 102, 78, ${0.1 + (fromNode.glow + toNode.glow) * 0.15})`;
            ctx.lineWidth = 1.0 + (fromNode.glow + toNode.glow) * 1.5;
            ctx.stroke();
        });
        
        // Render pulses
        this.pulses.forEach(p => {
            const x = p.startX + (p.endX - p.startX) * p.progress;
            const y = p.startY + (p.endY - p.startY) * p.progress;
            ctx.fillStyle = p.color;
            ctx.beginPath();
            ctx.arc(x, y, 3, 0, Math.PI * 2);
            ctx.fill();
        });

        // Render nodes
        this.nodes.forEach((node, idx) => {
            ctx.fillStyle = node.glow > 0.5 ? '#E4D9C6' : '#86A890';
            ctx.beginPath();
            ctx.arc(node.x, node.y, node.size, 0, Math.PI * 2);
            ctx.fill();
            
            // Draw clean typography labels (selectively show labels to prevent overcrowding)
            if (node.active || node.glow > 0.55 || idx % 4 === 0) {
                ctx.fillStyle = node.active ? 'rgba(31, 45, 37, 0.95)' : 'rgba(31, 45, 37, 0.75)';
                ctx.font = node.active ? 'bold 10px sans-serif' : 'bold 9px sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText(node.label, node.x, node.y - node.size - 6);
            }
        });

        // Update live active neurons HUD with realistic millisecond fluctuation out of 1,000,000
        const activeCountEl = document.getElementById('active-neurons-count');
        if (activeCountEl) {
            const activeRatio = this.nodes.filter(n => n.glow > 0.35).length / this.nodes.length;
            const noise = (Math.sin(Date.now() * 0.004) * 450) + (Math.random() - 0.5) * 200;
            const simulatedActive = Math.floor(130000 + activeRatio * 830000 + noise);
            activeCountEl.textContent = Math.max(10000, Math.min(1000000, simulatedActive)).toLocaleString();
        }
    }

    setPersona(mode) {
        this.personaMode = mode;
        this.stimulate(2.0);
    }
}

window.araBrain = null;
window.addEventListener('DOMContentLoaded', () => {
    window.araBrain = new AraBrain();
});
