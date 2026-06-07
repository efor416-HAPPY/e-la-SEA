package com.ara.platform.planner;

import org.springframework.stereotype.Service;

@Service
public class Planner {
    public String decomposeGoalToTasks(String goalDescription) {
        System.out.println("[Planner] 추론 결과 기반의 Goal -> Task -> SubTask -> Action 분해 계획 수립...");
        return "{ \"tasks\": [\"READ_FILE\", \"PARSE_METADATA\", \"MES_PRODUCT_SYNC\"] }";
    }
}
