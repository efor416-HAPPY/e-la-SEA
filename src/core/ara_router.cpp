// src/core/ara_router.cpp
#include <iostream>
#include <string>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <vector>
#include <thread>
#include <map>
#include <mutex>
#include <algorithm>

class MessageRouter {
private:
    int server_fd;
    std::string socket_path = "/tmp/ara_system.sock";
    std::map<std::string, int> agent_connections;
    std::mutex conn_mutex;

    // Helper to extract a value from JSON string (e.g., "action": "REGISTER")
    std::string ExtractJsonValue(const std::string& json_str, const std::string& key) {
        size_t key_pos = json_str.find("\"" + key + "\"");
        if (key_pos == std::string::npos) return "";
        
        size_t colon_pos = json_str.find(":", key_pos);
        if (colon_pos == std::string::npos) return "";
        
        size_t start_quote = json_str.find("\"", colon_pos);
        if (start_quote == std::string::npos) return "";
        
        size_t end_quote = json_str.find("\"", start_quote + 1);
        if (end_quote == std::string::npos) return "";
        
        return json_str.substr(start_quote + 1, end_quote - start_quote - 1);
    }

public:
    bool Start() {
        server_fd = socket(AF_UNIX, SOCK_STREAM, 0);
        if (server_fd == -1) {
            std::cerr << "[Router Error] Failed to create socket." << std::endl;
            return false;
        }

        unlink(socket_path.c_str());

        sockaddr_un addr{};
        addr.sun_family = AF_UNIX;
        strncpy(addr.sun_path, socket_path.c_str(), sizeof(addr.sun_path) - 1);

        if (bind(server_fd, (struct sockaddr*)&addr, sizeof(addr)) == -1) {
            std::cerr << "[Router Error] Bind failed." << std::endl;
            return false;
        }
        
        if (listen(server_fd, 10) == -1) {
            std::cerr << "[Router Error] Listen failed." << std::endl;
            return false;
        }

        std::cout << "[ARA Core] Unix Socket Router 가동 중: " << socket_path << std::endl;
        return true;
    }

    void HandleClient(int client_fd) {
        std::vector<char> buffer(4096);
        while (true) {
            ssize_t bytes_read = read(client_fd, buffer.data(), buffer.size());
            if (bytes_read <= 0) break;

            std::string raw_msg(buffer.data(), bytes_read);
            std::cout << "[Router 데이터 수신]: " << raw_msg << std::endl;

            // Packet routing and registration parsing
            std::string action = ExtractJsonValue(raw_msg, "action");
            std::string sender = ExtractJsonValue(raw_msg, "sender");
            std::string target = ExtractJsonValue(raw_msg, "target");

            if (action == "REGISTER" && !sender.empty()) {
                std::lock_guard<std::mutex> lock(conn_mutex);
                agent_connections[sender] = client_fd;
                std::cout << "[Router] 에이전트 등록 성공: " << sender << " (FD: " << client_fd << ")" << std::endl;
            } 
            else if (!target.empty()) {
                int target_fd = -1;
                {
                    std::lock_guard<std::mutex> lock(conn_mutex);
                    auto it = agent_connections.find(target);
                    if (it != agent_connections.end()) {
                        target_fd = it->second;
                    }
                }

                if (target_fd != -1) {
                    ssize_t bytes_written = write(target_fd, raw_msg.c_str(), raw_msg.size());
                    if (bytes_written <= 0) {
                        std::cerr << "[Router Warning] " << target << " 에이전트로 데이터 전송 실패." << std::endl;
                    } else {
                        std::cout << "[Router Routing] " << sender << " -> " << target << " 데이터 포워딩 성공." << std::endl;
                    }
                } else {
                    std::cerr << "[Router Warning] 대상 에이전트 '" << target << "'가 존재하지 않거나 오프라인 상태입니다." << std::endl;
                }
            }
        }

        // Clean up disconnected connection
        {
            std::lock_guard<std::mutex> lock(conn_mutex);
            for (auto it = agent_connections.begin(); it != agent_connections.end(); ) {
                if (it->second == client_fd) {
                    std::cout << "[Router] 에이전트 연결 해제: " << it->first << std::endl;
                    it = agent_connections.erase(it);
                } else {
                    ++it;
                }
            }
        }
        close(client_fd);
    }

    void AcceptLoop() {
        while (true) {
            int client_fd = accept(server_fd, nullptr, nullptr);
            if (client_fd == -1) continue;
            std::thread(&MessageRouter::HandleClient, this, client_fd).detach();
        }
    }

    ~MessageRouter() {
        if (server_fd != -1) {
            close(server_fd);
        }
        unlink(socket_path.c_str());
    }
};

int main() {
    MessageRouter router;
    if (router.Start()) {
        router.AcceptLoop();
    }
    return 0;
}
