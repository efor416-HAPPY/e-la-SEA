/**
 * 🖥️ DOM Manager
 * Handles selections, layout updates, chat bubbles, list building, and text rendering.
 */
export class DOMManager {
    constructor() {
        // Cache DOM elements
        this.webcamFeed = document.getElementById('webcam-feed');
        this.audioDbLabel = document.getElementById('audio-db-label');
        this.cpuLoadText = document.getElementById('cpu-load-text');
        this.dbStatusText = document.getElementById('db-status-text');
        this.chatMessages = document.getElementById('chat-messages-container');
        this.chatTextInput = document.getElementById('chat-text-input');
        this.currentFolderPath = document.getElementById('current-folder-path');
        this.fileList = document.getElementById('file-list');
        this.consoleOutput = document.getElementById('console-output');
        this.wisdomList = document.getElementById('wisdom-list');
        this.totalCount = document.getElementById('wisdom-total-count');
        this.interactionStatusText = document.getElementById('interaction-status-text');
        this.pulsingLeafIndicator = document.querySelector('.pulsing-leaf-indicator');
    }

    /**
     * Updates CPU Load text node.
     * @param {string} value
     */
    setCPULoad(value) {
        if (this.cpuLoadText) {
            this.cpuLoadText.textContent = value;
        }
    }

    /**
     * Updates DB status label.
     * @param {string} status
     */
    setDBStatus(status) {
        if (this.dbStatusText) {
            this.dbStatusText.textContent = status;
        }
    }

    /**
     * Updates Sound volume percentage label.
     * @param {string} text
     */
    setAudioVolume(text) {
        if (this.audioDbLabel) {
            this.audioDbLabel.textContent = text;
        }
    }

    /**
     * Updates connection/interaction state.
     * @param {string} text
     */
    setInteractionStatus(text) {
        if (this.interactionStatusText) {
            this.interactionStatusText.textContent = text;
        }
    }

    /**
     * Adjusts listening animation on leaf badge.
     * @param {boolean} isListening
     */
    setPulsingLeafListening(isListening) {
        if (this.pulsingLeafIndicator) {
            if (isListening) {
                this.pulsingLeafIndicator.classList.add('listening');
            } else {
                this.pulsingLeafIndicator.classList.remove('listening');
            }
        }
    }

    /**
     * Appends dialogue message.
     * @param {'user'|'ai'|'system'} sender
     * @param {string} text
     */
    appendChatMessage(sender, text) {
        if (!this.chatMessages) return;
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
        this.chatMessages.appendChild(msgDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    /**
     * Renders local directory list layout.
     */
    renderFileList(currentPath, items, onDirectoryClick, onFileClick) {
        if (!this.fileList) return;
        this.fileList.innerHTML = '';
        if (this.currentFolderPath) {
            this.currentFolderPath.textContent = currentPath;
        }

        // Parent navigation element
        if (currentPath && currentPath !== '내 PC' && currentPath !== '/' && currentPath !== '') {
            const parentItem = document.createElement('li');
            parentItem.className = 'file-item directory';
            parentItem.innerHTML = `<span>[상위 디렉토리]</span>`;
            parentItem.addEventListener('click', () => {
                let tempPath = currentPath.replace(/[\\/]$/, '');
                let lastIdx = Math.max(tempPath.lastIndexOf('/'), tempPath.lastIndexOf('\\'));
                if (lastIdx !== -1) {
                    onDirectoryClick(tempPath.substring(0, lastIdx));
                } else {
                    onDirectoryClick('');
                }
            });
            this.fileList.appendChild(parentItem);
        }

        // Draw children
        items.forEach(item => {
            const li = document.createElement('li');
            li.className = `file-item ${item.is_dir ? 'directory' : 'file'}`;
            li.innerHTML = `<span>${item.is_dir ? '📁' : '📄'} ${item.name}</span>`;
            li.addEventListener('click', () => {
                if (item.is_dir) {
                    onDirectoryClick(item.path);
                } else {
                    onFileClick(item.path);
                }
            });
            this.fileList.appendChild(li);
        });
    }

    renderFileListError() {
        if (this.fileList) {
            this.fileList.innerHTML = `<li class="file-item loading">로드 실패.</li>`;
        }
    }

    renderFileListLoading() {
        if (this.fileList) {
            this.fileList.innerHTML = `<li class="file-item loading">디렉토리 로드 중...</li>`;
        }
    }

    /**
     * Updates the UI list of archived knowledge.
     * @param {Array} items
     */
    renderWisdomList(items) {
        if (!this.wisdomList) return;
        if (this.totalCount) {
            this.totalCount.textContent = items.length;
        }

        if (items.length === 0) {
            this.wisdomList.innerHTML = `<div style="text-align: center; color: var(--text-secondary);">저장된 지혜가 없습니다.</div>`;
            return;
        }

        this.wisdomList.innerHTML = '';
        items.forEach(item => {
            const div = document.createElement('div');
            div.style.padding = '6px';
            div.style.borderBottom = '1px dashed var(--card-border)';
            div.innerHTML = `<strong>[${item.source}]</strong> ${item.title}<br/><span style="color: var(--text-secondary);">${item.scraped_at}</span>`;
            this.wisdomList.appendChild(div);
        });
    }

    renderWisdomError() {
        if (this.wisdomList) {
            this.wisdomList.innerHTML = `<div>지혜 로드 실패.</div>`;
        }
    }

    /**
     * Updates command terminal logs.
     * @param {string} text
     */
    writeConsoleOutput(text) {
        if (this.consoleOutput) {
            this.consoleOutput.textContent = text;
        }
    }
}
