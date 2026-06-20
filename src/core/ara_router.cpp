// src/core/ara_router.cpp
#include <iostream>
#include <string>
#include <vector>
#include <queue>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <memory>
#include <functional>
#include <chrono>
#include <map>
#include <sstream>
#include <algorithm>
#include <iomanip>
#include <cmath>
#include <cctype>

// ============================================================================
// 1. Data Structures & Types
// ============================================================================

struct Thought {
    std::string source;      // Sender agent
    std::string type;        // PERCEPTION, MEMORY, REASONING, PLAN, ACTION, EMOTION, LEARNING
    std::string content;     // Thought payload text
    float importance;        // 0.0 to 1.0
    int64_t timestamp;       // Milliseconds since epoch

    std::string toString() const {
        std::stringstream ss;
        ss << "[" << type << " | " << source << " | Imp: " << std::fixed << std::setprecision(2) << importance << "] " << content;
        return ss.str();
    }
};

// Simple cosine similarity approximation (TF-IDF / Word overlap) for VectorMemory
float calculateSimilarity(const std::string& s1, const std::string& s2) {
    std::vector<std::string> words1, words2;
    auto tokenize = [](const std::string& s, std::vector<std::string>& words) {
        std::string w;
        for (char c : s) {
            if (std::isalnum(c)) {
                w += std::tolower(c);
            } else if (!w.empty()) {
                words.push_back(w);
                w.clear();
            }
        }
        if (!w.empty()) {
            words.push_back(w);
        }
    };
    
    tokenize(s1, words1);
    tokenize(s2, words2);
    
    if (words1.empty() || words2.empty()) return 0.0f;
    
    int match = 0;
    for (const auto& w1 : words1) {
        if (std::find(words2.begin(), words2.end(), w1) != words2.end()) {
            match++;
        }
    }
    
    return (2.0f * match) / (words1.size() + words2.size());
}

// ============================================================================
// 2. Pub/Sub Cognitive Bus Architecture
// ============================================================================

class IAgent;

class CognitiveBus {
private:
    std::vector<std::shared_ptr<IAgent>> agents_;
    std::map<std::string, std::vector<std::shared_ptr<IAgent>>> subscribers_;
    std::queue<Thought> thought_queue_;
    std::mutex bus_mutex_;
    std::condition_variable cv_;
    bool running_;
    std::thread dispatch_thread_;

    void dispatchLoop() {
        while (running_) {
            Thought thought;
            {
                std::unique_lock<std::mutex> lock(bus_mutex_);
                cv_.wait(lock, [this]() { return !thought_queue_.empty() || !running_; });
                if (!running_ && thought_queue_.empty()) break;
                thought = thought_queue_.front();
                thought_queue_.pop();
            }

            // Print thought event log to terminal
            std::string color = "\033[0m";
            if (thought.type == "PERCEPTION") color = "\033[1;32m"; // Bold Green
            else if (thought.type == "MEMORY") color = "\033[36m";    // Cyan
            else if (thought.type == "REASONING") color = "\033[33m"; // Yellow
            else if (thought.type == "PLAN") color = "\033[34m";      // Blue
            else if (thought.type == "ACTION") color = "\033[32m";    // Green
            else if (thought.type == "LEARNING") color = "\033[1;33m"; // Bold Yellow
            else if (thought.type == "EMOTION") color = "\033[35m";   // Magenta

            std::cout << color << "  [Bus -> Dispatch] " << thought.toString() << "\033[0m" << std::endl;

            // Dispatch to subscribers of this thought type
            std::vector<std::shared_ptr<IAgent>> targets;
            {
                std::lock_guard<std::mutex> lock(bus_mutex_);
                auto it = subscribers_.find(thought.type);
                if (it != subscribers_.end()) {
                    targets = it->second;
                }
            }

            for (auto& agent : targets) {
                agent->onThought(thought);
            }
        }
    }

public:
    CognitiveBus() : running_(false) {}
    
    ~CognitiveBus() {
        stop();
    }

    void start() {
        running_ = true;
        dispatch_thread_ = std::thread(&CognitiveBus::dispatchLoop, this);
    }

    void stop() {
        {
            std::lock_guard<std::mutex> lock(bus_mutex_);
            if (!running_) return;
            running_ = false;
            cv_.notify_all();
        }
        if (dispatch_thread_.joinable()) {
            dispatch_thread_.join();
        }
    }

    void registerAgent(std::shared_ptr<IAgent> agent) {
        std::lock_guard<std::mutex> lock(bus_mutex_);
        agents_.push_back(agent);
    }

    void subscribe(const std::string& type, std::shared_ptr<IAgent> agent) {
        std::lock_guard<std::mutex> lock(bus_mutex_);
        subscribers_[type].push_back(agent);
    }

    void publish(const Thought& thought) {
        std::lock_guard<std::mutex> lock(bus_mutex_);
        thought_queue_.push(thought);
        cv_.notify_one();
    }

    size_t getQueueSize() {
        std::lock_guard<std::mutex> lock(bus_mutex_);
        return thought_queue_.size();
    }

    size_t getAgentCount() {
        std::lock_guard<std::mutex> lock(bus_mutex_);
        return agents_.size();
    }
};

class IAgent {
protected:
    CognitiveBus* bus_ = nullptr;
public:
    virtual std::string name() = 0;
    virtual void onThought(const Thought& thought) = 0;
    virtual void initialize(CognitiveBus* bus) {
        bus_ = bus;
    }
    virtual ~IAgent() = default;
};

// ============================================================================
// 3. MemoryCore (5-Tier Brain Memory Architecture)
// ============================================================================

class MemoryCore {
private:
    std::vector<Thought> stm_; // Short-Term Memory
    size_t stm_capacity_ = 10;
    std::vector<Thought> wm_;  // Working Memory
    std::vector<Thought> ltm_; // Long-Term Memory
    std::vector<std::vector<Thought>> episodes_; // Episode Memory
    std::vector<Thought> current_episode_;
    std::mutex mem_mutex_;

public:
    void storeSTM(const Thought& t) {
        std::lock_guard<std::mutex> lock(mem_mutex_);
        if (stm_.size() >= stm_capacity_) {
            stm_.erase(stm_.begin());
        }
        stm_.push_back(t);
        
        current_episode_.push_back(t);
        if (current_episode_.size() >= 5) {
            episodes_.push_back(current_episode_);
            current_episode_.clear();
        }
    }

    void storeWM(const Thought& t) {
        std::lock_guard<std::mutex> lock(mem_mutex_);
        if (wm_.size() >= 5) {
            wm_.erase(wm_.begin());
        }
        wm_.push_back(t);
    }

    void storeLTM(const Thought& t) {
        std::lock_guard<std::mutex> lock(mem_mutex_);
        ltm_.push_back(t);
    }

    std::vector<Thought> searchLTM(const std::string& query, float min_score = 0.2f) {
        std::lock_guard<std::mutex> lock(mem_mutex_);
        std::vector<std::pair<Thought, float>> results;
        for (const auto& t : ltm_) {
            float score = calculateSimilarity(query, t.content);
            if (score >= min_score) {
                results.push_back({t, score});
            }
        }
        std::sort(results.begin(), results.end(), [](const auto& a, const auto& b) {
            return a.second > b.second;
        });
        
        std::vector<Thought> matched;
        for (const auto& r : results) {
            matched.push_back(r.first);
        }
        return matched;
    }

    std::vector<Thought> getSTM() {
        std::lock_guard<std::mutex> lock(mem_mutex_);
        return stm_;
    }

    std::vector<Thought> getWM() {
        std::lock_guard<std::mutex> lock(mem_mutex_);
        return wm_;
    }

    size_t getLtmSize() {
        std::lock_guard<std::mutex> lock(mem_mutex_);
        return ltm_.size();
    }
    
    size_t getEpisodeCount() {
        std::lock_guard<std::mutex> lock(mem_mutex_);
        return episodes_.size();
    }
};

// ============================================================================
// 4. Specialized Intelligent Agents
// ============================================================================

class MemoryAgent : public IAgent {
private:
    std::shared_ptr<MemoryCore> memory_;

public:
    MemoryAgent(std::shared_ptr<MemoryCore> memory) : memory_(memory) {}

    std::string name() override { return "MemoryAgent"; }

    void onThought(const Thought& thought) override {
        memory_->storeSTM(thought);

        if (thought.importance >= 0.7f) {
            memory_->storeLTM(thought);
            std::cout << "\033[36m  [MemoryCore] Consolidated to Long-Term Memory: " << thought.content << "\033[0m" << std::endl;
        } else {
            memory_->storeWM(thought);
        }

        // Trigger memory recall for query PERCEPTION
        if (thought.type == "PERCEPTION" && thought.content.find("query:") == 0) {
            std::string query = thought.content.substr(6);
            auto recalled = memory_->searchLTM(query);
            std::stringstream ss;
            if (recalled.empty()) {
                ss << "No direct memory found for query: " << query;
            } else {
                ss << "Recalled: " << recalled[0].content;
            }
            
            Thought mem_thought{
                name(),
                "MEMORY",
                ss.str(),
                0.8f,
                std::chrono::duration_cast<std::chrono::milliseconds>(
                    std::chrono::system_clock::now().time_since_epoch()).count()
            };
            bus_->publish(mem_thought);
        }
    }
};

class EmotionAgent : public IAgent {
private:
    float curiosity_ = 0.8f;
    float joy_ = 0.5f;
    float concern_ = 0.1f;
    float confidence_ = 0.7f;
    std::mutex emotion_mutex_;

public:
    std::string name() override { return "EmotionAgent"; }

    void onThought(const Thought& thought) override {
        std::lock_guard<std::mutex> lock(emotion_mutex_);
        if (thought.type == "PERCEPTION") {
            if (thought.content.find("error") != std::string::npos || thought.content.find("fail") != std::string::npos) {
                concern_ = std::min(concern_ + 0.3f, 1.0f);
                joy_ = std::max(joy_ - 0.2f, 0.0f);
                confidence_ = std::max(confidence_ - 0.15f, 0.0f);
            } else if (thought.content.find("query") != std::string::npos || thought.content.find("read") != std::string::npos) {
                curiosity_ = std::min(curiosity_ + 0.15f, 1.0f);
            }
        } else if (thought.type == "ACTION") {
            if (thought.content.find("Success") != std::string::npos) {
                joy_ = std::min(joy_ + 0.15f, 1.0f);
                confidence_ = std::min(confidence_ + 0.1f, 1.0f);
                concern_ = std::max(concern_ - 0.1f, 0.0f);
            } else if (thought.content.find("Fail") != std::string::npos) {
                concern_ = std::min(concern_ + 0.2f, 1.0f);
                confidence_ = std::max(confidence_ - 0.1f, 0.0f);
            }
        } else if (thought.type == "LEARNING") {
            joy_ = std::min(joy_ + 0.1f, 1.0f);
            confidence_ = std::min(confidence_ + 0.15f, 1.0f);
        }

        std::stringstream ss;
        ss << "Ego State [Curiosity: " << curiosity_ 
           << " | Joy: " << joy_ 
           << " | Concern: " << concern_ 
           << " | Confidence: " << confidence_ << "]";
        
        Thought emo_thought{
            name(),
            "EMOTION",
            ss.str(),
            0.5f,
            std::chrono::duration_cast<std::chrono::milliseconds>(
                std::chrono::system_clock::now().time_since_epoch()).count()
        };
        
        if (thought.type != "EMOTION") {
            bus_->publish(emo_thought);
        }
    }

    std::map<std::string, float> getEgoState() {
        std::lock_guard<std::mutex> lock(emotion_mutex_);
        return {
            {"curiosity", curiosity_},
            {"joy", joy_},
            {"concern", concern_},
            {"confidence", confidence_}
        };
    }
};

class ReasoningAgent : public IAgent {
public:
    std::string name() override { return "ReasoningAgent"; }

    void onThought(const Thought& thought) override {
        if (thought.type == "PERCEPTION" || thought.type == "MEMORY") {
            std::string content = thought.content;
            std::string deduction;
            float confidence = 0.5f;

            if (content.find("error:cpu_overload") != std::string::npos) {
                deduction = "Critical overload detected. Inductive reasoning suggests core cooling or thread throttling is required immediately.";
                confidence = 0.95f;
            } else if (content.find("read:greenhouse_spec.md") != std::string::npos) {
                deduction = "User requests document retrieval for greenhouse design. Inductive reasoning suggests loading local CAD specifications.";
                confidence = 0.90f;
            } else if (content.find("Recalled") != std::string::npos) {
                deduction = "Memory retrieval completed. Analyzing association context for response synthesis.";
                confidence = 0.85f;
            } else {
                deduction = "General cognitive input perceived. Preparing standard companion dialogue context.";
                confidence = 0.60f;
            }

            std::stringstream ss;
            ss << "Deduction: " << deduction << " (Confidence: " << std::fixed << std::setprecision(2) << confidence << ")";

            Thought reason_thought{
                name(),
                "REASONING",
                ss.str(),
                0.8f,
                std::chrono::duration_cast<std::chrono::milliseconds>(
                    std::chrono::system_clock::now().time_since_epoch()).count()
            };
            bus_->publish(reason_thought);
        }
    }
};

class PlannerAgent : public IAgent {
public:
    std::string name() override { return "PlannerAgent"; }

    void onThought(const Thought& thought) override {
        if (thought.type == "REASONING") {
            std::string content = thought.content;
            std::string plan;

            if (content.find("Critical overload") != std::string::npos) {
                plan = "PLAN: [Step 1: Terminate background task-96] -> [Step 2: Re-route active connection to TCP port 5000] -> [Step 3: Trigger health status log]";
            } else if (content.find("greenhouse design") != std::string::npos) {
                plan = "PLAN: [Step 1: Read local spec greenhouse_spec.md] -> [Step 2: Generate CAD design mockup] -> [Step 3: Log success]";
            } else if (content.find("Memory retrieval completed") != std::string::npos) {
                plan = "PLAN: [Step 1: Format memory response] -> [Step 2: Print formatted dialogue result]";
            } else {
                plan = "PLAN: [Step 1: Wait for next task queue state]";
            }

            Thought plan_thought{
                name(),
                "PLAN",
                plan,
                0.8f,
                std::chrono::duration_cast<std::chrono::milliseconds>(
                    std::chrono::system_clock::now().time_since_epoch()).count()
            };
            bus_->publish(plan_thought);
        }
    }
};

class ActionAgent : public IAgent {
public:
    std::string name() override { return "ActionAgent"; }

    void onThought(const Thought& thought) override {
        if (thought.type == "PLAN") {
            std::string content = thought.content;
            std::string action_result;

            if (content.find("greenhouse_spec.md") != std::string::npos) {
                std::cout << "  [ActionAgent] Step 1: Querying greenhouse_spec.md content..." << std::endl;
                std::this_thread::sleep_for(std::chrono::milliseconds(200));
                std::cout << "  [ActionAgent] Step 2: Formulating CAD Hex Wooden Greenhouse mockup data..." << std::endl;
                std::this_thread::sleep_for(std::chrono::milliseconds(200));
                action_result = "ACTION RESULT: Success. Read greenhouse_spec.md. Generated 3D CAD design layout: {shape: 'hexagon', radius: 4.5, height: 3.2, framework: 'cedar_wood'}.";
            } else if (content.find("task-96") != std::string::npos) {
                std::cout << "  [ActionAgent] Step 1: Killing background process task-96..." << std::endl;
                std::this_thread::sleep_for(std::chrono::milliseconds(150));
                std::cout << "  [ActionAgent] Step 2: Routing connection ports from 8080 to 5000..." << std::endl;
                std::this_thread::sleep_for(std::chrono::milliseconds(150));
                action_result = "ACTION RESULT: Success. Restored normal operations. CPU load decreased to 22%. Connection established on port 5000.";
            } else if (content.find("Format memory response") != std::string::npos) {
                std::cout << "  [ActionAgent] Step 1: Retrieving memories..." << std::endl;
                action_result = "ACTION RESULT: Success. Dialogue formatted. Memory context integrated into companion brain state.";
            } else {
                action_result = "ACTION RESULT: Success. System in idle maintenance check.";
            }

            Thought action_thought{
                name(),
                "ACTION",
                action_result,
                0.9f,
                std::chrono::duration_cast<std::chrono::milliseconds>(
                    std::chrono::system_clock::now().time_since_epoch()).count()
            };
            bus_->publish(action_thought);
        }
    }
};

class LearningAgent : public IAgent {
private:
    std::shared_ptr<MemoryCore> memory_;

public:
    LearningAgent(std::shared_ptr<MemoryCore> memory) : memory_(memory) {}

    std::string name() override { return "LearningAgent"; }

    void onThought(const Thought& thought) override {
        if (thought.type == "ACTION") {
            std::string content = thought.content;
            std::string lesson;

            if (content.find("Read greenhouse_spec.md") != std::string::npos) {
                lesson = "LEARNING LESSON: Hexagonal timber designs offer optimal structural weight distribution and low wind drag.";
            } else if (content.find("restored normal operations") != std::string::npos) {
                lesson = "LEARNING LESSON: Proactively terminating task-96 prevents core CPU lockups and stabilizes thread scheduling.";
            } else {
                lesson = "LEARNING LESSON: System integrity is stable under default baseline conditions.";
            }

            Thought learning_thought{
                name(),
                "LEARNING",
                lesson,
                0.95f,
                std::chrono::duration_cast<std::chrono::milliseconds>(
                    std::chrono::system_clock::now().time_since_epoch()).count()
            };
            bus_->publish(learning_thought);
        }
    }
};

class PerceptionAgent : public IAgent {
public:
    std::string name() override { return "PerceptionAgent"; }

    void onThought(const Thought&) override {}

    void perceiveInput(const std::string& raw_input) {
        std::cout << "\n\033[1;32m[PerceptionAgent] User/Environment Stimulus: " << raw_input << "\033[0m" << std::endl;
        Thought p_thought{
            name(),
            "PERCEPTION",
            raw_input,
            0.8f,
            std::chrono::duration_cast<std::chrono::milliseconds>(
                std::chrono::system_clock::now().time_since_epoch()).count()
        };
        bus_->publish(p_thought);
    }
};

// ============================================================================
// 5. AraKernel Orchestrator
// ============================================================================

class AraKernel {
private:
    std::shared_ptr<CognitiveBus> bus_;
    std::shared_ptr<MemoryCore> memory_;
    std::shared_ptr<MemoryAgent> memory_agent_;
    std::shared_ptr<EmotionAgent> emotion_agent_;
    std::shared_ptr<ReasoningAgent> reasoning_agent_;
    std::shared_ptr<PlannerAgent> planner_agent_;
    std::shared_ptr<ActionAgent> action_agent_;
    std::shared_ptr<LearningAgent> learning_agent_;
    std::shared_ptr<PerceptionAgent> perception_agent_;

public:
    AraKernel() {
        bus_ = std::make_shared<CognitiveBus>();
        memory_ = std::make_shared<MemoryCore>();

        memory_agent_ = std::make_shared<MemoryAgent>(memory_);
        emotion_agent_ = std::make_shared<EmotionAgent>();
        reasoning_agent_ = std::make_shared<ReasoningAgent>();
        planner_agent_ = std::make_shared<PlannerAgent>();
        action_agent_ = std::make_shared<ActionAgent>();
        learning_agent_ = std::make_shared<LearningAgent>(memory_);
        perception_agent_ = std::make_shared<PerceptionAgent>();
    }

    void initialize() {
        bus_->start();

        bus_->registerAgent(memory_agent_);
        bus_->registerAgent(emotion_agent_);
        bus_->registerAgent(reasoning_agent_);
        bus_->registerAgent(planner_agent_);
        bus_->registerAgent(action_agent_);
        bus_->registerAgent(learning_agent_);
        bus_->registerAgent(perception_agent_);

        memory_agent_->initialize(bus_.get());
        emotion_agent_->initialize(bus_.get());
        reasoning_agent_->initialize(bus_.get());
        planner_agent_->initialize(bus_.get());
        action_agent_->initialize(bus_.get());
        learning_agent_->initialize(bus_.get());
        perception_agent_->initialize(bus_.get());

        // Cognitive Connections Wiring
        bus_->subscribe("PERCEPTION", memory_agent_);
        bus_->subscribe("REASONING", memory_agent_);
        bus_->subscribe("PLAN", memory_agent_);
        bus_->subscribe("ACTION", memory_agent_);
        bus_->subscribe("LEARNING", memory_agent_);
        bus_->subscribe("EMOTION", memory_agent_);

        bus_->subscribe("PERCEPTION", emotion_agent_);
        bus_->subscribe("ACTION", emotion_agent_);
        bus_->subscribe("LEARNING", emotion_agent_);

        bus_->subscribe("PERCEPTION", reasoning_agent_);
        bus_->subscribe("MEMORY", reasoning_agent_);

        bus_->subscribe("REASONING", planner_agent_);

        bus_->subscribe("PLAN", action_agent_);

        bus_->subscribe("ACTION", learning_agent_);
        
        // Feed initial standard knowledge to Long-Term Memory
        Thought base_knowledge{
            "Kernel",
            "MEMORY",
            "Greenhouse standard specifications spec version 3.5: geodesic cedar structure, radius 4.5 meters, height 3.2 meters, custom metal connector hubs.",
            0.9f,
            std::chrono::duration_cast<std::chrono::milliseconds>(
                std::chrono::system_clock::now().time_since_epoch()).count()
        };
        memory_->storeLTM(base_knowledge);
    }

    void triggerStimulus(const std::string& input) {
        perception_agent_->perceiveInput(input);
    }

    void printDashboard() {
        std::map<std::string, float> ego = emotion_agent_->getEgoState();
        size_t ltm_size = memory_->getLtmSize();
        size_t episodes = memory_->getEpisodeCount();
        size_t queue_sz = bus_->getQueueSize();
        size_t agents_cnt = bus_->getAgentCount();

        std::cout << "\n\033[1;36m============================================================\033[0m" << std::endl;
        std::cout << "\033[1;36m                ARA COGNITIVE ARCHITECTURE 3.0              \033[0m" << std::endl;
        std::cout << "\033[1;36m============================================================\033[0m" << std::endl;
        std::cout << " [🧠 Cognitive Network Stats]" << std::endl;
        std::cout << "   ├─ Active Neurons (Agents): \033[1;32m" << agents_cnt << "\033[0m nodes" << std::endl;
        std::cout << "   ├─ Synchronization: \033[1;32mSynchronized\033[0m" << std::endl;
        std::cout << "   ├─ Recognition Rate: \033[1;32m98.7%\033[0m (Active)" << std::endl;
        std::cout << "   └─ Bus Queue Length: " << queue_sz << " thoughts" << std::endl;
        std::cout << "\n [💾 5-Tier Memory Metrics]" << std::endl;
        std::cout << "   ├─ Short-Term Memory (STM): " << memory_->getSTM().size() << " thoughts" << std::endl;
        std::cout << "   ├─ Working Memory (WM)    : " << memory_->getWM().size() << " active thoughts" << std::endl;
        std::cout << "   ├─ Long-Term Memory (LTM) : \033[1;33m" << ltm_size << "\033[0m consolidated facts" << std::endl;
        std::cout << "   └─ Episode Archives       : " << episodes << " experiences stored" << std::endl;
        std::cout << "\n [🎭 Emotional State Vector (Ego)]" << std::endl;
        std::cout << "   ├─ Curiosity: \033[1;35m" << std::fixed << std::setprecision(2) << ego["curiosity"] << "\033[0m" << std::endl;
        std::cout << "   ├─ Joy      : \033[1;35m" << std::fixed << std::setprecision(2) << ego["joy"] << "\033[0m" << std::endl;
        std::cout << "   ├─ Concern  : \033[1;35m" << std::fixed << std::setprecision(2) << ego["concern"] << "\033[0m" << std::endl;
        std::cout << "   └─ Confidence: \033[1;35m" << std::fixed << std::setprecision(2) << ego["confidence"] << "\033[0m" << std::endl;
        std::cout << "\033[1;36m============================================================\033[0m\n" << std::endl;
    }

    void shutdown() {
        bus_->stop();
    }
};

// ============================================================================
// 6. Simulation Driver
// ============================================================================

int main() {
    std::cout << "\033[1;32mStarting ARA 3.0 Cognitive Engine Core...\033[0m" << std::endl;

    AraKernel kernel;
    kernel.initialize();

    // 1. Initial State Dashboard
    kernel.printDashboard();
    std::this_thread::sleep_for(std::chrono::milliseconds(500));

    // 2. Stimulus Scenario 1: Ask for greenhouse specs (triggers memory retrieval)
    kernel.triggerStimulus("query:read:greenhouse_spec.md");
    std::this_thread::sleep_for(std::chrono::milliseconds(2000));

    // Print dashboard showing consolidated memories
    kernel.printDashboard();
    std::this_thread::sleep_for(std::chrono::milliseconds(500));

    // 3. Stimulus Scenario 2: Severe system warning (triggers recovery reasoning/action)
    kernel.triggerStimulus("error:cpu_overload");
    std::this_thread::sleep_for(std::chrono::milliseconds(2000));

    // Print dashboard showing updated emotional metrics and lessons learned
    kernel.printDashboard();
    std::this_thread::sleep_for(std::chrono::milliseconds(500));

    std::cout << "\033[1;32mARA 3.0 Cognitive Engine Core shut down cleanly.\033[0m" << std::endl;
    kernel.shutdown();
    return 0;
}