/**
 * 🛠️ Recovery Manager
 * Automatically handles offline/online fallbacks and triggers client self-healing modes.
 */
export class RecoveryManager {
    constructor(webSocketService, domManager, auditLog) {
        this.webSocketService = webSocketService;
        this.domManager = domManager;
        this.auditLog = auditLog;
        this.isOfflineMode = false;
    }

    /**
     * Fallback to localized simulated values when connection fails.
     */
    switchToOfflineMode() {
        if (this.isOfflineMode) return;
        this.isOfflineMode = true;
        this.auditLog.log("RECOVERY", "Backend unavailable. Activating client offline fallback mode.", "WARN");
        this.domManager.setDBStatus("로컬 모드");
        this.domManager.setCPULoad("0%");
        this.domManager.appendChatMessage("system", "서버와 연결을 구성할 수 없어 로컬 사색을 가동합니다. 🌱");
    }

    /**
     * Restore remote services synchronizations.
     */
    switchToOnlineMode() {
        if (!this.isOfflineMode) return;
        this.isOfflineMode = false;
        this.auditLog.log("RECOVERY", "Connection re-established. Syncing with remote APIs.", "SUCCESS");
        this.domManager.setDBStatus("활성화");
        this.domManager.appendChatMessage("system", "서버와의 연결이 다시 정상으로 복구되었습니다. 잎사귀 네트워크가 동기화되었습니다. 🍃");
    }

    /**
     * Reconnects to backend services when a socket drops.
     */
    handleConnectionLoss() {
        this.switchToOfflineMode();
        this.webSocketService.connect();
    }
}
