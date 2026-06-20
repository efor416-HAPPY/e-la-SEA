#include <iostream>
#include <string>
#include <vector>
#include <thread>
#include <mutex>
#include <queue>
#include <chrono>
#include <sstream>
#include <memory>
#include <functional>
#include <map>
#include <algorithm>
#include <condition_variable>
#include <iomanip>
#include <cctype>

// Cross-Platform Socket/Pipe Header Configuration
#ifdef _WIN32
    #ifndef WIN32_LEAN_AND_MEAN
        #define WIN32_LEAN_AND_MEAN
    #endif
    #include <windows.h>
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #pragma comment(lib, "ws2_32.lib")
#else
    #include <sys/socket.h>
    #include <sys/un.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <unistd.h>
#endif

// ============================================================================
// 1. Interfaces & Types
// ============================================================================

enum class CommandType {
    OPEN_APP,
    SYNC_FEED,
    FILE_READ,
    UNKNOWN
};

std::string CommandTypeToString(CommandType type) {
    switch (type) {
        case CommandType::OPEN_APP:  return "OPEN_APP";
        case CommandType::SYNC_FEED:  return "SYNC_FEED";
        case CommandType::FILE_READ:  return "FILE_READ";
        default:                     return "UNKNOWN";
    }
}

struct Command {
    CommandType type;
    std::string payload;
};

enum class Role {
    USER,
    ADMIN,
    SYSTEM
};

std::string RoleToString(Role role) {
    switch (role) {
        case Role::USER:   return "USER";
        case Role::ADMIN:  return "ADMIN";
        case Role::SYSTEM: return "SYSTEM";
        default:           return "UNKNOWN";
    }
}

class ITransport {
public:
    virtual bool connect() = 0;
    virtual bool send(const std::string& data) = 0;
    virtual std::string receive() = 0;
    virtual void disconnect() = 0;
    virtual ~ITransport() = default;
};

// ============================================================================
// 2. Transport Layer Implementations
// ============================================================================

class TcpTransport : public ITransport {
private:
    std::string host_;
    int port_;
    bool is_connected_;
    std::mutex mutex_;

public:
    TcpTransport(std::string host = "127.0.0.1", int port = 9091)
        : host_(std::move(host)), port_(port), is_connected_(false) {}

    bool connect() override {
        std::lock_guard<std::mutex> lock(mutex_);
        std::cout << "[TcpTransport] Connecting to " << host_ << ":" << port_ << "..." << std::endl;
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        is_connected_ = true;
        return true;
    }

    bool send(const std::string& data) override {
        std::lock_guard<std::mutex> lock(mutex_);
        if (!is_connected_) return false;
        std::cout << "[TcpTransport] Sending packet: " << data << std::endl;
        return true;
    }

    std::string receive() override {
        std::lock_guard<std::mutex> lock(mutex_);
        if (!is_connected_) return "";
        return "response:{\"status\":\"success\",\"reply\":\"TCP OK\"}";
    }

    void disconnect() override {
        std::lock_guard<std::mutex> lock(mutex_);
        if (is_connected_) {
            std::cout << "[TcpTransport] Disconnected safely." << std::endl;
            is_connected_ = false;
        }
    }
};

class PipeTransport : public ITransport {
private:
    std::string pipe_name_;
    bool is_connected_;
    std::mutex mutex_;

public:
    PipeTransport(std::string name = "ara_ipc_pipe")
        : pipe_name_(std::move(name)), is_connected_(false) {}

    bool connect() override {
        std::lock_guard<std::mutex> lock(mutex_);
        std::cout << "[PipeTransport] Connecting to Named Pipe: " << pipe_name_ << "..." << std::endl;
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
        is_connected_ = true;
        return true;
    }

    bool send(const std::string& data) override {
        std::lock_guard<std::mutex> lock(mutex_);
        if (!is_connected_) return false;
        std::cout << "[PipeTransport] Writing to pipe: " << data << std::endl;
        return true;
    }

    std::string receive() override {
        std::lock_guard<std::mutex> lock(mutex_);
        if (!is_connected_) return "";
        return "response:{\"status\":\"success\",\"reply\":\"Pipe OK\"}";
    }

    void disconnect() override {
        std::lock_guard<std::mutex> lock(mutex_);
        if (is_connected_) {
            std::cout << "[PipeTransport] Closing Named Pipe handle." << std::endl;
            is_connected_ = false;
        }
    }
};

class LocalSocketTransport : public ITransport {
private:
    std::queue<std::string> mailbox_;
    std::mutex mutex_;
    std::condition_variable cv_;
    bool is_connected_;

public:
    LocalSocketTransport() : is_connected_(false) {}

    bool connect() override {
        std::lock_guard<std::mutex> lock(mutex_);
        std::cout << "[LocalSocketTransport] In-memory IPC Mailbox ready." << std::endl;
        is_connected_ = true;
        return true;
    }

    bool send(const std::string& data) override {
        std::lock_guard<std::mutex> lock(mutex_);
        if (!is_connected_) return false;
        mailbox_.push(data);
        cv_.notify_one();
        return true;
    }

    std::string receive() override {
        std::unique_lock<std::mutex> lock(mutex_);
        if (!is_connected_) return "";

        if (mailbox_.empty()) {
            cv_.wait_for(lock, std::chrono::milliseconds(300));
        }

        if (mailbox_.empty()) {
            return "response:{\"status\":\"success\",\"reply\":\"Local Mailbox Idle\"}";
        }

        std::string msg = mailbox_.front();
        mailbox_.pop();
        return msg;
    }

    void disconnect() override {
        std::lock_guard<std::mutex> lock(mutex_);
        is_connected_ = false;
        while (!mailbox_.empty()) mailbox_.pop();
        std::cout << "[LocalSocketTransport] Mailbox flushed and closed." << std::endl;
    }
};

// ============================================================================
// 3. Security Layer
// ============================================================================

class AuditLogger {
private:
    std::mutex mutex_;

    std::string GetCurrentTimestamp() {
        auto now = std::chrono::system_clock::now();
        auto in_time_t = std::chrono::system_clock::to_time_t(now);
        std::stringstream ss;
        ss << std::put_time(std::localtime(&in_time_t), "%Y-%m-%d %H:%M:%S");
        return ss.str();
    }

public:
    void log(const std::string& user, const std::string& action, const std::string& result) {
        std::lock_guard<std::mutex> lock(mutex_);
        std::cout << "[AUDIT LOG | " << GetCurrentTimestamp() << "] Operator=" << user
                  << " | Action=" << action << " | Result=" << result << std::endl;
    }
};

class PermissionManager {
public:
    bool authorize(Role role, const Command& cmd) {
        switch (cmd.type) {
            case CommandType::OPEN_APP:
                return (role == Role::ADMIN || role == Role::SYSTEM);
            case CommandType::SYNC_FEED:
                return true;
            case CommandType::FILE_READ:
                return true;
            default:
                return false;
        }
    }
};

// ============================================================================
// 4. Command Parser, Validator, Router
// ============================================================================

class CommandParser {
public:
    Command parse(const std::string& rawInput) {
        Command cmd{CommandType::UNKNOWN, ""};

        size_t colon_pos = rawInput.find(':');
        if (colon_pos == std::string::npos) {
            cmd.payload = rawInput;
            return cmd;
        }

        std::string cmd_str = rawInput.substr(0, colon_pos);
        std::string payload = rawInput.substr(colon_pos + 1);

        cmd_str.erase(
            std::remove_if(cmd_str.begin(), cmd_str.end(),
                [](unsigned char ch) { return std::isspace(ch); }),
            cmd_str.end()
        );

        if (cmd_str == "open") {
            cmd.type = CommandType::OPEN_APP;
        } else if (cmd_str == "sync") {
            cmd.type = CommandType::SYNC_FEED;
        } else if (cmd_str == "read") {
            cmd.type = CommandType::FILE_READ;
        }

        cmd.payload = payload;
        return cmd;
    }
};

class CommandValidator {
public:
    bool validate(const Command& cmd, std::string& out_error) {
        if (cmd.type == CommandType::UNKNOWN) {
            out_error = "Invalid/Unknown command instruction header.";
            return false;
        }

        std::string payload = cmd.payload;
        payload.erase(
            std::remove_if(payload.begin(), payload.end(),
                [](unsigned char ch) { return std::isspace(ch); }),
            payload.end()
        );

        if (payload.empty()) {
            out_error = "Command payload parameter cannot be empty.";
            return false;
        }

        std::string lower = cmd.payload;
        std::transform(lower.begin(), lower.end(), lower.begin(),
            [](unsigned char c) { return std::tolower(c); });

        if (lower.find("rm -rf") != std::string::npos ||
            lower.find("drop table") != std::string::npos ||
            lower.find("format") != std::string::npos) {
            out_error = "Security validation exception: Dangerous keyword pattern detected.";
            return false;
        }

        return true;
    }
};

class ProcessService {
public:
    bool launch(const std::string& app) {
        std::cout << "[ProcessService] Safely launching binary '" << app << "' in background thread." << std::endl;
        return true;
    }
};

class FeedService {
public:
    std::string sync() {
        std::cout << "[FeedService] Pulling academic RSS & YouTube video indices..." << std::endl;
        return "FeedData: {NASA: 'Mars Rover APOD', YouTube: 'Ha Ru Channel upload 0'}";
    }
};

class FileService {
public:
    std::string read(const std::string& path) {
        std::cout << "[FileService] Parsing secure local workspace file: " << path << std::endl;
        return "FileContent: {spec_version: 3.5, architecture: 'geodesic_dome'}";
    }
};

class MemoryService {
public:
    bool store(const std::string& record) {
        std::cout << "[MemoryService] Committing wisdom log to SQLite Warm DB & JSON Cold files." << std::endl;
        return true;
    }
};

class CommandRouter {
private:
    ProcessService process_service_;
    FeedService feed_service_;
    FileService file_service_;
    MemoryService memory_service_;

public:
    std::string route(const Command& cmd) {
        switch (cmd.type) {
            case CommandType::OPEN_APP:
                if (process_service_.launch(cmd.payload)) {
                    return "Successfully launched application " + cmd.payload;
                }
                return "Failed to launch application " + cmd.payload;

            case CommandType::SYNC_FEED: {
                std::string feed_res = feed_service_.sync();
                memory_service_.store(feed_res);
                return "Synchronized successfully. " + feed_res;
            }

            case CommandType::FILE_READ: {
                std::string content = file_service_.read(cmd.payload);
                memory_service_.store("Read file: " + cmd.payload);
                return content;
            }

            default:
                return "Unknown routing pathway.";
        }
    }
};

// ============================================================================
// 5. Recovery Layer
// ============================================================================

class RetryManager {
public:
    template<typename T>
    bool execute(T operation, int retries) {
        int attempt = 0;
        while (attempt < retries) {
            try {
                if (operation()) {
                    return true;
                }
            } catch (const std::exception& e) {
                std::cerr << "[RetryManager] Warning: Exception caught on attempt "
                          << (attempt + 1) << ": " << e.what() << std::endl;
            }
            attempt++;
            std::this_thread::sleep_for(std::chrono::milliseconds(50 * attempt));
        }
        return false;
    }
};

class HealthMonitor {
public:
    bool isAlive() {
        std::cout << "[HealthMonitor] Checking threads, sockets, and memory pools -> STABLE" << std::endl;
        return true;
    }
};

// ============================================================================
// 6. Core Controller
// ============================================================================

class CoreController {
private:
    std::unique_ptr<ITransport> transport_;
    CommandParser parser_;
    CommandRouter router_;
    CommandValidator validator_;
    AuditLogger logger_;
    PermissionManager permission_;
    RetryManager retry_;
    HealthMonitor health_;
    std::mutex core_mutex_;

public:
    CoreController(std::unique_ptr<ITransport> transport)
        : transport_(std::move(transport)) {
        retry_.execute([this]() {
            return transport_ && transport_->connect();
        }, 3);
    }

    void swapTransport(std::unique_ptr<ITransport> new_transport) {
        std::lock_guard<std::mutex> lock(core_mutex_);
        std::cout << "[CoreController] Swapping active Transport Layer..." << std::endl;

        if (transport_) {
            transport_->disconnect();
        }

        transport_ = std::move(new_transport);

        bool connected = retry_.execute([this]() {
            return transport_ && transport_->connect();
        }, 3);

        if (!connected) {
            std::cerr << "[CoreController] Failed to re-establish new transport connection after retries." << std::endl;
        }
    }

    void process(Role operator_role, const std::string& rawCommand) {
        std::lock_guard<std::mutex> lock(core_mutex_);
        std::string role_str = RoleToString(operator_role);

        std::cout << "\n==============================================\n";
        std::cout << "  ARA Pipeline Execution Start: " << rawCommand << "\n";
        std::cout << "==============================================\n";

        if (!health_.isAlive()) {
            logger_.log(role_str, rawCommand, "ERROR: Core degraded state");
            return;
        }

        if (!transport_ || !transport_->send(rawCommand)) {
            logger_.log(role_str, rawCommand, "ERROR: Transport send failed");
            return;
        }

        std::string received_raw = transport_->receive();
        std::cout << "[CoreController] Received payload from active transport: " << received_raw << std::endl;

        Command cmd = parser_.parse(rawCommand);

        std::string err_msg;
        if (!validator_.validate(cmd, err_msg)) {
            std::cerr << "[CoreController] Validation failed: " << err_msg << std::endl;
            logger_.log(role_str, rawCommand, "REJECTED: " + err_msg);
            return;
        }

        if (!permission_.authorize(operator_role, cmd)) {
            std::cerr << "[CoreController] Permission Denied for operator role: " << role_str << std::endl;
            logger_.log(role_str, rawCommand, "DENIED: Insufficient permissions");
            return;
        }

        std::string execution_result = router_.route(cmd);
        std::cout << "[CoreController] Service Execution Result: " << execution_result << std::endl;

        logger_.log(role_str, CommandTypeToString(cmd.type) + " " + cmd.payload,
                    "SUCCESS: " + execution_result);
    }
};

// ============================================================================
// 7. Main
// ============================================================================

int main() {
    std::cout << "=== ARA CORE C++ ARCHITECTURE SIMULATION START ===" << std::endl;

    auto controller = std::make_unique<CoreController>(std::make_unique<LocalSocketTransport>());

    controller->process(Role::USER, "sync:feed");
    controller->process(Role::USER, "open:calculator");
    controller->process(Role::ADMIN, "open:notepad");
    controller->process(Role::ADMIN, "open:calc && rm -rf /");

    std::cout << "\n[Simulation] Simulating on-the-fly transport switching..." << std::endl;
    controller->swapTransport(std::make_unique<TcpTransport>("127.0.0.1", 9091));
    controller->process(Role::ADMIN, "read:greenhouse_spec.md");

    controller->swapTransport(std::make_unique<PipeTransport>("ara_ipc_pipe"));
    controller->process(Role::SYSTEM, "sync:feed");

    std::cout << "\n=== ARA CORE C++ ARCHITECTURE SIMULATION END ===" << std::endl;
    return 0;
}