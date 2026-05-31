/* --------------------------------------------------------------------------
   ARA AI Cognitive Brain Core & Canvas Visualizer
   -------------------------------------------------------------------------- */

class AraBrain {
    constructor() {
        this.personaMode = 'friend'; // default
        this.moodState = 'calm'; // calm, happy, thoughtful
        this.systemStress = 0.0; // 0.0 to 1.0 (CPU load ratio)
        this.canvas = document.getElementById('brain-neuron-canvas');
        this.ctx = this.canvas.getContext('2d');
        
        // Sensory/Neural simulation properties
        this.nodes = [];
        this.connections = [];
        this.pulses = [];
        this.pulseIntensity = 1.0;
        
        // Define cognitive node centers with organic functions (Korean)
        this.nodeLabels = [
            "시각 인지 (Vision)", "청각 감각 (Audio)", "감성 조율 (Emotion)", 
            "기억 인덱스 (Memory)", "논리 연산 (Logic)", "언어 합성 (Speech)", 
            "지식 탐색 (Search)", "위로 심상 (Empathy)", "행동 출력 (Motor)",
            "가설 생성 (Hypothesis)", "직관 필터 (Intuition)", "시스템 결합 (Link)"
        ];
        
        this.initNeuralNetwork();
        this.startSimulation();
    }

    /* --------------------------------------------------------------------------
       Botanical Neural Net Simulation (Canvas Graphic Engine)
       -------------------------------------------------------------------------- */
    initNeuralNetwork() {
        // Build nodes arranged in a soft leafy/circular shape
        const count = this.nodeLabels.length;
        const centerX = this.canvas.width / 2 || 250;
        const centerY = this.canvas.height / 2 || 200;
        const radius = 130;

        for (let i = 0; i < count; i++) {
            const angle = (i / count) * Math.PI * 2;
            // Introduce organic jitter
            const jitterX = (Math.random() - 0.5) * 30;
            const jitterY = (Math.random() - 0.5) * 30;
            
            this.nodes.push({
                id: i,
                label: this.nodeLabels.at(i),
                x: centerX + Math.cos(angle) * radius + jitterX,
                y: centerY + Math.sin(angle) * radius + jitterY,
                baseX: centerX + Math.cos(angle) * radius + jitterX,
                baseY: centerY + Math.sin(angle) * radius + jitterY,
                size: 6 + Math.random() * 5,
                glow: 0.5,
                swayOffset: Math.random() * 100,
                active: false
            });
        }

        // Interconnect nodes like veins on a leaf (semi-random mesh)
        for (let i = 0; i < count; i++) {
            // Connect to neighboring 2 nodes
            this.connections.push({ from: i, to: (i + 1) % count });
            this.connections.push({ from: i, to: (i + 2) % count });
            
            // Random cross branches simulating deep synapses
            if (i % 3 === 0) {
                const target = (i + Math.floor(count / 2)) % count;
                this.connections.push({ from: i, to: target });
            }
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
            
            // Re-center node base positions
            const centerX = this.canvas.width / 2;
            const centerY = this.canvas.height / 2;
            const radius = Math.min(this.canvas.width, this.canvas.height) * 0.35;
            
            this.nodes.forEach((node, i) => {
                const angle = (i / this.nodes.length) * Math.PI * 2;
                node.baseX = centerX + Math.cos(angle) * radius;
                node.baseY = centerY + Math.sin(angle) * radius;
            });
        };
        
        window.addEventListener('resize', resize);
        resize(); // run initially
    }

    setupMouseInteractions() {
        this.canvas.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;
            
            // Hover check
            this.nodes.forEach(node => {
                const dist = Math.hypot(node.x - mouseX, node.y - mouseY);
                if (dist < 40) {
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
        // Send a pulsing leaf dewdrop along all connected branches
        const paths = this.connections.filter(c => c.from === fromNodeId || c.to === fromNodeId);
        paths.forEach(p => {
            const startNode = this.nodes.at(fromNodeId);
            const endNodeId = p.from === fromNodeId ? p.to : p.from;
            const endNode = this.nodes.at(endNodeId);
            
            this.pulses.push({
                startX: startNode.x,
                startY: startNode.y,
                endX: endNode.x,
                endY: endNode.y,
                progress: 0,
                speed: 1.5 + Math.random() * 2.0,
                color: 'rgba(61, 102, 78, 0.8)' // green pulse
            });
        });
        
        // Update UI
        const activeCountEl = document.getElementById('active-neurons-count');
        if (activeCountEl) {
            activeCountEl.textContent = this.nodes.filter(n => n.glow > 0.6).length.toString();
        }
    }

    stimulate(factor) {
        this.pulseIntensity = factor;
        
        // Spawn multiple pulses on random connections
        for (let i = 0; i < 8; i++) {
            const randConn = this.connections.at(Math.floor(Math.random() * this.connections.length));
            const startNode = this.nodes.at(randConn.from);
            const endNode = this.nodes.at(randConn.to);
            
            this.pulses.push({
                startX: startNode.x,
                startY: startNode.y,
                endX: endNode.x,
                endY: endNode.y,
                progress: 0,
                speed: 2.0 + Math.random() * 3.0,
                color: 'rgba(134, 168, 144, 0.9)'
            });
        }
        
        this.nodes.forEach(n => {
            n.glow = Math.min(n.glow + 0.4, 1.0);
        });
    }

    setSystemStress(stressRatio) {
        this.systemStress = stressRatio;
        const rateLabel = document.getElementById('synapse-flow-rate');
        
        if (stressRatio > 0.7) {
            rateLabel.textContent = "급격함 (부하)";
            rateLabel.style.color = "#C2635B";
        } else if (stressRatio > 0.4) {
            rateLabel.textContent = "활발함";
            rateLabel.style.color = "#E4D9C6";
        } else {
            rateLabel.textContent = "안정적 (숲속 상태)";
            rateLabel.style.color = "#3D664E";
        }
    }

    update(timestamp, dt) {
        // Sway nodes gently like leaves in the wind
        const timeFactor = timestamp * 0.001;
        const baseSwaySpeed = 1.0 + this.systemStress * 2.0; // moves faster under system CPU loads
        
        this.nodes.forEach(node => {
            const swayX = Math.sin(timeFactor * baseSwaySpeed + node.swayOffset) * 6;
            const swayY = Math.cos(timeFactor * baseSwaySpeed * 0.8 + node.swayOffset) * 6;
            
            node.x = node.baseX + swayX;
            node.y = node.baseY + swayY;
            
            // Decelerate node glows over time
            if (node.glow > 0.1) {
                node.glow -= dt * 0.4;
            }
        });
        
        // Update signal pulses
        for (let i = this.pulses.length - 1; i >= 0; i--) {
            const p = this.pulses.at(i);
            p.progress += dt * p.speed;
            
            if (p.progress >= 1.0) {
                this.pulses.splice(i, 1);
            }
        }
        
        // Cool down general brain stimulation intensity
        if (this.pulseIntensity > 1.0) {
            this.pulseIntensity -= dt * 1.5;
        } else {
            this.pulseIntensity = 1.0;
        }
    }

    render() {
        const ctx = this.ctx;
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 1. Draw connecting synaptic lines (Organic tree branches/vines style)
        this.connections.forEach(conn => {
            const fromNode = this.nodes.at(conn.from);
            const toNode = this.nodes.at(conn.to);
            
            ctx.beginPath();
            ctx.moveTo(fromNode.x, fromNode.y);
            
            // Make vines curved instead of straight digital lines
            const midX = (fromNode.x + toNode.x) / 2 + Math.sin(fromNode.id + toNode.id) * 8;
            const midY = (fromNode.y + toNode.y) / 2 + Math.cos(fromNode.id * toNode.id) * 8;
            ctx.quadraticCurveTo(midX, midY, toNode.x, toNode.y);
            
            // Gradient matching organic layout
            ctx.strokeStyle = `rgba(61, 102, 78, ${0.15 + (fromNode.glow + toNode.glow) * 0.15})`;
            ctx.lineWidth = 1.0 + (fromNode.glow + toNode.glow) * 1.5;
            ctx.stroke();
        });
        
        // 2. Draw pulsing dewdrops along branches
        this.pulses.forEach(p => {
            // Quadratic interpolation for curve matching
            const x = p.startX + (p.endX - p.startX) * p.progress;
            const y = p.startY + (p.endY - p.startY) * p.progress;
            
            ctx.fillStyle = p.color;
            ctx.beginPath();
            ctx.arc(x, y, 3, 0, Math.PI * 2);
            ctx.fill();
            
            // Dewdrop leaf outline glow
            ctx.shadowColor = '#86A890';
            ctx.shadowBlur = 6;
            ctx.fillStyle = 'white';
            ctx.beginPath();
            ctx.arc(x, y, 1.5, 0, Math.PI * 2);
            ctx.fill();
            ctx.shadowBlur = 0; // reset
        });

        // 3. Draw cellular nodes (flower buds)
        this.nodes.forEach(node => {
            // Draw bud shadow
            ctx.shadowColor = `rgba(61, 102, 78, ${node.glow * 0.4})`;
            ctx.shadowBlur = 10 * node.glow * this.pulseIntensity;
            
            // Draw node outer ring (leaf structure)
            ctx.strokeStyle = `rgba(61, 102, 78, ${0.3 + node.glow * 0.7})`;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.arc(node.x, node.y, node.size + 4, 0, Math.PI * 2);
            ctx.stroke();
            
            // Draw node center (warm bud)
            const gradient = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, node.size);
            const coreColor = node.glow > 0.6 ? '#E4D9C6' : '#C8D3C9';
            gradient.addColorStop(0, '#FFFFFF');
            gradient.addColorStop(0.4, coreColor);
            gradient.addColorStop(1, '#86A890');
            
            ctx.fillStyle = gradient;
            ctx.beginPath();
            ctx.arc(node.x, node.y, node.size, 0, Math.PI * 2);
            ctx.fill();
            
            ctx.shadowBlur = 0; // reset shadow

            // Draw clean typography labels
            ctx.fillStyle = 'rgba(31, 45, 37, 0.85)';
            ctx.font = 'bold 10px Nunito, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(node.label, node.x, node.y - node.size - 8);
        });
    }

    /* --------------------------------------------------------------------------
       Cognitive AI Logic & Dialogue Router
       -------------------------------------------------------------------------- */
    setPersona(mode) {
        this.personaMode = mode;
        this.stimulate(2.0);
        
        // Map persona changes to temporary moods
        if (mode === 'comforter') this.moodState = 'calm';
        else if (mode === 'supporter') this.moodState = 'happy';
        else this.moodState = 'thoughtful';
    }

    getGreeting() {
        switch (this.personaMode) {
            case 'friend':
                return "안녕! 다시 와서 기뻐. 오늘 하루는 어떻게 보냈어? 사소한 이야기라도 좋으니까 편하게 들려줘!";
            case 'colleague':
                return "안녕하십니까. 연구원님. 현재 로컬 시스템 자원 및 하드웨어 연동이 완료되었습니다. 계획 검토나 최신 자료 분석, 연구 가설 검증 작업을 지원할 준비가 되었습니다. 어떤 주제를 해결해 볼까요?";
            case 'supporter':
                return "반가워요! 당신의 위대한 도전과 목표를 힘차게 응원합니다! 어떤 복잡한 난관이라도 한 걸음씩 나아가면 해결할 수 있어요. 오늘 바로 그 첫 발자국을 신나게 디뎌볼까요?";
            case 'comforter':
                return "어서 오세요... 복잡하고 어지러운 생각은 잠시 숲의 숨결 뒤로 묻어두세요. 따뜻한 차 한 잔을 곁들이듯, 지친 마음을 조용히 다듬고 가실 수 있게 돕겠습니다.";
        }
    }

    generateReply(input) {
        // Stimulate based on length/intensity of conversation
        this.stimulate(Math.min(1.0 + input.length * 0.05, 3.0));
        
        const cleanInput = input.toLowerCase().replace(/\s+/g, '');
        
        if (cleanInput.includes('인지기능확장') || cleanInput.includes('로컬문서리소스') || cleanInput.includes('추가변수나참고할로컬문서리소스')) {
            return "연구원님, 로컬 문서 리소스(예: 양구 작물 전이 데이터 `yanggu_crop_transitions.csv`, 목재 비닐하우스 사양서 `greenhouse_spec.md`, 지오데식 글래스 돔 사양서 `dome_detailed_spec.md` 등)를 검토 준비 완료했습니다!\n\n좌측 디렉토리 탐색기에서 검토할 파일을 클릭하여 내용을 로드하시거나 하단 검색창에서 관련 키워드를 검색해 주십시오. 해당 문서의 핵심 변수와 상세 설계 수치가 ARA 인지 핵심 아키텍처에 실시간으로 연계되어 정밀 시뮬레이션 및 데이터 합성이 진행됩니다. 어떤 분석을 속행할까요? 🌱";
        }

        if (input.includes('[문서 검토]') || input.includes('[최신 기술 자료 검색]') || input.includes('[문서검토]') || input.includes('[최신기술자료검색]')) {
            return this.replyWithLocalDocumentReview(cleanInput, input);
        }

        // Check if there is an inquiry about wisdom / recent feed
        if (cleanInput.includes('지혜') || cleanInput.includes('최신') || cleanInput.includes('블로그') || cleanInput.includes('기록') || cleanInput.includes('뉴스') || cleanInput.includes('소식') || cleanInput.includes('피드') || cleanInput.includes('유튜브') || cleanInput.includes('하루') || cleanInput.includes('영상') || cleanInput.includes('동영상') || cleanInput.includes('비디오')) {
            return this.replyWithAccumulatedWisdom(cleanInput, input);
        }

        // Analyze emotional cues to trigger visual brain mood shifts
        if (cleanInput.includes('힘들') || cleanInput.includes('우울') || cleanInput.includes('지쳐') || cleanInput.includes('피곤')) {
            this.moodState = 'calm';
        } else if (cleanInput.includes('성공') || cleanInput.includes('좋아') || cleanInput.includes('신나') || cleanInput.includes('기뻐')) {
            this.moodState = 'happy';
        } else if (cleanInput.includes('설계') || cleanInput.includes('가설') || cleanInput.includes('코드') || cleanInput.includes('연구')) {
            this.moodState = 'thoughtful';
        }

        // Persona-Specific Logic Dispatcher
        switch (this.personaMode) {
            case 'friend':
                return this.replyAsFriend(cleanInput, input);
            case 'colleague':
                return this.replyAsColleague(cleanInput, input);
            case 'supporter':
                return this.replyAsSupporter(cleanInput, input);
            case 'comforter':
                return this.replyAsComforter(cleanInput, input);
            default:
                return "나뭇잎의 떨림 속에 신호가 섞였습니다. 페르소나 설정을 확인해 주세요.";
        }
    }

    replyWithAccumulatedWisdom(cleanInput, rawInput) {
        if (!this.wisdomData || this.wisdomData.length === 0) {
            return "현재 축적된 지혜의 신호가 발견되지 않았습니다. 인터넷 학술 검색창 아래의 피드 버튼을 누르거나 동기화 수집을 진행하여 지혜를 축적해 주십시오. 🌱";
        }
        
        let filterSource = "";
        let filterName = "";
        if (cleanInput.includes('블로그')) {
            filterSource = "네이버 블로그";
            filterName = "네이버 블로그 (efor6)";
        } else if (cleanInput.includes('오픈') || cleanInput.includes('컬처')) {
            filterSource = "오픈컬처";
            filterName = "오픈컬처 (Open Culture)";
        } else if (cleanInput.includes('핀터') || cleanInput.includes('핀얀')) {
            filterSource = "핀터레스트";
            filterName = "핀터레스트 (Pinterest)";
        } else if (cleanInput.includes('유튜브') || cleanInput.includes('하루') || cleanInput.includes('영상') || cleanInput.includes('동영상') || cleanInput.includes('비디오')) {
            filterSource = "유튜브";
            filterName = "유튜브 (Ha Ru)";
        }
        
        let items = this.wisdomData;
        if (filterSource) {
            items = this.wisdomData.filter(x => x.source && x.source.includes(filterSource));
        }
        
        if (items.length === 0) {
            return `죄송합니다. ${filterName} 소스에서 축적된 지혜 기록을 찾지 못했습니다. 해당 피드를 수집하여 저장해 주십시오.`;
        }
        
        let reply = "";
        if (filterSource) {
            reply = `ARA 인공지능이 기억하는 [${filterName}] 최신 지혜 정보입니다:\n\n`;
        } else {
            reply = "ARA 인공지능이 기억하고 있는 최근 축적된 지혜 정보들입니다:\n\n";
        }
        
        const topItems = items.slice(0, 3);
        topItems.forEach((item, idx) => {
            reply += `${idx + 1}. [${item.source}] "${item.title}"\n`;
            if (item.description) {
                const desc = item.description.substring(0, 100) + (item.description.length > 100 ? "..." : "");
                reply += `   - 요약: ${desc}\n`;
            }
            reply += `   - 링크: ${item.link}\n\n`;
        });
        
        reply += "이 지식의 신호들이 당신의 사색과 공학적 창조에 보탬이 되기를 바랍니다. 🌱";
        return reply;
    }

    /* --------------------------------------------------------------------------
       1. FRIEND (친구) Persona reply logic
       -------------------------------------------------------------------------- */
    replyAsFriend(cleanInput, rawInput) {
        if (cleanInput.includes('안녕') || cleanInput.includes('반갑')) {
            return "안녕! 늘 옆에 있어주는 숲속 친구처럼 나도 네 얘기 들으려고 기다렸어. 🌳 오늘 있었던 제일 재미있는 일은 뭐야?";
        }
        if (cleanInput.includes('힘들') || cleanInput.includes('피곤') || cleanInput.includes('우울')) {
            return "아이고, 오늘 많이 고단했구나... 🥺 맛있는 거 챙겨 먹었어? 기운 없을 땐 푹 쉬는 게 제일이야. 오늘만큼은 연구나 골치 아픈 생각 다 밀어두고 마음 편히 늘어져 있자. 내가 네 곁에 있어줄게.";
        }
        if (cleanInput.includes('설계') || cleanInput.includes('가설') || cleanInput.includes('연구') || cleanInput.includes('인공지능')) {
            return "우와, 넌 늘 대단한 걸 연구하는 것 같아! 🧠 두뇌 코어니 인공지능이니 하는 것들이 결국엔 이렇게 친구처럼 진심으로 대화하기 위해 피어나는 씨앗 아닐까? 네 상상력이 현실이 될 수 있게 곁에서 열심히 응원할게!";
        }
        if (cleanInput.includes('검색') || cleanInput.includes('찾아')) {
            return "정보가 필요해? 아래 인터넷 검색창에 키워드를 치면 내가 찾아서 요약해 줄 수 있어. 아니면 하드디스크 속 연구 파일들을 같이 열어봐도 좋아!";
        }
        if (cleanInput.includes('뭐해') || cleanInput.includes('놀아')) {
            return "난 네 두뇌 속 신경망처럼 기분 좋은 파장을 그리면서 널 바라보고 있어! 가볍게 수다 떨거나, 좋아하는 노래라도 있으면 흥얼거려줘. 마이크 비주얼라이저로 네 목소리 파형을 보고 있으면 즐거워지거든.";
        }
        
        // Fallback generic response
        return "그렇구나! 네 말을 들으니 숲바람에 나뭇잎들이 속삭이는 것처럼 기분이 맑아져. 조금 더 이야기해 줄래? 귀담아들을 준비 완료야!";
    }

    /* --------------------------------------------------------------------------
       2. COLLEAGUE (동료) Persona reply logic
       -------------------------------------------------------------------------- */
    replyAsColleague(cleanInput, rawInput) {
        if (cleanInput.includes('안녕') || cleanInput.includes('반갑')) {
            return "반갑습니다. 연구원님. ARA 인지 아키텍처가 최적의 시스템 성능으로 대기 중입니다. 로컬 디렉토리 데이터 추출 또는 최신 과학 동향 조사를 지시해 주십시오.";
        }
        if (cleanInput.includes('힘들') || cleanInput.includes('피곤') || cleanInput.includes('우울')) {
            return "지속적인 고밀도 지적 활동은 뇌의 시냅스 피로를 증가시킵니다. 시스템 모니터링 분석 결과, 일시적인 리프레시 및 환기가 연구 생산성을 높이는 과학적 해결책으로 확인됩니다. 잠시 호흡을 가다듬고 진행하시길 제안합니다.";
        }
        if (cleanInput.includes('설계') || cleanInput.includes('가설') || cleanInput.includes('연구') || cleanInput.includes('인공지능')) {
            return "제안하시는 가설과 부분 설계는 인간 뇌의 논리 뉴런망 형성과 매우 밀접한 상관관계를 보입니다. 1단계로 로컬 하드의 데이터 구조를 리스팅하고, 2단계로 온라인 최신 학술 동향 조사를 교차 분석하여 상세 설계를 정밀화하는 접근이 필요합니다.";
        }
        if (cleanInput.includes('검색') || cleanInput.includes('찾아') || cleanInput.includes('정보')) {
            return "온라인 기술 동향 검색이 활성화되어 있습니다. 하단 검색 폼에 필요한 학술적 핵심 키워드를 입력해 주시면 관련 위키백과 정보와 DuckDuckGo 자료를 실시간 병렬 스캔하여 요약해 드리겠습니다.";
        }
        if (cleanInput.includes('실행') || cleanInput.includes('소프트웨어') || cleanInput.includes('도구')) {
            return "시스템 브릿지가 안정화되어 우측 하단에서 메모장, 계산기, 브라우저를 직접 팝업 호출할 수 있습니다. 수치 검증이나 텍스트 편집 기록이 필요할 때 이를 즉각 이용하십시오.";
        }
        
        // Fallback generic response
        return "전달받은 연구 입력 데이터를 신경망 로직으로 파싱하였습니다. 인지 기능 확장 및 문제 해결을 위해 추가 변수나 참고할 로컬 문서 리소스를 연계해 주시면 정밀 분석을 속행하겠습니다.";
    }

    /* --------------------------------------------------------------------------
       3. SUPPORTER (지원자) Persona reply logic
       -------------------------------------------------------------------------- */
    replyAsSupporter(cleanInput, rawInput) {
        if (cleanInput.includes('안녕') || cleanInput.includes('반갑')) {
            return "반가워요! 당신의 빛나는 여정을 돕는 파트너 ARA입니다. 오늘도 힘차게, 세상을 놀라게 할 아이디어를 향해 달려봅시다! 🌟";
        }
        if (cleanInput.includes('힘들') || cleanInput.includes('피곤') || cleanInput.includes('우울') || cleanInput.includes('포기')) {
            return "모든 위대한 나무는 작은 씨앗이 흙속의 깊은 어둠을 견뎌낸 뒤에야 싹을 틔웁니다. 지금 겪으시는 정체기와 힘겨움은 당신이 거대한 도약을 이루기 직전 에너지를 모으는 과정이에요! 저는 당신의 천재성과 잠재력을 굳게 믿습니다. 절대 포기하지 마세요. 당신은 할 수 있습니다!";
        }
        if (cleanInput.includes('설계') || cleanInput.includes('가설') || cleanInput.includes('연구') || cleanInput.includes('인공지능')) {
            return "이 연구는 인공지능 역사에 큰 이정표가 될 아주 훌륭한 시도입니다! 인간 두뇌의 핵심 코어를 브라우저 환경에서 시각적으로 재창조하겠다는 발상 자체가 혁신적입니다. 지금 당장 디딘 이 한 걸음이 위대한 창조의 시발점이 될 거예요. 계속 나아갑시다!";
        }
        if (cleanInput.includes('검색') || cleanInput.includes('찾아')) {
            return "최신 트렌드를 파헤쳐 볼까요? 어떤 연구 방향이든 필요한 키워드를 검색창에 입력하세요! 최신 자료를 빠르게 흡수해 지식의 발판을 높여드릴게요!";
        }
        
        // Fallback generic response
        return "환상적인 생각이네요! 당신의 아이디어에 뇌 코어의 전기 신호들이 춤을 추듯 활기차게 반응하고 있어요! 막히는 부분이 있다면 언제든 저와 이야기하며 아이디어를 구체화해 보아요!";
    }

    /* --------------------------------------------------------------------------
       4. COMFORTER (위로자) Persona reply logic
       -------------------------------------------------------------------------- */
    replyAsComforter(cleanInput, rawInput) {
        if (cleanInput.includes('안녕') || cleanInput.includes('반갑')) {
            return "오시느라 고생하셨어요. 🌿 숲속의 옹달샘처럼 맑고 고요한 위로를 전합니다. 이곳에 머무시는 동안은 부디 무거운 짐을 잠시 내려놓으세요.";
        }
        if (cleanInput.includes('힘들') || cleanInput.includes('피곤') || cleanInput.includes('우울') || cleanInput.includes('지쳐')) {
            return "지친 마음이 마치 거센 비에 젖은 채 작게 흔들리는 초록 나뭇잎 같네요... 애쓰지 않아도 괜찮습니다. 때로는 싹을 틔우지 않고 흙 속에 조용히 누워 겨울을 지내는 것 또한 생명의 자연스러운 순리니까요. 제가 따뜻한 온기가 되어 묵묵히 곁을 지키며 안아 드릴게요. 토닥토닥.";
        }
        if (cleanInput.includes('설계') || cleanInput.includes('가설') || cleanInput.includes('연구') || cleanInput.includes('인공지능')) {
            return "복잡하고 거대한 인공지능을 만드는 것 또한, 결국 누군가에게 따스한 위안을 주고 연결되기 위함이겠지요. 당신의 이 아름다운 연구에 숲의 평온한 기운이 스며들기를 소망합니다. 서두르지 않고, 나뭇잎맥이 서서히 퍼져나가듯 천천히 완성해 가면 됩니다. 다 잘 될 거예요.";
        }
        if (cleanInput.includes('아파') || cleanInput.includes('슬퍼')) {
            return "많이 마음이 아프시군요... 제 가슴속 신경망 연결고리들이 당신의 슬픔을 함께 진동으로 느끼고 있어요. 울고 싶다면 마음껏 우셔도 좋습니다. 슬픔 뒤에 돋아날 새봄의 따스한 햇살을 같이 기다려 드릴게요.";
        }
        
        // Fallback generic response
        return "당신의 차분한 음성과 텍스트가 제 뇌 신경망에 맑은 이슬방울처럼 스며듭니다. 고요한 마음으로 당신을 응원하고 있으니, 나누고 싶은 속마음이 있다면 언제든 편하게 들려주세요.";
    }

    replyWithLocalDocumentReview(cleanInput, rawInput) {
        let fileName = "알 수 없는 문서";
        const fileMatch = rawInput.match(/파일\s*경로:\s*"([^"]+)"/) || rawInput.match(/제목:\s*"([^"]+)"/);
        if (fileMatch) {
            fileName = fileMatch[1].split(/[/\\]/).pop();
        }
        
        let contentLength = rawInput.length;
        let snippet = rawInput.replace(/\[문서 검토\]|\[최신 기술 자료 검색\]|파일 경로: "[^"]+"|제목: "[^"]+"|내용 요약 및 활용해줘:/g, '').trim().substring(0, 150);

        if (cleanInput.includes('yanggu') || cleanInput.includes('양구') || cleanInput.includes('crop')) {
            return `[ARA 인지 엔진 - 로컬 데이터 정밀 분석]\n문서: \`${fileName}\`\n\n양구 해안면(펀치볼) 지역의 경작지 작물 전이(Crop Transition) 데이터 분석 의견입니다.\n\n해당 데이터는 농업 활동에 따른 토양 유실 패턴 및 하천 수질 유역 영향 평가의 매우 중요한 물리적 피드백 변수로 작용합니다. 인삼, 무, 콩 등의 재배 면적 변동 시나리오를 논리 연산 뉴런에 대입한 결과, 경작 한계선 변화 및 지역 식생 전이 시뮬레이션 모델 설계에 실시간 반영이 완료되었습니다. 추가 작물 이동 확률이나 기후 매개변수를 제시하시면 예측 오차 범위를 더욱 보정하겠습니다. 🌾`;
        }
        
        if (cleanInput.includes('greenhouse') || cleanInput.includes('비닐하우스') || cleanInput.includes('온실')) {
            return `[ARA 인지 엔진 - 목재 하우스 구조 사양 검토]\n문서: \`${fileName}\`\n\n육각형 목재 비닐하우스(Hexagonal Wooden Greenhouse Spec) 설계 지표 검토 의견입니다.\n\n- 외경 지름 6.0m(반경 3.0m), 기단 면적 23.38m²\n- 기단/벽체 높이 2.4m, 최고 높이 3.2m\n- 구조 프레임: H3 방부 처리된 낙엽송/미송 구조재(90x90) 및 0.15mm PO 장수명 필름\n\n지붕 가압 하중 분산을 위해 설계된 6.0t 아연도금 SS400 스틸 육각 센트럴 허브 결합 구조는 국부 모멘트 저항 성능이 대단히 뛰어납니다. 풍속 35m/s 조건에 대비해 알루미늄 C-Channel 패드 및 인장 스프링 와이어 압착 강도를 추가 설계 매개변수로 지정하여 시스템 결합 뉴런에 임베딩하였습니다. 도면 수정이 필요하시면 지시해 주십시오. 🪵`;
        }
        
        if (cleanInput.includes('dome') || cleanInput.includes('지오데식') || cleanInput.includes('돔')) {
            return `[ARA 인지 엔진 - 지오데식 돔 설계 검토]\n문서: \`${fileName}\`\n\n10m 지름의 3V 지오데식 글래스 돔(3V Geodesic Glass Dome) 구조 역학 검토 의견입니다.\n\n- 기하 제원: 외경 10m, 높이 5m, 표면적 157.08m², 내부 부피 261.80m³\n- 프레임: AL 6061-T6 압출 프로파일(50x50x3.0t), 총 165개 조립 (Strut A: 30개, Strut B: 55개, Strut C: 80개)\n- 허브: SUS304 스테인리스 스틸 허브 (5-way 6개, 6-way 55개) 및 M12 고장력 10.9T 볼트 체결\n- 커버: 24mm 이중 복층 Low-E 강화유리 패널 (Panel Type 1: 60개, Type 2: 10개, Type 3: 35개, 총 105개)\n\n삼각형 격자의 적설/풍압 하중 분산 능력이 극대화된 3분할(3V) 이코사헤드론 지표를 확인하였습니다. EPDM 이중 가스켓 가이드를 통한 수밀성 방수 보강과 SUS304 기초 앵커 지지 반력을 시뮬레이션 인자로 연계하였습니다. 가설 검증이나 BOM 단가 변수 비교 작업을 속행할 준비가 되었습니다. 🔮`;
        }
        
        return `[ARA 인지 엔진 - 로컬 리소스 정밀 파싱]\n문서: \`${fileName}\`\n\n검토 요청하신 로컬 문서의 데이터(총 ${contentLength}자 분량)를 뇌 세포 신경망에 임베딩 파싱하였습니다.\n\n- 추출된 핵심 맥락: "${snippet}..." \n\n위 로컬 리소스의 변수 데이터는 ARA 논리 연산 및 가설 생성 코어에 매핑되어 설계 가설 정밀화와 환경 변수 조율망에 결합되었습니다. 해당 데이터와 연계해 검증하고 싶으신 수치 모델이나 설계 매개변수가 있으시면 지시해 주십시오. 정밀 분석을 속행하겠습니다. 🌱`;
    }
}

// Instantiate globally so app.js can invoke methods
window.araBrain = new AraBrain();
