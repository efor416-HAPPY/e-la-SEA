/* ==========================================================================
   🌱 ARA App Controller (Hardware & API Binding)
   ========================================================================== */

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

    // 2. Start Camera & Audio Analyzers
    initCamera();
    initAudioAnalyzer();
    
    // 3. Initialize Speech Recognition
    initSpeechRecognition();

    // 4. Connect Backend Data
    initBackendConnection();

    // 5. Setup Action Listeners
    setupEventListeners();
});

/* --------------------------------------------------------------------------
   Sensory Input: Camera & Video Stream
   -------------------------------------------------------------------------- */
function initCamera() {
    webcamFeed.style.display = 'none';
    const placeholder = document.createElement('div');
    placeholder.className = 'camera-placeholder';
    placeholder.innerHTML = `<p style="text-align: center; font-size: 11px; color: var(--text-secondary); margin-top: 50px;">카메라가 꺼져 있습니다.</p>`;
    placeholder.style.height = '100%';
    placeholder.style.backgroundColor = '#E2EAE3';
    webcamFeed.parentNode.appendChild(placeholder);
}

async function toggleCamera() {
    const icon = document.getElementById('icon-camera-status');
    const placeholder = document.querySelector('.camera-placeholder');

    if (isCameraOn) {
        if (cameraStream) {
            cameraStream.getTracks().forEach(track => track.stop());
            cameraStream = null;
        }
        webcamFeed.srcObject = null;
        webcamFeed.style.display = 'none';
        if (placeholder) placeholder.style.display = 'block';
        icon.setAttribute('data-lucide', 'video-off');
        isCameraOn = false;
    } else {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 320, height: 240 } });
            cameraStream = stream;
            webcamFeed.srcObject = stream;
            webcamFeed.style.display = 'block';
            if (placeholder) placeholder.style.display = 'none';
            icon.setAttribute('data-lucide', 'video');
            isCameraOn = true;
        } catch (err) {
            console.warn("Webcam access denied:", err);
        }
    }
    lucide.createIcons();
}

/* --------------------------------------------------------------------------
   Sensory Input: Audio & Mic Visualization
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
        console.warn("Microphone access denied:", err);
        audioDbLabel.textContent = "오디오 입력 차단";
    }
}

function drawAudioWave() {
    if (!audioAnalyser) return;
    const canvas = audioWaveform;
    const ctx = canvas.getContext('2d');
    const bufferLength = audioAnalyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    canvas.width = canvas.parentNode.clientWidth;
    canvas.height = canvas.parentNode.clientHeight;
    
    function draw() {
        requestAnimationFrame(draw);
        audioAnalyser.getByteTimeDomainData(dataArray);
        
        ctx.fillStyle = '#F2ECE1';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        ctx.lineWidth = 2;
        ctx.strokeStyle = '#3D664E';
        ctx.beginPath();
        
        const sliceWidth = canvas.width * 1.0 / bufferLength;
        let x = 0;
        let sumSq = 0;
        
        for (let i = 0; i < bufferLength; i++) {
            const v = dataArray[i] / 128.0;
            const y = v * canvas.height / 2;
            const dev = v - 1.0;
            sumSq += dev * dev;

            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
            x += sliceWidth;
        }
        ctx.lineTo(canvas.width, canvas.height / 2);
        ctx.stroke();
        
        const rms = Math.sqrt(sumSq / bufferLength);
        const volumePercent = Math.min(Math.round(rms * 400), 100);
        audioDbLabel.textContent = `Volume: ${volumePercent}%`;

        // Sound triggered auto camera start
        const chkAutoCamera = document.getElementById('chk-sound-auto-camera');
        if (chkAutoCamera && chkAutoCamera.checked && volumePercent > 30 && !isCameraOn) {
            toggleCamera();
        }
    }
    draw();
}

/* --------------------------------------------------------------------------
   Voice: Web Speech API (STT & TTS)
   -------------------------------------------------------------------------- */
function initSpeechRecognition() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) {
        btnVoiceInput.style.display = 'none';
        return;
    }
    
    speechRecognition = new SpeechRec();
    speechRecognition.lang = 'ko-KR';
    speechRecognition.continuous = true;
    
    speechRecognition.onstart = () => {
        isListening = true;
        btnVoiceInput.className = 'btn-voice-listening';
        pulsingLeafIndicator.classList.add('listening');
        interactionStatusText.textContent = "청취 중...";
    };
    
    speechRecognition.onend = () => {
        if (isListening) {
            try { speechRecognition.start(); } catch (e) {}
        } else {
            btnVoiceInput.className = 'btn-voice-ready';
            pulsingLeafIndicator.classList.remove('listening');
            interactionStatusText.textContent = "이야기를 기다리는 중...";
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
}

function speakText(text) {
    if (isSoundMuted || !('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    
    const cleanText = text.replace(/[*#`_\-\[\]()]/g, '').trim();
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = 'ko-KR';
    window.speechSynthesis.speak(utterance);
}

/* --------------------------------------------------------------------------
   API Bridging
   -------------------------------------------------------------------------- */
function initBackendConnection() {
    updateSystemStats();
    loadDirectoryList('');
    loadWisdomStorage();
    setInterval(updateSystemStats, 5000);
}

async function updateSystemStats() {
    try {
        const res = await fetch(`${API_BASE}/api/system`);
        if (!res.ok) throw new Error();
        const stats = await res.json();
        cpuLoadText.textContent = `${stats.cpu_usage}%`;
        dbStatusText.textContent = "활성화";
        if (window.araBrain) {
            window.araBrain.setSystemStress(stats.cpu_usage / 100.0);
        }
    } catch (err) {
        cpuLoadText.textContent = '0%';
        dbStatusText.textContent = "로컬 모드";
    }
}

async function loadDirectoryList(path) {
    fileList.innerHTML = `<li class="file-item loading">디렉토리 로드 중...</li>`;
    try {
        const encodedPath = encodeURIComponent(path);
        const res = await fetch(`${API_BASE}/api/files?action=list&path=${encodedPath}`);
        if (!res.ok) throw new Error();
        const data = await res.json();
        currentPath = data.current_path;
        currentFolderPath.textContent = currentPath;
        
        fileList.innerHTML = '';
        
        if (currentPath && currentPath !== '내 PC' && currentPath !== '/') {
            const parentItem = document.createElement('li');
            parentItem.className = 'file-item directory';
            parentItem.innerHTML = `<span>[상위 디렉토리]</span>`;
            parentItem.addEventListener('click', () => {
                let tempPath = currentPath.replace(/[\\/]$/, '');
                let lastIdx = Math.max(tempPath.lastIndexOf('/'), tempPath.lastIndexOf('\\'));
                if (lastIdx !== -1) {
                    loadDirectoryList(tempPath.substring(0, lastIdx));
                } else {
                    loadDirectoryList('');
                }
            });
            fileList.appendChild(parentItem);
        }

        data.items.forEach(item => {
            const li = document.createElement('li');
            li.className = `file-item ${item.is_dir ? 'directory' : 'file'}`;
            li.innerHTML = `<span>${item.is_dir ? '📁' : '📄'} ${item.name}</span>`;
            li.addEventListener('click', () => {
                if (item.is_dir) {
                    loadDirectoryList(item.path);
                } else {
                    loadFileContent(item.path);
                }
            });
            fileList.appendChild(li);
        });
    } catch (err) {
        fileList.innerHTML = `<li class="file-item loading">로드 실패.</li>`;
    }
}

async function loadFileContent(filePath) {
    try {
        const encodedPath = encodeURIComponent(filePath);
        const res = await fetch(`${API_BASE}/api/files?action=read&path=${encodedPath}`);
        if (!res.ok) throw new Error();
        const data = await res.json();
        appendMessage('system', `로컬 파일 로드: ${filePath.split(/[/\\]/).pop()}`);
        chatTextInput.value = `[문서 검토] "${data.path}"\n내용:\n${data.content.substring(0, 500)}`;
        chatTextInput.focus();
    } catch (err) {
        alert("파일을 읽을 수 없습니다.");
    }
}

async function loadWisdomStorage() {
    const wisdomList = document.getElementById('wisdom-list');
    const totalCount = document.getElementById('wisdom-total-count');
    try {
        const res = await fetch(`${API_BASE}/api/brain/wisdom`);
        if (!res.ok) throw new Error();
        const items = await res.json();
        totalCount.textContent = items.length;
        
        if (items.length === 0) {
            wisdomList.innerHTML = `<div style="text-align: center; color: var(--text-secondary);">저장된 지혜가 없습니다.</div>`;
            return;
        }

        wisdomList.innerHTML = '';
        items.forEach(item => {
            const div = document.createElement('div');
            div.style.padding = '6px';
            div.style.borderBottom = '1px dashed var(--card-border)';
            div.innerHTML = `<strong>[${item.source}]</strong> ${item.title}<br/><span style="color: var(--text-secondary);">${item.scraped_at}</span>`;
            wisdomList.appendChild(div);
        });
    } catch (err) {
        wisdomList.innerHTML = `<div>지혜 로드 실패.</div>`;
    }
}

async function runLocalUtility(appName) {
    consoleOutput.textContent = `실행 요청: ${appName}...`;
    try {
        const res = await fetch(`${API_BASE}/api/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target: appName })
        });
        const data = await res.json();
        consoleOutput.textContent = data.message;
        appendMessage('system', data.message);
    } catch (err) {
        consoleOutput.textContent = "서버 연결 오류.";
    }
}

function appendMessage(sender, text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message ${sender}`;
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = text;
    
    const timeSpan = document.createElement('span');
    timeSpan.className = 'message-time';
    const now = new Date();
    timeSpan.textContent = `${now.getHours()}:${now.getMinutes().toString().padStart(2, '0')}`;
    
    msgDiv.appendChild(bubble);
    msgDiv.appendChild(timeSpan);
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendMessage() {
    const text = chatTextInput.value.trim();
    if (!text) return;
    
    appendMessage('user', text);
    chatTextInput.value = '';
    
    const activePersonaBtn = document.querySelector('.btn-persona.active');
    const persona = activePersonaBtn ? activePersonaBtn.getAttribute('data-persona') : 'friend';
    
    try {
        const res = await fetch(`${API_BASE}/api/brain/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, persona: persona })
        });
        const data = await res.json();
        appendMessage('ai', data.text);
        speakText(data.text);
        
        if (window.araBrain) {
            window.araBrain.stimulate(data.pulse);
        }
        loadWisdomStorage();  // Refresh stored wisdom list
    } catch (err) {
        appendMessage('ai', "서버와 연결을 구성할 수 없어 로컬 사색을 가동합니다. 🌱");
    }
}

/* --------------------------------------------------------------------------
   Event Listeners
   -------------------------------------------------------------------------- */
function setupEventListeners() {
    btnSendMessage.addEventListener('click', sendMessage);
    chatTextInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    
    btnToggleCamera.addEventListener('click', toggleCamera);
    
    btnVoiceInput.addEventListener('click', () => {
        if (isListening) {
            isListening = false;
            if (speechRecognition) speechRecognition.stop();
        } else {
            isListening = true;
            if (speechRecognition) speechRecognition.start();
        }
    });

    btnToggleSound.addEventListener('click', () => {
        isSoundMuted = !isSoundMuted;
        const icon = btnToggleSound.querySelector('i');
        icon.setAttribute('data-lucide', isSoundMuted ? 'volume-x' : 'volume-2');
        lucide.createIcons();
    });

    btnRefreshFiles.addEventListener('click', () => {
        loadDirectoryList(currentPath);
    });

    // Persona triggers
    document.querySelectorAll('.btn-persona').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.btn-persona').forEach(b => b.classList.remove('active'));
            const targetBtn = e.currentTarget;
            targetBtn.classList.add('active');
            
            const persona = targetBtn.getAttribute('data-persona');
            if (window.araBrain) {
                window.araBrain.setPersona(persona);
            }
        });
    });

    // Quick launchers
    document.querySelectorAll('.quick-launch-buttons .btn-tool').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const app = e.currentTarget.getAttribute('data-target');
            runLocalUtility(app);
        });
    });
}
