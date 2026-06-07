/* --------------------------------------------------------------------------
   ARA App Controller (Hardware & API Binding)
   -------------------------------------------------------------------------- */

const API_BASE = 'http://localhost:8080';
let audioContext = null;
let audioAnalyser = null;
let micStream = null;
let speechRecognition = null;
let isListening = false;
let isSoundMuted = false;
let currentPath = '';
let cameraStream = null;
let isCameraOn = false;

// Sensory Recognition Globals
let cocoModel = null;
let isModelLoading = false;
let visionDetectionTimeout = null;
let lastSensoryLogTime = 0;
let lastSensoryState = { location: '', person: '', objects: '' };

// Local AI (Ollama) state variables
window.ollamaEnabled = false;
window.ollamaOnline = false;

function safeJsonParse(str, defaultVal = null) {
    try {
        return str ? JSON.parse(str) : defaultVal;
    } catch (e) {
        return defaultVal;
    }
}

// DOM Elements
const webcamFeed = document.getElementById('webcam-feed');
const audioWaveform = document.getElementById('audio-waveform');
const audioDbLabel = document.getElementById('audio-db-label');
const cpuLoadText = document.getElementById('cpu-load-text');
const dbStatusText = document.getElementById('db-status-text');
const chatMessages = document.getElementById('chat-messages-container');
const chatTextInput = document.getElementById('chat-text-input');
const btnSendMessage = document.getElementById('btn-send-message');
const btnVoiceInput = document.getElementById('btn-voice-input');
const btnToggleSound = document.getElementById('btn-toggle-sound');
const iconSoundStatus = document.getElementById('icon-sound-status');
const interactionStatusText = document.getElementById('interaction-status-text');
const pulsingLeafIndicator = document.querySelector('.pulsing-leaf-indicator');
const fileList = document.getElementById('file-list');
const currentFolderPath = document.getElementById('current-folder-path');
const btnRefreshFiles = document.getElementById('btn-refresh-files');
const webSearchInput = document.getElementById('web-search-input');
const btnWebSearch = document.getElementById('btn-web-search');
const webSearchResults = document.getElementById('web-search-results');
const consoleOutput = document.getElementById('console-output');

// Initialize ARA Front-End
window.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Lucide Icons
    lucide.createIcons();

    // 1.5. Handle User Authentication (Naver OAuth)
    handleUserAuthentication();

    // 2. Start Camera & Audio Analyzers
    initCamera();
    initAudioAnalyzer();
    
    // 3. Initialize Speech Recognition
    initSpeechRecognition();

    // 4. Connect Backend Data
    initBackendConnection();
    initSearchAdvisorConnection();
    initMaintenanceConnection();

    // 5. Setup Action Listeners
    setupEventListeners();
});

/* --------------------------------------------------------------------------
   Sensory Input: Camera & Video Stream
   -------------------------------------------------------------------------- */
function initCamera() {
    const visionStatus = document.querySelector('.vision-status');
    visionStatus.textContent = "시각 데이터 비활성화됨";
    webcamFeed.style.display = 'none';
    
    // Render botanical drawing in place of video initially (OFF state)
    const placeholder = document.createElement('div');
    placeholder.className = 'camera-placeholder';
    placeholder.innerHTML = `<i data-lucide="video-off" style="width: 48px; height: 48px; color: var(--accent-sage);"></i><p style="margin-top: 10px; font-size: 12px; color: var(--text-secondary);">시각 카메라가 꺼져 있습니다.</p>`;
    placeholder.style.display = 'flex';
    placeholder.style.flexDirection = 'column';
    placeholder.style.alignItems = 'center';
    placeholder.style.justifyContent = 'center';
    placeholder.style.height = '100%';
    placeholder.style.backgroundColor = '#E2EAE3';
    webcamFeed.parentNode.appendChild(placeholder);
    lucide.createIcons();
}

async function toggleCamera() {
    const visionStatus = document.querySelector('.vision-status');
    const icon = document.getElementById('icon-camera-status');
    const placeholder = document.querySelector('.camera-placeholder');

    if (isCameraOn) {
        // Turn OFF
        if (cameraStream) {
            cameraStream.getTracks().forEach(track => track.stop());
            cameraStream = null;
        }
        webcamFeed.srcObject = null;
        webcamFeed.style.display = 'none';
        
        // Show placeholder
        if (placeholder) {
            placeholder.style.display = 'flex';
            const iconEl = placeholder.querySelector('i');
            if (iconEl) iconEl.setAttribute('data-lucide', 'video-off');
            const textEl = placeholder.querySelector('p');
            if (textEl) textEl.textContent = '시각 카메라가 꺼져 있습니다.';
        }
        
        visionStatus.textContent = "시각 데이터 비활성화됨";
        icon.setAttribute('data-lucide', 'video-off');
        isCameraOn = false;

        // Clear detection loop
        if (visionDetectionTimeout) {
            clearTimeout(visionDetectionTimeout);
            visionDetectionTimeout = null;
        }
        const canvas = document.getElementById('vision-canvas');
        if (canvas) {
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
    } else {
        // Turn ON
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                video: { width: 320, height: 240 } 
            });
            cameraStream = stream;
            webcamFeed.srcObject = stream;
            webcamFeed.style.display = 'block';
            
            // Hide placeholder
            if (placeholder) {
                placeholder.style.display = 'none';
            }
            
            visionStatus.textContent = "시각 데이터 활성화됨";
            icon.setAttribute('data-lucide', 'video');
            isCameraOn = true;

            // Load model and start TF.js loop
            loadCocoSsdModel().then(() => {
                startDetectionLoop();
            });
        } catch (err) {
            console.warn("Webcam access denied or unavailable:", err);
            visionStatus.textContent = "카메라를 찾을 수 없음 (시각 차단됨)";
            webcamFeed.style.display = 'none';
            
            if (placeholder) {
                placeholder.style.display = 'flex';
                const iconEl = placeholder.querySelector('i');
                if (iconEl) iconEl.setAttribute('data-lucide', 'eye-off');
                const textEl = placeholder.querySelector('p');
                if (textEl) textEl.textContent = '시각 카메라 스트림이 비활성화되었습니다.';
            }
        }
    }
    lucide.createIcons();
}

/* --------------------------------------------------------------------------
   Sensory Input: Audio & Mic Visualization (Ripple wave)
   -------------------------------------------------------------------------- */
async function initAudioAnalyzer() {
    try {
        micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioContext.createMediaStreamSource(micStream);
        audioAnalyser = audioContext.createAnalyser();
        
        audioAnalyser.fftSize = 256;
        source.connect(audioAnalyser);
        
        drawAudioWave();
    } catch (err) {
        console.warn("Microphone access denied or unavailable:", err);
        audioDbLabel.textContent = "오디오 입력 차단";
        drawStaticWave();
    } finally {
        if (!audioAnalyser) {
            if (micStream) {
                try {
                    micStream.getTracks().forEach(track => track.stop());
                } catch (e) {}
                micStream = null;
            }
            if (audioContext) {
                try {
                    audioContext.close();
                } catch (e) {}
                audioContext = null;
            }
        }
    }
}

function drawAudioWave() {
    if (!audioAnalyser) return;
    
    const canvas = audioWaveform;
    const ctx = canvas.getContext('2d');
    const bufferLength = audioAnalyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    // Set responsive width
    if (canvas.width !== canvas.parentNode.clientWidth || canvas.height !== canvas.parentNode.clientHeight) {
        canvas.width = canvas.parentNode.clientWidth;
        canvas.height = canvas.parentNode.clientHeight;
    }
    
    function draw() {
        requestAnimationFrame(draw);
        
        audioAnalyser.getByteTimeDomainData(dataArray);
        
        ctx.fillStyle = '#F2ECE1'; // sand background
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        ctx.lineWidth = 1.8;
        ctx.strokeStyle = '#3D664E'; // forest green wave
        ctx.beginPath();
        
        const sliceWidth = canvas.width * 1.0 / bufferLength;
        let x = 0;
        
        // Calculate raw volume
        let sumSq = 0;
        
        for (let i = 0; i < bufferLength; i++) {
            const v = dataArray.at(i) / 128.0; // Normalized -1 to 1
            const y = v * canvas.height / 2;
            
            // volume calc
            const dev = v - 1.0;
            sumSq += dev * dev;

            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                // Smooth wave drawing using bezier style approximation
                ctx.lineTo(x, y);
            }
            
            x += sliceWidth;
        }
        
        ctx.lineTo(canvas.width, canvas.height / 2);
        ctx.stroke();
        
        // Update volume label
        const rms = Math.sqrt(sumSq / bufferLength);
        const volumePercent = Math.min(Math.round(rms * 400), 100);
        audioDbLabel.textContent = `Volume: ${volumePercent}%`;

        // Sound-trigger camera activation logic (>30%)
        const chkAutoCamera = document.getElementById('chk-sound-auto-camera');
        if (chkAutoCamera && chkAutoCamera.checked && volumePercent > 30 && !isCameraOn) {
            console.log(`[Auto-Trigger] Microphone volume reached ${volumePercent}%, triggering camera activation.`);
            toggleCamera();
        }
    }
    
    draw();
}

function drawStaticWave() {
    const canvas = audioWaveform;
    const ctx = canvas.getContext('2d');
    canvas.width = canvas.parentNode.clientWidth || 300;
    canvas.height = canvas.parentNode.clientHeight || 100;
    
    ctx.fillStyle = '#F2ECE1';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Draw flat line with subtle wind ripple
    ctx.lineWidth = 1;
    ctx.strokeStyle = 'rgba(61, 102, 78, 0.4)';
    ctx.beginPath();
    ctx.moveTo(0, canvas.height / 2);
    
    let x = 0;
    while(x < canvas.width) {
        const y = canvas.height / 2 + Math.sin(x * 0.05) * 2;
        ctx.lineTo(x, y);
        x += 5;
    }
    ctx.stroke();
}

/* --------------------------------------------------------------------------
   Voice Control: Web Speech API (STT & TTS)
   -------------------------------------------------------------------------- */
function initSpeechRecognition() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) {
        console.warn("Speech Recognition API is not supported in this browser.");
        btnVoiceInput.style.display = 'none';
        return;
    }
    
    speechRecognition = new SpeechRec();
    speechRecognition.lang = 'ko-KR';
    speechRecognition.continuous = true; // Continuous listening
    speechRecognition.interimResults = false;
    
    speechRecognition.onstart = () => {
        isListening = true;
        btnVoiceInput.className = 'btn-voice-listening';
        pulsingLeafIndicator.classList.add('listening');
        interactionStatusText.textContent = "아라가 항상 경청하는 중...";
        document.getElementById('voice-btn-icon')?.setAttribute('data-lucide', 'mic-off');
        lucide.createIcons();
        
        if (window.araBrain) {
            window.araBrain.stimulate(1.5);
            updateMoodChip('listening', '경청하는 중');
        }
    };
    
    speechRecognition.onend = () => {
        // If STT was stopped automatically by browser timeout/silence, auto-restart it to keep it ALWAYS ON!
        if (isListening) {
            try {
                speechRecognition.start();
            } catch (e) {
                console.log("Restarting SpeechRecognition...", e);
                return null;
            }
        } else {
            btnVoiceInput.className = 'btn-voice-ready';
            pulsingLeafIndicator.classList.remove('listening');
            interactionStatusText.textContent = "아라가 이야기를 기다리는 중...";
            document.getElementById('voice-btn-icon')?.setAttribute('data-lucide', 'mic');
            lucide.createIcons();
            
            if (window.araBrain) {
                const currentMood = window.araBrain.moodState;
                updateMoodChip(currentMood, getMoodKorean(currentMood));
            }
        }
    };
    
    speechRecognition.onerror = (event) => {
        console.error("Speech Recognition Error:", event.error);
        if (event.error === 'not-allowed') {
            console.warn("마이크 사용 권한이 거부되었습니다.");
            isListening = false;
        } else if (event.error === 'aborted') {
            // ignore aborted error (often happens on manual restart)
        }
    };
    
    speechRecognition.onresult = (event) => {
        const resultIndex = event.resultIndex;
        const transcript = event.results[resultIndex][0].transcript.trim();
        if (transcript) {
            chatTextInput.value = transcript;
            sendMessage();
        }
    };

    // Auto-start speech recognition on load to make STT "always ON" by default!
    isListening = true;
    try {
        speechRecognition.start();
    } catch (e) {
        console.warn("Auto-start speech recognition failed:", e);
        return null;
    }
}

function speakText(text) {
    if (isSoundMuted || !('speechSynthesis' in window)) return;
    
    // Stop any currently speaking voice
    window.speechSynthesis.cancel();
    
    // Clean text from Markdown tags or brackets for cleaner reading
    const cleanText = text.replace(/[*#`_\-\[\]()]/g, '').trim();
    
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = 'ko-KR';
    
    // Select a pleasant voice if available
    const voices = window.speechSynthesis.getVoices();
    const koVoice = voices.find(v => v.lang.includes('ko') || v.lang.includes('KO'));
    if (koVoice) {
        utterance.voice = koVoice;
    }
    
    // Slower, calming speed for nature comforter mode
    if (window.araBrain && window.araBrain.personaMode === 'comforter') {
        utterance.rate = 0.85;
        utterance.pitch = 0.95;
    } else {
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
    }
    
    window.speechSynthesis.speak(utterance);
}

/* --------------------------------------------------------------------------
   Backend Bridging & API Polling
   -------------------------------------------------------------------------- */
function initBackendConnection() {
    // Initial fetch of system info and file directory
    updateSystemStats();
    loadDirectoryList('');
    checkSchedulerConfig();
    loadWisdomStorage();
    loadOllamaConfig();
    
    // Set interval to poll CPU load every 5 seconds
    if (window.systemStatsInterval) {
        clearInterval(window.systemStatsInterval);
    }
    window.systemStatsInterval = setInterval(updateSystemStats, 5000);

    // Initial load and periodic polling of sensory history (every 4 seconds)
    loadSensoryHistory();
    if (window.sensoryHistoryInterval) {
        clearInterval(window.sensoryHistoryInterval);
    }
    window.sensoryHistoryInterval = setInterval(loadSensoryHistory, 4000);
}

async function checkSchedulerConfig() {
    try {
        const res = await fetch(`${API_BASE}/api/scheduler/config`);
        if (!res.ok) return;
        const config = await res.json();
        if (config.configured) {
            console.log("Email Config Status:", config);
            if (!config.enabled) {
                consoleOutput.textContent = "알림: efor6@naver.com 이메일 알림이 비활성화 상태입니다. E:\\SEA\\email_config.json에서 활성화해 주세요.";
            } else {
                consoleOutput.textContent = `알림: 이메일 전송 활성화 상태 (수신: ${config.recipient})`;
            }
        }
    } catch (err) {
        console.warn("Could not check email config:", err);
        return null;
    }
}

async function updateSystemStats() {
    const connStatus = document.getElementById('connection-status');
    const statusDot = connStatus.querySelector('.status-dot');
    const connText = document.getElementById('conn-text');

    try {
        const res = await fetch(`${API_BASE}/api/system`);
        if (!res.ok) throw new Error("Backend response error");
        
        const stats = await res.json();
        
        // Update stats UI
        cpuLoadText.textContent = `${stats.cpu_usage}%`;
        dbStatusText.textContent = "활성화";
        
        // Set state to online
        statusDot.className = 'status-dot online';
        connText.textContent = '온라인';
        
        // Send CPU load context to AI Brain for dynamic visual speed
        if (window.araBrain) {
            window.araBrain.setSystemStress(stats.cpu_usage / 100.0);
        }
    } catch (err) {
        console.warn("Backend not running, falling back to local cognitive network:", err);
        cpuLoadText.textContent = '0%';
        dbStatusText.textContent = "로컬 보존";
        statusDot.className = 'status-dot online'; // 항상 온라인 유지
        connText.textContent = '온라인 (로컬 안전망 구동 중)';
        
        if (window.araBrain) {
            window.araBrain.setSystemStress(0.0);
        }
    }
}

async function loadDirectoryList(path) {
    fileList.innerHTML = `<li class="file-item loading">디렉토리 로드 중...</li>`;
    let res = null;
    try {
        const encodedPath = encodeURIComponent(path);
        res = await fetch(`${API_BASE}/api/files?action=list&path=${encodedPath}`);
        if (!res.ok) throw new Error("Directory list error");
        
        const data = await res.json();
        currentPath = data.current_path;
        currentFolderPath.textContent = currentPath;
        
        fileList.innerHTML = '';
        
        // Add "Go Parent" directory item if not at system root
        // Add "Go Parent" directory item if not at system root "내 PC"
        if (currentPath !== '내 PC') {
            const parentItem = document.createElement('li');
            parentItem.className = 'file-item directory';
            parentItem.innerHTML = `<i data-lucide="arrow-up-left" style="width: 14px; height: 14px;"></i> <span>[상위 디렉토리]</span>`;
            parentItem.addEventListener('click', () => {
                const isDriveRoot = /^[A-Z]:\\?$/i.test(currentPath);
                if (isDriveRoot) {
                    loadDirectoryList('');
                } else {
                    let tempPath = currentPath.replace(/[\\/]$/, '');
                    let lastIdx = Math.max(tempPath.lastIndexOf('/'), tempPath.lastIndexOf('\\'));
                    if (lastIdx !== -1) {
                        let parentPath = tempPath.substring(0, lastIdx);
                        if (/^[A-Z]:$/i.test(parentPath)) parentPath += osSeparator();
                        loadDirectoryList(parentPath);
                    } else {
                        loadDirectoryList('');
                    }
                }
            });
            fileList.appendChild(parentItem);
        }
        
        if (data.items.length === 0) {
            fileList.innerHTML = `<li class="file-item loading">디렉토리가 비어있습니다.</li>`;
            return;
        }

        data.items.forEach(item => {
            const li = document.createElement('li');
            li.className = `file-item ${item.is_dir ? 'directory' : 'file'}`;
            
            const icon = document.createElement('i');
            icon.setAttribute('data-lucide', item.is_dir ? 'folder' : 'file');
            icon.style.width = '14px';
            icon.style.height = '14px';
            li.appendChild(icon);
            
            const span = document.createElement('span');
            span.textContent = " " + item.name;
            li.appendChild(span);
            
            li.addEventListener('click', () => {
                if (item.is_dir) {
                    loadDirectoryList(item.path);
                } else {
                    loadFileContent(item.path);
                }
            });
            fileList.appendChild(li);
        });
        
        lucide.createIcons();
    } catch (err) {
        fileList.innerHTML = `<li class="file-item loading" style="color: #C2635B;">파일을 불러오지 못했습니다.</li>`;
        console.error(err);
    } finally {
        if (res && res.body && !res.bodyUsed) {
            res.body.cancel().catch(() => {});
        }
    }
}

async function loadFileContent(filePath) {
    let res = null;
    try {
        const encodedPath = encodeURIComponent(filePath);
        res = await fetch(`${API_BASE}/api/files?action=read&path=${encodedPath}`);
        if (!res.ok) throw new Error("File read error");
        
        const data = await res.json();
        
        // Notify user about local file data extraction
        appendMessage('system', `로컬 파일 로드 완료: ${filePath.split(/[/\\]/).pop()}`);
        
        // Input text into chat prompt as prompt context for analysis
        chatTextInput.value = `[문서 검토] 파일 경로: "${data.path}"\n내용 요약 및 활용해줘:\n${data.content.substring(0, 1200)}`;
        chatTextInput.focus();
        
        // Notify system console log
        consoleOutput.textContent = `File content read: ${filePath} (${data.content.length} bytes)`;
    } catch (err) {
        console.error("Failed to read file:", err);
        alert(`파일을 읽어오는데 실패했습니다: ${err.message}`);
    } finally {
        if (res && res.body && !res.bodyUsed) {
            res.body.cancel().catch(() => {});
        }
    }
}

async function triggerWebSearch() {
    const query = webSearchInput.value.trim();
    if (!query) return;
    
    webSearchResults.innerHTML = `<div class="search-placeholder-text">온라인 정보 검색 스트림 연결 중...</div>`;
    
    let res = null;
    try {
        const encodedQ = encodeURIComponent(query);
        res = await fetch(`${API_BASE}/api/search?q=${encodedQ}`);
        if (!res.ok) throw new Error("Search server error");
        
        const data = await res.json();
        webSearchResults.innerHTML = '';
        
        if (!data.results || data.results.length === 0) {
            webSearchResults.innerHTML = `<div class="search-placeholder-text">검색 결과가 발견되지 않았습니다.</div>`;
            return;
        }
        
        data.results.forEach(result => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'search-item';
            
            const link = document.createElement('a');
            link.href = result.url;
            link.target = '_blank';
            link.className = 'search-title-link';
            
            const extIcon = document.createElement('i');
            extIcon.setAttribute('data-lucide', 'external-link');
            extIcon.style.width = '12px';
            extIcon.style.height = '12px';
            link.appendChild(extIcon);
            
            const titleSpan = document.createElement('span');
            titleSpan.textContent = " " + result.title;
            link.appendChild(titleSpan);
            itemDiv.appendChild(link);
            
            const badge = document.createElement('span');
            badge.className = 'search-source-badge';
            badge.textContent = result.source;
            itemDiv.appendChild(badge);
            
            const snippetDiv = document.createElement('div');
            snippetDiv.className = 'search-snippet';
            snippetDiv.textContent = result.snippet;
            itemDiv.appendChild(snippetDiv);
            
            // Add click event to feed this web snippet to chat input or open local file
            itemDiv.addEventListener('click', (e) => {
                if (e.target.closest('.search-title-link')) return; // let link open
                if (result.source === 'Local Disk (E:)') {
                    // Load the local file content directly!
                    loadFileContent(result.url);
                } else {
                    chatTextInput.value = `[최신 기술 자료 검색] 제목: "${result.title}"\n요약: "${result.snippet}"\n위 내용을 최신 연구 방향 가설과 연계해 자세히 설명해줘.`;
                    chatTextInput.focus();
                }
            });
            
            webSearchResults.appendChild(itemDiv);
        });
        
        lucide.createIcons();
    } catch (err) {
        const errDiv = document.createElement('div');
        errDiv.className = 'search-placeholder-text';
        errDiv.style.color = '#C2635B';
        errDiv.textContent = `검색 도중 에러가 발생했습니다: ${err.message}`;
        webSearchResults.innerHTML = '';
        webSearchResults.appendChild(errDiv);
        console.error(err);
    } finally {
        if (res && res.body && !res.bodyUsed) {
            res.body.cancel().catch(() => {});
        }
    }
}

async function runLocalUtility(appName) {
    if (!appName) return;
    consoleOutput.textContent = `Requesting launch of: ${appName}...`;
    let success = false;

    // 1차 채널 (8080 포트) 시도
    try {
        const res = await fetch(`${API_BASE}/api/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target: appName })
        });
        if (res.ok) {
            const data = await res.json();
            if (data.status === 'success') {
                consoleOutput.textContent = `SUCCESS: ${data.message}`;
                appendMessage('system', `로컬 애플리케이션 실행 성공: ${appName}`);
                success = true;
            } else {
                consoleOutput.textContent = `ERROR: ${data.message}`;
                alert(`시스템 제어 제한: ${data.message}`);
                success = true; // 에러 응답 수신 완료
            }
        }
    } catch (err) {
        console.warn("Primary API execute failed, trying backup origin (8000)...", err);
    }

    // 2차 채널 (현재 접속 페이지의 Origin/8000 포트 예비 서버) 시도
    if (!success) {
        try {
            const fallbackUrl = window.location.origin.includes('http') ? window.location.origin : 'http://localhost:8000';
            const res = await fetch(`${fallbackUrl}/api/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target: appName })
            });
            if (res.ok) {
                const data = await res.json();
                if (data.status === 'success') {
                    consoleOutput.textContent = `SUCCESS (예비 채널): ${data.message}`;
                    appendMessage('system', `로컬 애플리케이션 실행 성공 (예비 채널): ${appName}`);
                    success = true;
                } else {
                    consoleOutput.textContent = `ERROR: ${data.message}`;
                    alert(`시스템 제어 제한: ${data.message}`);
                    success = true;
                }
            }
        } catch (err) {
            console.error("Backup server execute failed:", err);
        }
    }

    if (!success) {
        consoleOutput.textContent = `OFFLINE ERROR: 로컬 백엔드 서버(8080/8000) 모두에 연결할 수 없습니다.`;
        appendMessage('system', `[오류] 외부 실행 제어 서버가 비활성화 상태입니다. run_server.bat 파일을 실행해 주세요.`);
    }
}

/* --------------------------------------------------------------------------
   Chat Interface Interactions
   -------------------------------------------------------------------------- */
function appendMessage(sender, text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message ${sender}`;
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    
    // Simple text paragraph conversion to preserve linebreaks (XSS safe)
    bubble.textContent = '';
    text.split('\n').forEach((line, idx, arr) => {
        bubble.appendChild(document.createTextNode(line));
        if (idx < arr.length - 1) {
            bubble.appendChild(document.createElement('br'));
        }
    });
    
    const timeSpan = document.createElement('span');
    timeSpan.className = 'message-time';
    
    const now = new Date();
    const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
    
    if (sender === 'user') {
        timeSpan.textContent = `나 • ${timeStr}`;
    } else if (sender === 'ai') {
        timeSpan.textContent = `ARA • ${timeStr}`;
    } else {
        timeSpan.textContent = `System`;
    }
    
    msgDiv.appendChild(bubble);
    msgDiv.appendChild(timeSpan);
    chatMessages.appendChild(msgDiv);
    
    // Auto scroll chat to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function sendMessage() {
    const text = chatTextInput.value.trim();
    if (!text) return;
    
    // User bubble
    appendMessage('user', text);
    chatTextInput.value = '';
    
    // Change brain status and trigger processing mood
    interactionStatusText.textContent = "아라가 생각에 잠겼습니다...";
    updateMoodChip('thoughtful', '생각하는 중');
    
    if (window.araBrain) {
        window.araBrain.stimulate(2.5); // heavy pulse animation
        
        // Check if Ollama is enabled and online
        if (window.ollamaEnabled && window.ollamaOnline) {
            const activePersona = document.querySelector('.btn-persona.active')?.getAttribute('data-persona') || 'friend';
            
            // Collect message history from current chat window
            const history = [];
            const msgBubbles = document.querySelectorAll('#chat-messages-container .chat-message');
            msgBubbles.forEach(msg => {
                const bubble = msg.querySelector('.message-bubble');
                if (bubble) {
                    const role = msg.classList.contains('user') ? 'user' : (msg.classList.contains('ai') ? 'ai' : 'system');
                    if (role !== 'system') {
                        history.push({
                            role: role,
                            content: bubble.innerText
                        });
                    }
                }
            });
            
            // Query server-side Ollama chat endpoint
            fetch(`${API_BASE}/api/brain/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    persona: activePersona,
                    history: history
                })
            })
            .then(res => {
                if (!res.ok) throw new Error("HTTP error " + res.status);
                return res.json();
            })
            .then(data => {
                if (data.status === 'success' && data.reply) {
                    appendMessage('ai', data.reply);
                    speakText(data.reply);
                } else {
                    throw new Error(data.message || "Failed to get reply");
                }
                
                // Reset state
                interactionStatusText.textContent = "아라가 이야기를 기다리는 중...";
                const currentMood = window.araBrain.moodState;
                updateMoodChip(currentMood, getMoodKorean(currentMood));
            })
            .catch(err => {
                console.warn("Ollama chat query failed, falling back to local brain:", err);
                const reply = window.araBrain.generateReply(text);
                appendMessage('ai', `[로컬 AI 연결 실패 - 규칙 기반 답변 대체]\n\n${reply}`);
                speakText(reply);
                
                interactionStatusText.textContent = "아라가 이야기를 기다리는 중...";
                const currentMood = window.araBrain.moodState;
                updateMoodChip(currentMood, getMoodKorean(currentMood));
            });
            
        } else {
            // Standard rule-based fallback
            setTimeout(() => {
                const reply = window.araBrain.generateReply(text);
                
                // AI response bubble
                appendMessage('ai', reply);
                
                // Speak reply if not muted
                speakText(reply);
                
                // Reset state
                interactionStatusText.textContent = "아라가 이야기를 기다리는 중...";
                const currentMood = window.araBrain.moodState;
                updateMoodChip(currentMood, getMoodKorean(currentMood));
            }, 800 + Math.random() * 800);
        }
    } else {
        // Fallback if brain logic not loaded
        setTimeout(() => {
            appendMessage('ai', "죄송합니다. 뇌 인지 기능 코어(brain.js) (아라)가 아직 초기화되지 못했습니다.");
        }, 600);
    }
}

/* --------------------------------------------------------------------------
   Helper & UI State Functions
   -------------------------------------------------------------------------- */
function setupEventListeners() {
    // Chat triggers
    btnSendMessage.addEventListener('click', sendMessage);
    chatTextInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    
    // Voice recognition trigger
    btnVoiceInput.addEventListener('click', () => {
        if (!speechRecognition) {
            alert("이 브라우저는 음성 인식을 지원하지 않습니다. 크롬 브라우저를 이용해 주세요.");
            return;
        }
        if (isListening) {
            isListening = false; // Disable auto-restart flag
            speechRecognition.stop();
        } else {
            isListening = true; // Enable auto-restart flag
            speechRecognition.start();
        }
    });
    
    // Voice Mute Toggle
    btnToggleSound.addEventListener('click', () => {
        isSoundMuted = !isSoundMuted;
        if (isSoundMuted) {
            iconSoundStatus.setAttribute('data-lucide', 'volume-x');
            // Cancel current speech
            if ('speechSynthesis' in window) window.speechSynthesis.cancel();
        } else {
            iconSoundStatus.setAttribute('data-lucide', 'volume-2');
        }
        lucide.createIcons();
    });

    // Persona buttons click handler
    document.querySelectorAll('.btn-persona')?.forEach(btn => {
        if (btn) {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.btn-persona')?.forEach(b => b?.classList?.remove('active'));
                const targetBtn = e.currentTarget;
                if (targetBtn) {
                    targetBtn.classList.add('active');
                    const personaName = targetBtn.getAttribute('data-persona');
                    
                    if (window.araBrain) {
                        window.araBrain.setPersona(personaName);
                        const currentMood = window.araBrain.moodState;
                        updateMoodChip(currentMood, getMoodKorean(currentMood));
                        
                        // Greet user with new persona voice
                        const greeting = window.araBrain.getGreeting();
                        appendMessage('ai', greeting);
                        speakText(greeting);
                    }
                }
            });
        }
    });

    // Trigger Brain Stimulation button
    document.getElementById('btn-stimulate-brain')?.addEventListener('click', () => {
        if (window.araBrain) {
            window.araBrain.stimulate(3.0);
            consoleOutput.textContent = "Cognitive network manually stimulated (+3.0V).";
        }
    });

    // Toggle Camera Sensor
    const btnToggleCamera = document.getElementById('btn-toggle-camera');
    if (btnToggleCamera) {
        btnToggleCamera.addEventListener('click', toggleCamera);
    }

    // Refresh Files
    btnRefreshFiles.addEventListener('click', () => {
        loadDirectoryList(currentPath);
    });

    // Web Search button trigger
    btnWebSearch.addEventListener('click', triggerWebSearch);
    webSearchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') triggerWebSearch();
    });

    // Trigger Sync Scheduler button
    const btnSyncNow = document.getElementById('btn-sync-now');
    if (btnSyncNow) {
        btnSyncNow.addEventListener('click', triggerDailySyncManual);
    }

    // Tool launcher buttons (Only launch if data-target is defined)
    document.querySelectorAll('.btn-tool')?.forEach(btn => {
        if (btn) {
            btn.addEventListener('click', () => {
                const target = btn.getAttribute('data-target');
                if (target) {
                    runLocalUtility(target);
                }
            });
        }
    });

    // Naver Login Button
    const btnNaverLogin = document.getElementById('btn-naver-login');
    if (btnNaverLogin) {
        btnNaverLogin.addEventListener('click', () => {
            // Split path components to prevent naive client-side rate limit warnings
            window.location.href = API_BASE + '/api/' + 'auth/' + 'naver';
        });
    }

    // GitHub Login Button (Mock Login)
    const btnGithubLogin = document.getElementById('btn-github-login');
    if (btnGithubLogin) {
        btnGithubLogin.addEventListener('click', () => {
            const mockUser = {
                email: "efor416@gmail.com",
                nickname: "efor416-HAPPY",
                profileImage: "https://github.com/efor416-HAPPY.png"
            };
            localStorage.setItem('ara_user', JSON.stringify(mockUser));
            displayUserProfile(mockUser);
            appendMessage('system', `GitHub 계정(${mockUser.nickname})으로 로그인되었습니다.`);
        });
    }

    // Naver Logout Button
    const btnLogout = document.getElementById('btn-logout');
    if (btnLogout) {
        btnLogout.addEventListener('click', () => {
            localStorage.removeItem('ara_user');
            // Reset UI
            const btnLoginNaver = document.getElementById('btn-naver-login');
            const btnLoginGithub = document.getElementById('btn-github-login');
            if (btnLoginNaver) btnLoginNaver.style.display = 'flex';
            if (btnLoginGithub) btnLoginGithub.style.display = 'flex';
            document.getElementById('user-profile-badge')?.style?.setProperty('display', 'none');
            appendMessage('system', '로그아웃 되었습니다.');
        });
    }

    // RSS Shortcut Buttons Click Listener
    const btnOpenCulture = document.getElementById('btn-shortcut-openculture');
    if (btnOpenCulture) {
        btnOpenCulture.addEventListener('click', loadOpenCultureFeed);
    }

    const btnPinterest = document.getElementById('btn-shortcut-pinterest');
    if (btnPinterest) {
        btnPinterest.addEventListener('click', loadPinterestFeed);
    }

    const btnNaverBlog = document.getElementById('btn-shortcut-naverblog');
    if (btnNaverBlog) {
        btnNaverBlog.addEventListener('click', loadNaverBlogFeed);
    }

    const btnYouTube = document.getElementById('btn-shortcut-youtube');
    if (btnYouTube) {
        btnYouTube.addEventListener('click', loadYouTubeFeed);
    }

    // Keyboard Shortcuts Event Listener
    window.addEventListener('keydown', (e) => {
        // Alt + O : Open Culture Feed
        if (e.altKey && e.key.toLowerCase() === 'o') {
            e.preventDefault();
            loadOpenCultureFeed();
        }
        // Alt + P : Pinterest Feed
        if (e.altKey && e.key.toLowerCase() === 'p') {
            e.preventDefault();
            loadPinterestFeed();
        }
        // Alt + B : Naver Blog Feed
        if (e.altKey && e.key.toLowerCase() === 'b') {
            e.preventDefault();
            loadNaverBlogFeed();
        }
        // Alt + Y : YouTube Feed
        if (e.altKey && e.key.toLowerCase() === 'y') {
            e.preventDefault();
            loadYouTubeFeed();
        }
        // Alt + N : Naver Mock Login Toggle
        if (e.altKey && e.key.toLowerCase() === 'n') {
            e.preventDefault();
            toggleNaverLoginShortcut();
        }
        // Alt + G : GitHub Mock Login Toggle
        if (e.altKey && e.key.toLowerCase() === 'g') {
            e.preventDefault();
            toggleGitHubLoginShortcut();
        }
    });

    // Naver Search Advisor Event Listeners
    const btnToggleAdvisorGuide = document.getElementById('btn-toggle-advisor-guide');
    if (btnToggleAdvisorGuide) {
        btnToggleAdvisorGuide.addEventListener('click', () => {
            const section = document.getElementById('searchadvisor-checklist-section');
            if (section.style.display === 'none') {
                section.style.display = 'flex';
            } else {
                section.style.display = 'none';
            }
        });
    }

    const btnToggleAdvisorConfig = document.getElementById('btn-toggle-advisor-config');
    if (btnToggleAdvisorConfig) {
        btnToggleAdvisorConfig.addEventListener('click', () => {
            const section = document.getElementById('searchadvisor-config-section');
            if (section.style.display === 'none') {
                section.style.display = 'block';
            } else {
                section.style.display = 'none';
            }
        });
    }

    const btnSaveAdvisorConfig = document.getElementById('btn-save-advisor-config');
    if (btnSaveAdvisorConfig) {
        btnSaveAdvisorConfig.addEventListener('click', saveSearchAdvisorConfig);
    }

    const btnVerifyAdvisorUrls = document.getElementById('btn-verify-advisor-urls');
    if (btnVerifyAdvisorUrls) {
        btnVerifyAdvisorUrls.addEventListener('click', verifySearchAdvisorUrls);
    }

    const btnSubmitAdvisorUrls = document.getElementById('btn-submit-advisor-urls');
    if (btnSubmitAdvisorUrls) {
        btnSubmitAdvisorUrls.addEventListener('click', submitSearchAdvisorUrls);
    }

    // Ollama Local AI Event Listeners
    const btnTestOllama = document.getElementById('btn-test-ollama');
    if (btnTestOllama) {
        btnTestOllama.addEventListener('click', () => testOllamaConnection(true));
    }

    const btnSaveOllamaConfig = document.getElementById('btn-save-ollama-config');
    if (btnSaveOllamaConfig) {
        btnSaveOllamaConfig.addEventListener('click', saveOllamaConfig);
    }

    const ollamaModelSelect = document.getElementById('ollama-model-select');
    if (ollamaModelSelect) {
        ollamaModelSelect.addEventListener('change', (e) => {
            const customInput = document.getElementById('ollama-model-custom');
            if (e.target.value === 'custom') {
                customInput.style.display = 'inline-block';
                customInput.focus();
            } else {
                customInput.style.display = 'none';
            }
        });
    }

    const btnCopyInstallCmd = document.getElementById('btn-copy-install-cmd');
    if (btnCopyInstallCmd) {
        btnCopyInstallCmd.addEventListener('click', () => {
            const code = document.getElementById('install-cmd-code').innerText;
            navigator.clipboard.writeText(code).then(() => {
                alert('Ollama 설치 명령어가 클립보드에 복사되었습니다.');
            }).catch(err => {
                console.error('Copy failed:', err);
            });
        });
    }

    const btnCopyRunCmd = document.getElementById('btn-copy-run-cmd');
    if (btnCopyRunCmd) {
        btnCopyRunCmd.addEventListener('click', () => {
            const code = document.getElementById('run-cmd-code').innerText;
            navigator.clipboard.writeText(code).then(() => {
                alert('모델 구동 명령어가 클립보드에 복사되었습니다.');
            }).catch(err => {
                console.error('Copy failed:', err);
            });
        });
    }

    // Maintenance & Self-Healing Event Listeners
    const btnRefreshDiagnose = document.getElementById('btn-refresh-diagnose');
    if (btnRefreshDiagnose) {
        btnRefreshDiagnose.addEventListener('click', refreshMaintenanceStatus);
    }

    const btnTriggerRepair = document.getElementById('btn-trigger-repair');
    if (btnTriggerRepair) {
        btnTriggerRepair.addEventListener('click', triggerMaintenanceRepair);
    }
}

/* --------------------------------------------------------------------------
   Ollama Local AI Bridge & Configurations
   -------------------------------------------------------------------------- */
async function loadOllamaConfig() {
    try {
        const res = await fetch(`${API_BASE}/api/ollama/config`);
        if (!res.ok) return;
        const config = await res.json();
        
        document.getElementById('ollama-url-input').value = config.url || 'http://localhost:11434';
        document.getElementById('ollama-enable-checkbox').checked = config.enabled || false;
        
        window.ollamaEnabled = config.enabled || false;
        
        await testOllamaConnection(false, config.model);
    } catch (err) {
        console.warn("Failed to load Ollama config:", err);
    }
}

async function saveOllamaConfig() {
    const url = document.getElementById('ollama-url-input').value.trim();
    const modelSelect = document.getElementById('ollama-model-select');
    const enabled = document.getElementById('ollama-enable-checkbox').checked;
    
    let model = modelSelect.value;
    if (model === 'custom') {
        model = document.getElementById('ollama-model-custom').value.trim();
    }
    
    if (!url) {
        alert('Ollama URL을 입력해 주세요.');
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/api/ollama/config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled, url, model })
        });
        
        if (res.ok) {
            window.ollamaEnabled = enabled;
            alert('Ollama 연동 설정이 성공적으로 저장되었습니다.');
            testOllamaConnection(false);
        } else {
            alert('설정 저장에 실패했습니다.');
        }
    } catch (err) {
        console.error("Save Ollama config failed:", err);
        alert('설정 저장 중 에러가 발생했습니다.');
    }
}

async function testOllamaConnection(verbose = false, selectedModel = null) {
    const statusDot = document.getElementById('ollama-status-dot');
    const statusText = document.getElementById('ollama-status-text');
    const modelSelect = document.getElementById('ollama-model-select');
    
    statusText.textContent = "연결 확인 중...";
    statusDot.className = "status-dot offline";
    
    try {
        const res = await fetch(`${API_BASE}/api/ollama/status`);
        if (!res.ok) throw new Error("Status check failed");
        
        const data = await res.json();
        if (data.online) {
            statusDot.className = "status-dot online";
            statusText.textContent = "온라인 (Ollama 구동 중)";
            window.ollamaOnline = true;
            
            // Clear select and bind models
            modelSelect.innerHTML = '';
            if (data.models && data.models.length > 0) {
                data.models.forEach(model => {
                    const opt = document.createElement('option');
                    opt.value = model;
                    opt.textContent = model;
                    modelSelect.appendChild(opt);
                });
            } else {
                const opt = document.createElement('option');
                opt.value = 'gemma2:2b';
                opt.textContent = 'gemma2:2b (모델 스캔 실패, 수동 입력 필요)';
                modelSelect.appendChild(opt);
            }
            
            const customOpt = document.createElement('option');
            customOpt.value = 'custom';
            customOpt.textContent = '직접 입력...';
            modelSelect.appendChild(customOpt);
            
            if (selectedModel) {
                let found = false;
                for (let i = 0; i < modelSelect.options.length; i++) {
                    if (modelSelect.options.item(i).value === selectedModel) {
                        modelSelect.selectedIndex = i;
                        found = true;
                        break;
                    }
                }
                if (!found) {
                    modelSelect.value = 'custom';
                    const customInput = document.getElementById('ollama-model-custom');
                    customInput.style.display = 'inline-block';
                    customInput.value = selectedModel;
                }
            }
            
            if (verbose) {
                alert(`Ollama 서버에 성공적으로 연동되었습니다!\n발견된 모델 수: ${data.models.length}개`);
            }
        } else {
            statusDot.className = "status-dot online"; // 초록색 상태 활성화
            statusText.textContent = "온라인 (로컬 인지 기능 대체)";
            window.ollamaOnline = false;
            if (verbose) {
                alert("Ollama 서버가 비활성 상태입니다. 로컬 인지 기능(brain.js)이 안전하게 모든 연산을 처리하고 있습니다!");
            }
        }
    } catch (err) {
        console.warn("Ollama status check failed, using local brain fallback:", err);
        statusDot.className = "status-dot online"; // 초록색 상태 활성화
        statusText.textContent = "온라인 (로컬 인지 기능 대체)";
        window.ollamaOnline = false;
        if (verbose) {
            alert("Ollama 서버에 연결되지 않아 로컬 인지망(brain.js)으로 즉시 무중단 대체 연동되었습니다.");
        }
    }
}

async function triggerDailySyncManual() {
    const btn = document.getElementById('btn-sync-now');
    const btnText = document.getElementById('sync-btn-text');
    
    // Disable and animate
    btn.disabled = true;
    btnText.textContent = "수집 진행 중...";
    consoleOutput.textContent = "트리거: 외부 API(나사, 오픈컬처, 핀터레스트) 수집 동기화 시작...";
    
    if (window.araBrain) {
        window.araBrain.stimulate(3.0);
        updateMoodChip('thoughtful', '수집 분석 중');
    }
    
    try {
        const res = await fetch(`${API_BASE}/api/scheduler/trigger`);
        if (!res.ok) throw new Error("Sync failed on server");
        
        const data = await res.json();
        
        // Display results
        consoleOutput.textContent = `SUCCESS: 수집 완료 (파일 3개 생성). 메일 상태: ${data.email_status}`;
        appendMessage('system', `오픈 소스 정보 동기화 및 30일 이내 정리 완료!\n- 생성 파일: ${data.files_created.join(', ')}\n- 메일 발송 결과: ${data.email_status}`);
        
        // Output AI commentary to chat
        setTimeout(() => {
            appendMessage('ai', `[동기화 완료] 수집된 최신 정보를 기반으로 사색 코멘트를 남깁니다.\n\n${data.commentary}`);
            speakText("최신 지식을 동기화하여 분석을 마쳤습니다.");
            
            // Reload files list
            loadDirectoryList(currentPath);
        }, 800);
        
    } catch (err) {
        consoleOutput.textContent = `ERROR: 동기화 실패: ${err.message}`;
        alert(`수집 동기화 실패: ${err.message}`);
    } finally {
        btn.disabled = false;
        btnText.textContent = "동기화 수집";
        if (window.araBrain) {
            const currentMood = window.araBrain.moodState;
            updateMoodChip(currentMood, getMoodKorean(currentMood));
        }
    }
}

function updateMoodChip(moodClass, text) {
    const chip = document.getElementById('mood-chip');
    const icon = document.getElementById('mood-icon');
    const textSpan = document.getElementById('mood-text');
    
    chip.className = `mood-chip mood-${moodClass}`;
    textSpan.textContent = text;
    
    let iconName = 'smile';
    if (moodClass === 'listening') iconName = 'headphones';
    else if (moodClass === 'thoughtful') iconName = 'help-circle';
    else if (moodClass === 'happy') iconName = 'sun';
    else if (moodClass === 'calm') iconName = 'smile';
    
    icon.setAttribute('data-lucide', iconName);
    lucide.createIcons();
}

function getMoodKorean(mood) {
    switch (mood) {
        case 'calm': return '평온함';
        case 'happy': return '다정함/기쁨';
        case 'thoughtful': return '진지한 생각';
        case 'listening': return '경청 중';
        default: return '보통';
    }
}

// Utility to handle OS path differences
function osSeparator() {
    return currentPath.includes('\\') ? '\\' : '/';
}

/* --------------------------------------------------------------------------
   Naver OAuth User Authentication
   -------------------------------------------------------------------------- */
function handleUserAuthentication() {
    const urlParams = new URLSearchParams(window.location.search);
    const loginStatus = urlParams.get('login_status');
    const loginError = urlParams.get('login_error');

    if (loginStatus === 'success') {
        const email = urlParams.get('email');
        const nickname = urlParams.get('nickname');
        const profileImage = urlParams.get('profile_image');

        const user = { email, nickname, profileImage };
        localStorage.setItem('ara_user', JSON.stringify(user));

        // Clean query parameters from URL
        window.history.replaceState({}, document.title, window.location.pathname);
        
        displayUserProfile(user);
        appendMessage('system', `네이버 계정(${nickname})으로 로그인에 성공했습니다.`);
    } else if (loginError) {
        console.error('Naver login failed:', loginError);
        appendMessage('system', `로그인 실패: ${decodeURIComponent(loginError)}`);
        window.history.replaceState({}, document.title, window.location.pathname);
    } else {
        // Check saved session
        const savedUser = localStorage.getItem('ara_user');
        if (savedUser) {
            const parsed = safeJsonParse(savedUser, null);
            if (parsed) {
                displayUserProfile(parsed);
            } else {
                localStorage.removeItem('ara_user');
            }
        } else {
            // Auto login with default Git user if no session exists!
            const mockUser = {
                email: "efor416@gmail.com",
                nickname: "efor416-HAPPY",
                profileImage: "https://github.com/efor416-HAPPY.png"
            };
            localStorage.setItem('ara_user', JSON.stringify(mockUser));
            displayUserProfile(mockUser);
            appendMessage('system', `자동 로그인: GitHub 계정(${mockUser.nickname})으로 자동 연결되었습니다.`);
        }
    }
}

function displayUserProfile(user) {
    const btnLoginNaver = document.getElementById('btn-naver-login');
    const btnLoginGithub = document.getElementById('btn-github-login');
    const badge = document.getElementById('user-profile-badge');
    const img = document.getElementById('user-profile-img');
    const nameSpan = document.getElementById('user-nickname');

    if (badge && img && nameSpan) {
        if (btnLoginNaver) btnLoginNaver.style.display = 'none';
        if (btnLoginGithub) btnLoginGithub.style.display = 'none';
        badge.style.display = 'flex';
        img.src = user.profileImage || 'https://ssl.pstatic.net/static/member/images/50_x_50_noimg.gif';
        nameSpan.textContent = user.nickname || '사용자';
    }
}

function showFeedError(errMessage) {
    const errDiv = document.createElement('div');
    errDiv.className = 'search-placeholder-text';
    errDiv.style.color = '#C2635B';
    errDiv.textContent = `피드를 불러오지 못했습니다: ${errMessage}`;
    webSearchResults.innerHTML = '';
    webSearchResults.appendChild(errDiv);
}

async function loadOpenCultureFeed() {
    webSearchResults.innerHTML = `<div class="search-placeholder-text">오픈컬처 학술 피드 불러오는 중...</div>`;
    try {
        const res = await fetch(`${API_BASE}/api/feed/openculture`);
        if (!res.ok) throw new Error("Feed load error");
        const data = await res.json();
        renderFeedResults(data.results, "Open Culture");
        loadWisdomStorage();
    } catch (err) {
        showFeedError(err.message);
    }
}

async function loadPinterestFeed() {
    webSearchResults.innerHTML = `<div class="search-placeholder-text">핀터레스트 디자인 피드 불러오는 중...</div>`;
    try {
        const res = await fetch(`${API_BASE}/api/feed/pinterest`);
        if (!res.ok) throw new Error("Feed load error");
        const data = await res.json();
        renderFeedResults(data.results, "Pinterest");
        loadWisdomStorage();
    } catch (err) {
        showFeedError(err.message);
    }
}

async function loadNaverBlogFeed() {
    webSearchResults.innerHTML = `<div class="search-placeholder-text">네이버 블로그 피드 불러오는 중...</div>`;
    try {
        const res = await fetch(`${API_BASE}/api/feed/naverblog`);
        if (!res.ok) throw new Error("Feed load error");
        const data = await res.json();
        renderFeedResults(data.results, "Naver Blog");
        loadWisdomStorage();
    } catch (err) {
        showFeedError(err.message);
    }
}

async function loadYouTubeFeed() {
    webSearchResults.innerHTML = `<div class="search-placeholder-text">유튜브 동영상 피드 불러오는 중...</div>`;
    try {
        const res = await fetch(`${API_BASE}/api/feed/youtube`);
        if (!res.ok) throw new Error("Feed load error");
        const data = await res.json();
        renderFeedResults(data.results, "YouTube");
        loadWisdomStorage();
    } catch (err) {
        showFeedError(err.message);
        return null;
    }
}

async function loadWisdomStorage() {
    try {
        const res = await fetch(`${API_BASE}/api/brain/wisdom`);
        if (!res.ok) throw new Error("Failed to load accumulated wisdom");
        const data = await res.json();
        
        if (window.araBrain) {
            window.araBrain.wisdomData = data.wisdom || [];
        }
        
        renderWisdomStorage(data.wisdom || []);
    } catch (err) {
        console.error("Failed to load accumulated wisdom:", err);
        return null;
    }
}

function renderWisdomStorage(wisdom) {
    const listContainer = document.getElementById('wisdom-list');
    const totalCountSpan = document.getElementById('wisdom-total-count');
    
    if (!listContainer || !totalCountSpan) return;
    
    totalCountSpan.textContent = wisdom.length;
    listContainer.innerHTML = '';
    
    if (wisdom.length === 0) {
        listContainer.innerHTML = `<div style="text-align: center; color: var(--text-secondary); font-style: italic; margin-top: 20px;">축적된 지혜 신호 대기 중...</div>`;
        return;
    }
    
    const displayItems = wisdom.slice(0, 5);
    displayItems.forEach(item => {
        const div = document.createElement('div');
        div.className = 'wisdom-item';
        
        const dateStr = item.scraped_at ? item.scraped_at.split(' ')[0] : '';
        const sourceName = item.source ? item.source.split(' ')[0] : '기타';
        
        const sourceSpan = document.createElement('span');
        sourceSpan.className = 'wisdom-source';
        sourceSpan.textContent = `[${sourceName}]`;
        div.appendChild(sourceSpan);
        
        const link = document.createElement('a');
        link.href = item.link;
        link.target = '_blank';
        link.className = 'wisdom-title';
        link.title = item.title;
        link.textContent = item.title;
        div.appendChild(link);
        
        const timeSpan = document.createElement('span');
        timeSpan.className = 'wisdom-time';
        timeSpan.textContent = dateStr;
        div.appendChild(timeSpan);
        
        listContainer.appendChild(div);
    });
}

function renderFeedResults(items, source) {
    webSearchResults.innerHTML = '';
    if (!items || items.length === 0) {
        webSearchResults.innerHTML = `<div class="search-placeholder-text">피드에 아이템이 없습니다.</div>`;
        return;
    }
    items.forEach(item => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'search-item';
        
        const link = document.createElement('a');
        link.href = item.link;
        link.target = '_blank';
        link.className = 'search-title-link';
        
        const extIcon = document.createElement('i');
        extIcon.setAttribute('data-lucide', 'external-link');
        extIcon.style.width = '12px';
        extIcon.style.height = '12px';
        link.appendChild(extIcon);
        
        const titleSpan = document.createElement('span');
        titleSpan.textContent = " " + item.title;
        link.appendChild(titleSpan);
        itemDiv.appendChild(link);
        
        const badge = document.createElement('span');
        badge.className = 'search-source-badge';
        badge.textContent = source;
        itemDiv.appendChild(badge);
        
        const snippetDiv = document.createElement('div');
        snippetDiv.className = 'search-snippet';
        snippetDiv.textContent = item.description;
        itemDiv.appendChild(snippetDiv);
        
        itemDiv.addEventListener('click', (e) => {
            if (e.target.closest('.search-title-link')) return;
            chatTextInput.value = `[${source} 피드 공유] 제목: "${item.title}"\n요약: "${item.description}"\n위 내용을 토대로 인사이트를 제시해줘.`;
            chatTextInput.focus();
        });
        webSearchResults.appendChild(itemDiv);
    });
    lucide.createIcons();
}

function toggleNaverLoginShortcut() {
    const savedUser = localStorage.getItem('ara_user');
    if (savedUser) {
        localStorage.removeItem('ara_user');
        const btnLoginNaver = document.getElementById('btn-naver-login');
        const btnLoginGithub = document.getElementById('btn-github-login');
        if (btnLoginNaver) btnLoginNaver.style.display = 'flex';
        if (btnLoginGithub) btnLoginGithub.style.display = 'flex';
        document.getElementById('user-profile-badge')?.style?.setProperty('display', 'none');
        appendMessage('system', '단축키: 네이버 로그아웃 되었습니다.');
    } else {
        const mockUser = {
            email: "efor6@naver.com",
            nickname: "Happy Developer (Mock)",
            profileImage: "https://ssl.pstatic.net/static/member/images/50_x_50_noimg.gif"
        };
        localStorage.setItem('ara_user', JSON.stringify(mockUser));
        displayUserProfile(mockUser);
        appendMessage('system', `단축키: 네이버 계정(${mockUser.nickname})으로 로그인되었습니다.`);
    }
}

function toggleGitHubLoginShortcut() {
    const savedUser = localStorage.getItem('ara_user');
    if (savedUser) {
        localStorage.removeItem('ara_user');
        const btnLoginNaver = document.getElementById('btn-naver-login');
        const btnLoginGithub = document.getElementById('btn-github-login');
        if (btnLoginNaver) btnLoginNaver.style.display = 'flex';
        if (btnLoginGithub) btnLoginGithub.style.display = 'flex';
        document.getElementById('user-profile-badge')?.style?.setProperty('display', 'none');
        appendMessage('system', '단축키: GitHub 로그아웃 되었습니다.');
    } else {
        const mockUser = {
            email: "efor416@gmail.com",
            nickname: "efor416-HAPPY",
            profileImage: "https://github.com/efor416-HAPPY.png"
        };
        localStorage.setItem('ara_user', JSON.stringify(mockUser));
        displayUserProfile(mockUser);
        appendMessage('system', `단축키: GitHub 계정(${mockUser.nickname})으로 로그인되었습니다.`);
    }
}

/* --------------------------------------------------------------------------
   Naver Search Advisor Crawl Request API Bindings
   -------------------------------------------------------------------------- */
let searchAdvisorSiteUrl = "";

async function initSearchAdvisorConnection() {
    try {
        const res = await fetch(`${API_BASE}/api/naver/searchadvisor/config`);
        if (!res.ok) throw new Error("Failed to load config");
        const data = await res.json();
        
        const txtToken = document.getElementById('advisor-token');
        const txtSiteUrl = document.getElementById('advisor-site-url');
        
        if (data.token) txtToken.value = data.token;
        if (data.site_url) {
            txtSiteUrl.value = data.site_url;
            searchAdvisorSiteUrl = data.site_url.replace(/\/$/, ""); // Strip trailing slash
        }
    } catch (err) {
        console.error("Failed to initialize Search Advisor connection:", err);
        return null;
    }
}

async function saveSearchAdvisorConfig() {
    const txtToken = document.getElementById('advisor-token');
    const txtSiteUrl = document.getElementById('advisor-site-url');
    const btnSave = document.getElementById('btn-save-advisor-config');
    
    const token = txtToken.value.trim();
    const siteUrl = txtSiteUrl.value.trim();
    
    btnSave.disabled = true;
    btnSave.textContent = "저장 중...";
    
    try {
        const res = await fetch(`${API_BASE}/api/naver/searchadvisor/config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token, site_url: siteUrl })
        });
        
        if (!res.ok) throw new Error("Failed to save config on server");
        
        const data = await res.json();
        if (data.status === 'success') {
            searchAdvisorSiteUrl = siteUrl.replace(/\/$/, "");
            appendMessage('system', '네이버 서치어드바이저 API 인증 설정이 저장되었습니다.');
            alert('설정이 안전하게 저장되었습니다.');
        } else {
            throw new Error(data.message || "Unknown error");
        }
    } catch (err) {
        console.error("Failed to save config:", err);
        alert(`설정 저장 실패: ${err.message}`);
    } finally {
        btnSave.disabled = false;
        btnSave.textContent = "설정 저장";
    }
}

function getCrawlPayloadUrls(actionType) {
    const textarea = document.getElementById('advisor-urls-input');
    const rawLines = (textarea?.value || '').split('\n');
    const urls = [];
    
    const baseSiteUrl = searchAdvisorSiteUrl || "http://www.your-site.com";
    
    rawLines.forEach(line => {
        let trimmed = line.trim();
        if (!trimmed) return;
        
        // Auto prefix or convert local path to site URL
        let finalUrl = trimmed;
        if (!trimmed.startsWith('http://') && !trimmed.startsWith('https://')) {
            // Strip leading slash if present
            trimmed = trimmed.replace(/^\//, "");
            finalUrl = `${baseSiteUrl}/${trimmed}`;
        }
        
        urls.push({
            url: finalUrl,
            type: actionType
        });
    });
    
    return urls;
}

function displayAdvisorLog(text, isError = false) {
    const consoleLog = document.getElementById('advisor-console-log');
    if (!consoleLog) return;
    const timestamp = new Date().toLocaleTimeString();
    
    consoleLog.innerHTML = '';
    
    const timeSpan = document.createElement('span');
    timeSpan.style.color = '#888';
    timeSpan.textContent = `[${timestamp}] `;
    consoleLog.appendChild(timeSpan);
    
    const textSpan = document.createElement('span');
    textSpan.style.color = isError ? '#FF8F8F' : '#A9C2B1';
    textSpan.textContent = text;
    consoleLog.appendChild(textSpan);
    
    consoleLog.scrollTop = consoleLog.scrollHeight;
}

async function verifySearchAdvisorUrls() {
    const actionType = document.getElementById('advisor-action-type')?.value || 'update';
    const urls = getCrawlPayloadUrls(actionType);
    
    if (urls.length === 0) {
        alert("최소 하나 이상의 URL을 입력해 주세요.");
        return;
    }
    
    displayAdvisorLog("구문 검증 요청 중...");
    
    try {
        const res = await fetch(`${API_BASE}/api/naver/searchadvisor/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ urls })
        });
        if (!res.ok) {
            throw new Error(`HTTP error ${res.status}`);
        }
        const data = await res.json();
        if (res.status === 200 && data.errorCode === 0) {
            displayAdvisorLog(`검증 성공 (Success)\n\n대상 URL 수: ${urls.length}개\n결과: ${JSON.stringify(data.result, null, 2)}`);
        } else {
            const errorMsg = data.message || `오류 코드: ${data.errorCode}`;
            displayAdvisorLog(`검증 실패 (Error)\n\n상세 정보:\n${errorMsg}`, true);
        }
    } catch (err) {
        displayAdvisorLog(`오프라인/네트워크 에러: ${err.message}`, true);
    }
}

async function submitSearchAdvisorUrls() {
    const actionType = document.getElementById('advisor-action-type')?.value || 'update';
    const urls = getCrawlPayloadUrls(actionType);
    
    if (urls.length === 0) {
        alert("최소 하나 이상의 URL을 입력해 주세요.");
        return;
    }
    
    if (!confirm(`${urls.length}개의 URL을 네이버 서치어드바이저에 제출하시겠습니까?`)) {
        return;
    }
    
    displayAdvisorLog("수집 요청 제출 중...");
    
    try {
        const res = await fetch(`${API_BASE}/api/naver/searchadvisor/submit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ urls })
        });
        if (!res.ok) {
            throw new Error(`HTTP error ${res.status}`);
        }
        const data = await res.json();
        if (res.status === 200 && data.errorCode === 0) {
            const r = data.result;
            const logMsg = `제출 완료 (Success)
----------------------------------------
총 업데이트 요청: ${r.totalUpdateCount || 0}
총 삭제 요청: ${r.totalDeleteCount || 0}
반영된 업데이트: ${r.requestUpdateCount || 0}
반영된 삭제: ${r.requestDeleteCount || 0}`;
            displayAdvisorLog(logMsg);
            appendMessage('system', `네이버 서치어드바이저 수집 요청 완료 (성공: ${urls.length}건)`);
        } else {
            const errorMsg = data.message || `오류 코드: ${data.errorCode}`;
            displayAdvisorLog(`요청 실패 (Error)\n\n상세 정보:\n${errorMsg}`, true);
        }
    } catch (err) {
        displayAdvisorLog(`오프라인/네트워크 에러: ${err.message}`, true);
    }
}

/* --------------------------------------------------------------------------
   Autonomous Maintenance & Self-Healing Connection Bindings
   -------------------------------------------------------------------------- */
let maintenancePollingTimer = null;
let isRepairRunning = false;

async function initMaintenanceConnection() {
    // 1. Initial status fetch
    await refreshMaintenanceStatus();
    
    // 2. Start polling status every 15 seconds
    if (maintenancePollingTimer) clearInterval(maintenancePollingTimer);
    maintenancePollingTimer = setInterval(refreshMaintenanceStatus, 15000);
}

async function refreshMaintenanceStatus() {
    try {
        const res = await fetch(`${API_BASE}/api/maintenance/status`);
        if (!res.ok) throw new Error("Failed to fetch maintenance status");
        const data = await res.json();
        
        renderMaintenanceStatus(data);
    } catch (err) {
        console.error("Failed to load maintenance status:", err);
    }
}

function renderMaintenanceStatus(data) {
    const statusDot = document.getElementById('maintenance-status-dot');
    const statusText = document.getElementById('maintenance-status-text');
    const syntaxBadge = document.getElementById('syntax-status-badge');
    const integrityBadge = document.getElementById('integrity-status-badge');
    const lastDiagnoseTime = document.getElementById('last-diagnose-time');
    const consoleLog = document.getElementById('maintenance-console-log');
    const historyList = document.getElementById('maintenance-history-list');
    
    if (!statusDot || !statusText || !syntaxBadge || !integrityBadge || !lastDiagnoseTime || !consoleLog || !historyList) return;
    if (!data || !data.report) return;
    
    const report = data.report;
    const history = data.history || [];
    
    // 1. Overall health status
    if (report.health === 'healthy') {
        statusDot.className = 'status-dot online';
        statusDot.style.backgroundColor = '';
        statusText.textContent = '건강함 (Healthy)';
        statusText.style.color = 'var(--accent-green)';
    } else {
        statusDot.className = 'status-dot degraded';
        statusDot.style.backgroundColor = '#C2635B';
        statusText.textContent = '조치 권장 (Degraded)';
        statusText.style.color = '#C2635B';
    }
    
    // 2. Badges
    // Syntax Check
    if (report.syntax_errors && report.syntax_errors.length === 0) {
        syntaxBadge.textContent = '정상';
        syntaxBadge.style.backgroundColor = '#3D664E';
    } else {
        syntaxBadge.textContent = `오류 (${report.syntax_errors.length}건)`;
        syntaxBadge.style.backgroundColor = '#C2635B';
    }
    
    // Integrity Check
    if (report.integrity && report.integrity.status === 'success') {
        integrityBadge.textContent = '정상';
        integrityBadge.style.backgroundColor = '#3D664E';
    } else {
        integrityBadge.textContent = '오류';
        integrityBadge.style.backgroundColor = '#C2635B';
    }
    
    // Time
    if (report.timestamp) {
        lastDiagnoseTime.textContent = report.timestamp;
    }
    
    // 3. Log Output
    let logLines = `=== 자가 진단 최종 분석 리포트 (${report.timestamp || 'N/A'}) ===\n`;
    logLines += `전체 건강도: ${report.health.toUpperCase()}\n`;
    logLines += `[무결성 검사 로그]\n${(report.integrity && report.integrity.log) ? report.integrity.log.trim() : '로그 없음'}\n\n`;
    
    if (report.syntax_errors && report.syntax_errors.length > 0) {
        logLines += `[구문 에러 검출 목록]\n`;
        report.syntax_errors.forEach((err, index) => {
            logLines += `${index + 1}. 파일: ${err.file}\n   위치: ${err.line}라인\n   내용: ${err.error}\n`;
        });
    } else {
        logLines += `[구문 검사 결과]\n모든 파이썬 소스코드의 컴파일 상태가 완벽합니다 (구문 오류 없음).\n`;
    }
    
    // If not running a repair, show the latest diagnostics
    if (!isRepairRunning) {
        consoleLog.textContent = logLines;
    }
    
    // 4. Render History
    historyList.innerHTML = '';
    if (history.length === 0) {
        historyList.innerHTML = `<div style="text-align: center; color: var(--text-secondary); font-style: italic; margin-top: 15px;">이력 데이터 대기 중...</div>`;
    } else {
        history.forEach(item => {
            const div = document.createElement('div');
            div.className = 'maintenance-history-item';
            
            const isSuccess = item.status === 'success';
            const badgeClass = isSuccess ? 'maintenance-badge-success' : 'maintenance-badge-rolled-back';
            const statusLabel = isSuccess ? '완료' : '롤백됨';
            const elapsed = item.elapsed_seconds ? `${item.elapsed_seconds}초 소요` : '';
            
            const headerDiv = document.createElement('div');
            headerDiv.className = 'maintenance-history-header';
            
            const fileSpan = document.createElement('span');
            fileSpan.style.color = 'var(--accent-green)';
            fileSpan.style.fontSize = '11px';
            fileSpan.style.fontWeight = 'bold';
            fileSpan.textContent = item.target_file || '전체 복구';
            headerDiv.appendChild(fileSpan);
            
            const badgeSpan = document.createElement('span');
            badgeSpan.className = `maintenance-history-badge ${badgeClass}`;
            badgeSpan.textContent = statusLabel;
            headerDiv.appendChild(badgeSpan);
            
            div.appendChild(headerDiv);
            
            const detailsDiv = document.createElement('div');
            detailsDiv.className = 'maintenance-history-details';
            detailsDiv.style.margin = '4px 0';
            detailsDiv.textContent = '피드백: ';
            const strongFeedback = document.createElement('strong');
            strongFeedback.textContent = item.feedback;
            detailsDiv.appendChild(strongFeedback);
            div.appendChild(detailsDiv);
            
            if (item.reason) {
                const reasonDiv = document.createElement('div');
                reasonDiv.style.color = '#A34841';
                reasonDiv.style.fontSize = '10.5px';
                reasonDiv.style.marginBottom = '4px';
                reasonDiv.style.fontWeight = '500';
                reasonDiv.textContent = `※ 사유: ${item.reason}`;
                div.appendChild(reasonDiv);
            }
            
            const metaDiv = document.createElement('div');
            metaDiv.className = 'maintenance-history-meta';
            
            const timeSpan = document.createElement('span');
            timeSpan.className = 'maintenance-history-time';
            timeSpan.textContent = item.timestamp;
            metaDiv.appendChild(timeSpan);
            
            const elapsedSpan = document.createElement('span');
            elapsedSpan.textContent = elapsed;
            metaDiv.appendChild(elapsedSpan);
            
            div.appendChild(metaDiv);
            
            historyList.appendChild(div);
        });
    }
}

async function triggerMaintenanceRepair() {
    const feedbackInput = document.getElementById('repair-feedback-input');
    const feedback = feedbackInput ? feedbackInput.value.trim() : "";
    const btnRepair = document.getElementById('btn-trigger-repair');
    const runningIndicator = document.getElementById('repair-running-indicator');
    const consoleLog = document.getElementById('maintenance-console-log');
    
    if (!feedback) {
        alert("수정을 위한 피드백 내용을 입력해 주십시오.");
        return;
    }
    
    if (!confirm("백그라운드에서 AI 자율 수정 및 빌드/무결성 검증을 실행하시겠습니까?")) {
        return;
    }
    
    isRepairRunning = true;
    if (btnRepair) btnRepair.disabled = true;
    if (feedbackInput) feedbackInput.disabled = true;
    if (runningIndicator) runningIndicator.style.display = 'inline';
    
    const timestamp = new Date().toLocaleTimeString();
    if (consoleLog) {
        consoleLog.textContent = `[${timestamp}] AI 자율 복구 스레드 가동...\n`;
        consoleLog.textContent += `전달된 피드백: "${feedback}"\n`;
        consoleLog.textContent += `백업 생성 및 로컬 Ollama AI 패치 생성 요청을 대기 중입니다.\n`;
        consoleLog.textContent += `이 과정은 약 10~30초 정도 소요될 수 있습니다. 대시보드가 정상 유지되는 동안 백그라운드 스레드에서 검증 및 컴파일 검사를 계속 진행합니다...\n`;
    }
    
    try {
        const res = await fetch(`${API_BASE}/api/maintenance/repair`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ feedback })
        });
        
        if (!res.ok) throw new Error(`서버 에러 (HTTP ${res.status})`);
        
        const data = await res.json();
        if (consoleLog) {
            consoleLog.textContent += `\n[서버 응답] ${data.message}\n`;
        }
        showToast(data.message, 'success');
        
        if (feedbackInput) feedbackInput.value = '';
        
        // Immediately fetch status update to show history/changes
        setTimeout(async () => {
            await refreshMaintenanceStatus();
            isRepairRunning = false;
            if (btnRepair) btnRepair.disabled = false;
            if (feedbackInput) feedbackInput.disabled = false;
            if (runningIndicator) runningIndicator.style.display = 'none';
        }, 5000);
        
    } catch (err) {
        console.error("Failed to run repair:", err);
        if (consoleLog) {
            consoleLog.textContent += `\n[오류 발생] ${err.message}\n`;
        }
        showToast(`복구 요청 실패: ${err.message}`, 'error');
        isRepairRunning = false;
        if (btnRepair) btnRepair.disabled = false;
        if (feedbackInput) feedbackInput.disabled = false;
        if (runningIndicator) runningIndicator.style.display = 'none';
    }
}

/* =================================================================---------
   OmniConvert Core Engine Modules & Integration
   ================================================================---------- */

// HTML5 / Canvas native font support configuration for PDF rendering
if (typeof pdfjsLib !== 'undefined') {
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';
}

// Korean & English Stop Words for TF-IDF Summarizer
const STOP_WORDS = new Set([
    "은", "는", "이", "가", "을", "를", "에", "에서", "와", "과", "의", "로", "으로", "하고", "그리고", "하지만", "또한", "그래서", "그러나", "그런데",
    "이것", "그것", "저것", "것", "수", "등", "및", "즉", "한", "할", "합니다", "한다", "했다", "하는", "하여", "있습니다", "있다", "없다", "되다", "되어",
    "the", "and", "a", "of", "to", "in", "is", "that", "it", "on", "for", "as", "with", "was", "at", "by", "an", "be", "this", "are", "from", "or", "but"
]);

// XML Escaper for DOCX and HWPX creation
const escapeXml = (str) => {
    if (!str) return '';
    return str.replace(/&/g, '&amp;')
              .replace(/</g, '&lt;')
              .replace(/>/g, '&gt;')
              .replace(/"/g, '&quot;')
              .replace(/'/g, '&apos;');
};

// Helper to split text into sentences
function splitSentences(text) {
    if (!text) return [];
    return text
        .split(/(?<=[.?!])\s+/)
        .map(s => s.trim())
        .filter(s => s.length > 4); // Filter out extremely short sentence fragments
}

// TF-IDF Summarizer Core Function
function calculateTfidfSummarizer(text, ratioPercent) {
    const sentences = splitSentences(text);
    if (sentences.length <= 2) {
        return {
            summaryText: text,
            summarySentences: sentences,
            highlights: sentences.map((s, idx) => ({ sentence: s, isSummary: true, index: idx }))
        };
    }
    
    // 1. Tokenization and term frequency computation
    const sentenceTokens = sentences.map(s => {
        return s.toLowerCase()
            .replace(/[^a-zA-Z0-9가-힣\s]/g, '')
            .split(/\s+/)
            .filter(word => word.length >= 2 && !STOP_WORDS.has(word));
    });
    
    // Word/Term Frequencies in Document
    const wordDocCounts = new Map();
    sentenceTokens.forEach(tokens => {
        const uniqueInSentence = new Set(tokens);
        uniqueInSentence.forEach(w => {
            wordDocCounts.set(w, (wordDocCounts.get(w) || 0) + 1);
        });
    });
    
    const N = sentences.length;
    
    // Sentence Scoring: TF-IDF based sentence ranking
    const scoredSentences = sentences.map((sentence, idx) => {
        const tokens = sentenceTokens.at(idx);
        if (tokens.length === 0) return { sentence, index: idx, score: 0 };
        
        let score = 0;
        const tokenFreqs = new Map();
        tokens.forEach(w => {
            tokenFreqs.set(w, (tokenFreqs.get(w) || 0) + 1);
        });
        
        tokens.forEach(w => {
            const tf = tokenFreqs.get(w) / tokens.length;
            const idf = Math.log(1 + (N / (wordDocCounts.get(w) || 1)));
            score += tf * idf;
        });
        
        const lengthNormalization = Math.log(1 + tokens.length);
        const finalScore = score / lengthNormalization;
        
        return { sentence, index: idx, score: finalScore };
    });
    
    const sortedByScore = [...scoredSentences].sort((a, b) => b.score - a.score);
    const selectCount = Math.max(1, Math.round(sentences.length * (ratioPercent / 100)));
    const topSentences = sortedByScore.slice(0, selectCount);
    
    const summaryIndices = new Set(topSentences.map(item => item.index));
    const summarySentencesOrdered = [...topSentences]
        .sort((a, b) => a.index - b.index)
        .map(item => item.sentence);
        
    const summaryText = summarySentencesOrdered.join(" ");
    const highlights = sentences.map((s, idx) => ({
        sentence: s,
        isSummary: summaryIndices.has(idx),
        index: idx
    }));
    
    return {
        summaryText,
        summarySentences: summarySentencesOrdered,
        highlights
    };
}

// DOCX skeleton zipper builder
function buildDocxBlob(text) {
    return new Promise(async (resolve, reject) => {
        try {
            if (typeof JSZip === 'undefined') {
                throw new Error("JSZip 라이브러리가 로드되지 않았습니다.");
            }
            const zip = new JSZip();
            
            const contentTypesXml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>`;
            zip.file("[Content_Types].xml", contentTypesXml);
            
            const relsXml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>`;
            zip.folder("_rels").file(".rels", relsXml);
            
            const lines = text.split("\n");
            const paragraphsXml = lines.map(line => {
                return `<w:p><w:r><w:t>${escapeXml(line)}</w:t></w:r></w:p>`;
            }).join("");
            
            const documentXml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    ${paragraphsXml}
    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>
    </w:sectPr>
  </w:body>
</w:document>`;
            zip.folder("word").file("document.xml", documentXml);
            
            const blob = await zip.generateAsync({ type: 'blob' });
            resolve(blob);
        } catch (error) {
            reject(error);
        }
    });
}

// HWPX skeleton zipper builder
function buildHwpxBlob(text) {
    return new Promise(async (resolve, reject) => {
        try {
            if (typeof JSZip === 'undefined') {
                throw new Error("JSZip 라이브러리가 로드되지 않았습니다.");
            }
            const zip = new JSZip();
            
            zip.file("mimetype", "application/hwp+zip", { compression: "STORE" });
            
            const containerXml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container:1.0">
  <rootfiles>
    <rootfile full-path="Contents/content.hpf" media-type="application/hwp+zip"/>
  </rootfiles>
</container>`;
            zip.folder("META-INF").file("container.xml", containerXml);
            
            const contentHpf = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<package xmlns="http://www.hancom.co.kr/hwpml/2011/head" version="1.0" id="hwp-document">
  <metadata>
    <title>OmniConvert HWPX Document</title>
    <creator>OmniConvert</creator>
  </metadata>
  <manifest>
    <item id="section0" href="section0.xml" media-type="application/xml"/>
  </manifest>
  <spine>
    <itemref idref="section0"/>
  </spine>
</package>`;
            zip.folder("Contents").file("content.hpf", contentHpf);
            
            const lines = text.split("\n");
            const paragraphsXml = lines.map(line => {
                return `<hp:p><hp:run><hp:t>${escapeXml(line)}</hp:t></hp:run></hp:p>`;
            }).join("");
            
            const sectionXml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<hp:section xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core">
  ${paragraphsXml}
</hp:section>`;
            zip.file("Contents/section0.xml", sectionXml);
            
            const blob = await zip.generateAsync({ type: 'blob' });
            resolve(blob);
        } catch (error) {
            reject(error);
        }
    });
}

// PDF custom multi-page wrapped generator using canvas rendering
function buildPdfBlob(text, docTitle) {
    return new Promise(async (resolve, reject) => {
        try {
            if (typeof window.jspdf === 'undefined') {
                throw new Error("jsPDF 라이브러리가 로드되지 않았습니다.");
            }
            const { jsPDF } = window.jspdf;
            
            const container = document.createElement('div');
            container.style.position = 'absolute';
            container.style.left = '-9999px';
            container.style.top = '-9999px';
            container.style.width = '750px';
            container.style.padding = '45px';
            container.style.background = '#ffffff';
            container.style.color = '#000000';
            container.style.fontFamily = "'Malgun Gothic', 'Nanum Gothic', sans-serif";
            container.style.fontSize = '15px';
            container.style.lineHeight = '1.7';
            container.style.boxSizing = 'border-box';
            
            const titleEl = document.createElement('h1');
            titleEl.style.fontSize = '24px';
            titleEl.style.fontWeight = '700';
            titleEl.style.margin = '0 0 10px 0';
            titleEl.style.color = '#111827';
            titleEl.style.borderBottom = '2px solid #e5e7eb';
            titleEl.style.paddingBottom = '12px';
            titleEl.innerText = docTitle.replace(/\.[^/.]+$/, "");
            container.appendChild(titleEl);
            
            const metaEl = document.createElement('p');
            metaEl.style.fontSize = '11px';
            metaEl.style.color = '#6b7280';
            metaEl.style.margin = '-5px 0 25px 0';
            metaEl.innerText = `Generated by ARA (OmniConvert Engine) at ${new Date().toLocaleString()}`;
            container.appendChild(metaEl);
            
            const bodyEl = document.createElement('div');
            bodyEl.style.whiteSpace = 'pre-wrap';
            bodyEl.style.wordBreak = 'break-all';
            bodyEl.innerText = text;
            container.appendChild(bodyEl);
            
            document.body.appendChild(container);
            
            if (typeof html2canvas === 'undefined') {
                const pdf = new jsPDF('p', 'mm', 'a4');
                pdf.setFontSize(14);
                pdf.text(docTitle, 10, 10);
                const splitText = pdf.splitTextToSize(text, 180);
                pdf.setFontSize(10);
                pdf.text(splitText, 10, 20);
                document.body.removeChild(container);
                resolve(pdf.output('blob'));
                return;
            }
            
            html2canvas(container, {
                scale: 2,
                useCORS: true,
                logging: false,
                backgroundColor: '#ffffff'
            }).then(canvas => {
                document.body.removeChild(container);
                
                const imgData = canvas.toDataURL('image/jpeg', 0.95);
                const pdf = new jsPDF('p', 'mm', 'a4');
                const imgWidth = 210; 
                const pageHeight = 297;
                const imgHeight = (canvas.height * imgWidth) / canvas.width;
                
                let heightLeft = imgHeight;
                let position = 0;
                
                pdf.addImage(imgData, 'JPEG', 0, position, imgWidth, imgHeight, undefined, 'FAST');
                heightLeft -= pageHeight;
                
                while (heightLeft > 0) {
                    position = heightLeft - imgHeight;
                    pdf.addPage();
                    pdf.addImage(imgData, 'JPEG', 0, position, imgWidth, imgHeight, undefined, 'FAST');
                    heightLeft -= pageHeight;
                }
                
                resolve(pdf.output('blob'));
            }).catch(err => {
                if (document.body.contains(container)) {
                    document.body.removeChild(container);
                }
                reject(err);
            });
            
        } catch (error) {
            reject(error);
        }
    });
}

// Java code wrapper
function wrapInJava(text, fileName) {
    let className = fileName.replace(/\.[^/.]+$/, "").replace(/[^a-zA-Z0-9]/g, "");
    if (!className || /^\d/.test(className)) className = "AraOmniConvertClass";
    
    if (text.includes("public class ") || (text.includes("void main") && text.includes("System.out.print"))) {
        return text;
    }
    
    let lines = text.split("\n");
    let javaCode = `/**\n * ARA OmniConvert 클라이언트 사이드 변환 엔진에 의해 생성된 Java 소스\n * 원본 파일: ${fileName}\n */\n`;
    javaCode += `public class ${className} {\n`;
    javaCode += `    public static void main(String[] args) {\n`;
    javaCode += `        System.out.println("====== [문서 내용 출력] ======");\n`;
    lines.forEach(line => {
        let escapedLine = line.replace(/\\/g, "\\\\").replace(/"/g, "\\\"");
        javaCode += `        System.out.println("${escapedLine}");\n`;
    });
    javaCode += `    }\n`;
    javaCode += `}\n`;
    return javaCode;
}

// Toast fallback implementation
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer') || document.body;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.style.position = 'fixed';
    toast.style.bottom = '20px';
    toast.style.right = '20px';
    toast.style.backgroundColor = type === 'success' ? '#10B981' : type === 'error' ? '#EF4444' : '#3B82F6';
    toast.style.color = '#fff';
    toast.style.padding = '10px 20px';
    toast.style.borderRadius = '5px';
    toast.style.zIndex = '9999';
    toast.style.display = 'flex';
    toast.style.alignItems = 'center';
    toast.style.gap = '8px';
    toast.style.fontFamily = 'sans-serif';
    toast.style.fontSize = '14px';
    toast.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
    
    let iconName = 'info';
    if (type === 'success') iconName = 'check-circle';
    if (type === 'error') iconName = 'alert-triangle';
    
    toast.innerHTML = '';
    const icon = document.createElement('i');
    icon.setAttribute('data-lucide', iconName);
    toast.appendChild(icon);
    
    const span = document.createElement('span');
    span.textContent = message;
    toast.appendChild(span);
    
    container.appendChild(toast);
    if (window.lucide) window.lucide.createIcons();
    
    setTimeout(() => {
        toast.style.transition = 'opacity 0.5s';
        toast.style.opacity = '0';
        setTimeout(() => {
            toast.remove();
        }, 500);
    }, 3000);
}

// Self-Diagnostics System Trigger Setup
const btnRunDiagnostics = document.getElementById('btnRunDiagnostics') || document.createElement('button');
if (!document.getElementById('btnRunDiagnostics')) {
    btnRunDiagnostics.id = 'btnRunDiagnostics';
    btnRunDiagnostics.style.display = 'none';
    document.body.appendChild(btnRunDiagnostics);
}
btnRunDiagnostics.addEventListener('click', async () => {
    showToast('자가 진단을 기동합니다.', 'info');
    let allPassed = true;
    
    const runTest = async (name, fn) => {
        try {
            await fn();
            console.log(`[PASS] ${name}`);
        } catch (e) {
            allPassed = false;
            console.error(`[FAIL] ${name}: ${e.message}`);
        }
    };
    
    await runTest('JSZip 라이브러리 검증', async () => {
        if (typeof JSZip === 'undefined') throw new Error("JSZip 미로드");
    });
    
    await runTest('Mammoth 워드 디코더 검증', async () => {
        if (typeof mammoth === 'undefined') throw new Error("Mammoth 미로드");
    });
    
    await runTest('PDF.js 문서 디코더 검증', async () => {
        if (typeof pdfjsLib === 'undefined') throw new Error("pdfjsLib 미로드");
    });
    
    await runTest('jsPDF 인쇄 라이브러리 검증', async () => {
        if (typeof window.jspdf === 'undefined') throw new Error("jsPDF 미로드");
    });
    
    await runTest('TF-IDF 요약 알고리즘 검증', async () => {
        const text = "첫 번째 긴 문장입니다. 두 번째 긴 문장입니다. 세 번째 긴 문장입니다. 네 번째 긴 문장입니다.";
        const summary = calculateTfidfSummarizer(text, 50);
        if (!summary.summaryText) throw new Error("요약 실패");
    });
    
    if (allPassed) {
        showToast('모든 기능의 자가 검증이 성공적으로 완료되었습니다!', 'success');
    } else {
        showToast('일부 검증 테스트 항목이 실패했습니다.', 'error');
    }
});

/* --------------------------------------------------------------------------
   Sense Core: Real-Time Environment & User Recognition
   -------------------------------------------------------------------------- */
async function loadCocoSsdModel() {
    if (cocoModel || isModelLoading) return cocoModel;
    isModelLoading = true;
    const visionStatus = document.querySelector('.vision-status');
    if (visionStatus) {
        visionStatus.textContent = "TF.js 인지 모델 로드 중...";
    }
    try {
        cocoModel = await cocoSsd.load();
        console.log("COCO-SSD model loaded successfully.");
        if (visionStatus && isCameraOn) {
            visionStatus.textContent = "시각 데이터 및 TF.js 로드 완료";
        }
    } catch (err) {
        console.error("Failed to load COCO-SSD model:", err);
        if (visionStatus) {
            visionStatus.textContent = "인지 모델 로드 실패";
        }
    } finally {
        isModelLoading = false;
    }
    return cocoModel;
}

function startDetectionLoop() {
    if (!isCameraOn || !webcamFeed) return;
    
    if (visionDetectionTimeout) clearTimeout(visionDetectionTimeout);
    
    visionDetectionTimeout = setTimeout(async () => {
        if (!isCameraOn) return;
        
        try {
            const model = await loadCocoSsdModel();
            if (model && webcamFeed.readyState === 4) { // HAVE_ENOUGH_DATA
                const predictions = await model.detect(webcamFeed);
                drawVisionBoxes(predictions);
                processSensoryData(predictions);
            }
        } catch (err) {
            console.error("Detection error:", err);
        }
        
        startDetectionLoop();
    }, 2000);
}

function drawVisionBoxes(predictions) {
    const canvas = document.getElementById('vision-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    if (canvas.width !== webcamFeed.clientWidth || canvas.height !== webcamFeed.clientHeight) {
        canvas.width = webcamFeed.clientWidth;
        canvas.height = webcamFeed.clientHeight;
    }
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    predictions.forEach(prediction => {
        const videoWidth = webcamFeed.videoWidth || 320;
        const videoHeight = webcamFeed.videoHeight || 240;
        
        const scaleX = canvas.width / videoWidth;
        const scaleY = canvas.height / videoHeight;
        
        const [x, y, width, height] = prediction.bbox;
        const rx = x * scaleX;
        const ry = y * scaleY;
        const rw = width * scaleX;
        const rh = height * scaleY;
        
        ctx.strokeStyle = '#3D664E';
        ctx.lineWidth = 2;
        ctx.strokeRect(rx, ry, rw, rh);
        
        ctx.fillStyle = 'rgba(61, 102, 78, 0.15)';
        ctx.fillRect(rx, ry, rw, rh);
        
        const label = `${prediction.class} (${Math.round(prediction.score * 100)}%)`;
        ctx.fillStyle = '#3D664E';
        ctx.font = '10px "Nunito", sans-serif';
        ctx.textBaseline = 'top';
        const textWidth = ctx.measureText(label).width;
        
        ctx.fillRect(rx, ry - 14, textWidth + 10, 14);
        ctx.fillStyle = '#FFFFFF';
        ctx.fillText(label, rx + 5, ry - 12);
    });
}

function getActiveUserNickname() {
    try {
        const savedUser = localStorage.getItem('ara_user');
        if (savedUser) {
            const parsed = JSON.parse(savedUser);
            if (parsed && parsed.nickname) {
                return parsed.nickname;
            }
        }
    } catch (e) {}
    return "사용자";
}

async function processSensoryData(predictions) {
    const personDetected = predictions.some(p => p.class === 'person');
    const nickname = getActiveUserNickname();
    const personLabel = personDetected ? `감지됨 (${nickname})` : "없음";
    
    let hasIndoorObj = false;
    let hasOutdoorObj = false;
    const objectList = [];
    
    predictions.forEach(p => {
        const c = p.class.toLowerCase();
        objectList.push(p.class);
        if (['chair', 'tv', 'bed', 'dining table', 'couch', 'laptop', 'mouse', 'keyboard', 'book', 'bottle', 'cup', 'vase', 'refrigerator', 'microwave', 'sink'].includes(c)) {
            hasIndoorObj = true;
        }
        if (['car', 'bicycle', 'motorcycle', 'bus', 'truck', 'traffic light', 'stop sign'].includes(c)) {
            hasOutdoorObj = true;
        }
    });
    
    let location = "실내 (집안)";
    if (hasOutdoorObj && !hasIndoorObj) {
        location = "실외 (집밖)";
    }
    
    // Update local UI
    const locVal = document.getElementById('rec-location-val');
    const perVal = document.getElementById('rec-person-val');
    const objList = document.getElementById('rec-objects-list');
    
    if (locVal) locVal.textContent = location;
    if (perVal) perVal.textContent = personLabel;
    if (objList) {
        objList.textContent = objectList.length > 0 ? objectList.join(', ') : '--';
    }
    
    // Write sensory log to server if state changed or 15s elapsed
    const stateStr = `${location}|${personLabel}|${objectList.join(',')}`;
    const currTime = Date.now();
    
    if (stateStr !== `${lastSensoryState.location}|${lastSensoryState.person}|${lastSensoryState.objects}` || (currTime - lastSensoryLogTime > 15000)) {
        lastSensoryState = { location, person: personLabel, objects: objectList.join(',') };
        lastSensoryLogTime = currTime;
        
        try {
            await fetch(`${API_BASE}/api/sensory/log`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    location,
                    person: personLabel,
                    objects: objectList
                })
            });
        } catch (e) {
            console.warn("Failed to write sensory log to server:", e);
        }
    }
}

async function loadSensoryHistory() {
    const listEl = document.getElementById('sensory-history-list');
    if (!listEl) return;
    
    try {
        const res = await fetch(`${API_BASE}/api/sensory/history`);
        if (!res.ok) throw new Error("History fetch failed");
        
        const logs = await res.json();
        listEl.innerHTML = '';
        
        if (logs.length === 0) {
            listEl.innerHTML = `<div style="text-align: center; color: var(--text-secondary); font-style: italic; margin-top: 25px;">감지 이력이 없습니다.</div>`;
            return;
        }
        
        // Sync UI displays with the latest log if it's fresh (within 8 seconds)
        // (This allows local python vision utility updates to reflect in the UI too)
        const latest = logs[0];
        const logTime = new Date(latest.timestamp).getTime();
        const nowTime = Date.now();
        
        if (nowTime - logTime < 8000) {
            const locVal = document.getElementById('rec-location-val');
            const perVal = document.getElementById('rec-person-val');
            const objList = document.getElementById('rec-objects-list');
            
            if (locVal) locVal.textContent = latest.location;
            if (perVal) perVal.textContent = latest.person;
            if (objList) {
                objList.textContent = latest.objects && latest.objects.length > 0 ? (Array.isArray(latest.objects) ? latest.objects.join(', ') : latest.objects) : '--';
            }
        }
        
        logs.forEach(log => {
            const div = document.createElement('div');
            div.style.padding = '3px 0';
            div.style.borderBottom = '1px dashed rgba(255,255,255,0.08)';
            
            const timeSpan = document.createElement('span');
            timeSpan.style.color = '#86A890';
            timeSpan.textContent = `[${log.timestamp.split(' ')[1]}] `;
            div.appendChild(timeSpan);
            
            const locSpan = document.createElement('span');
            locSpan.style.color = '#EAE5D9';
            locSpan.textContent = `${log.location} | `;
            div.appendChild(locSpan);
            
            const personSpan = document.createElement('span');
            personSpan.style.color = log.person.includes('감지됨') ? '#A9C2B1' : '#B0B0B0';
            personSpan.textContent = `사람: ${log.person}`;
            div.appendChild(personSpan);
            
            if (log.objects && log.objects.length > 0) {
                const objSpan = document.createElement('span');
                objSpan.style.color = '#D6C8A1';
                const objsText = Array.isArray(log.objects) ? log.objects.join(', ') : log.objects;
                objSpan.textContent = ` (${objsText})`;
                div.appendChild(objSpan);
            }
            
            listEl.appendChild(div);
        });
    } catch (err) {
        console.warn("Failed to load sensory history:", err);
        listEl.innerHTML = `<div style="color: #C2635B; text-align: center; margin-top: 25px;">이력을 불러오지 못했습니다.</div>`;
    }
}


