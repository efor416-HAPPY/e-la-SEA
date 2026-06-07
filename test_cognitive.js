/**
 * AraRationalCore Cognitive Verification Script
 */
const AraRationalCore = require('./brain.js');

function runCognitiveTest() {
    console.log("==================================================");
    console.log("  ARA Rational Core Cognitive Verification System");
    console.log("==================================================");

    const core = new AraRationalCore();
    let passedTests = 0;
    let totalTests = 0;

    const assertTest = (name, condition, details = "") => {
        totalTests++;
        if (condition) {
            console.log(`[PASS] ${name}`);
            passedTests++;
        } else {
            console.error(`[FAIL] ${name}`);
            if (details) console.error(`       -> ${details}`);
        }
    };

    // Test 1: Instantiation
    assertTest("Class Instantiation Check", core instanceof AraRationalCore);

    // Test 2: Standard Perception & Greeting Stance
    const resNormal = core.perceive("안녕하세요 아라, 오늘 날씨가 참 맑네요.");
    assertTest("Standard Response Generation", resNormal && typeof resNormal.text === "string" && resNormal.text.length > 0);
    assertTest("Standard Stance Identification", resNormal.stance === "wise_companion", `Stance: ${resNormal.stance}`);

    // Test 3: Distress Signal Detection (altruistic stance)
    const resDistress = core.perceive("오늘 프로젝트에 계속 에러가 나고 실패해서 너무 힘들고 슬퍼요.");
    assertTest("Distress Signal Recognition Stance", resDistress.stance === "devoted_helper", `Stance: ${resDistress.stance}`);
    assertTest("Distress Signal Altruism Influence", resDistress.pulse === 0.6, `Pulse: ${resDistress.pulse}`);

    // Test 4: Dynamic Code Analysis Detection (cognitive enhancement check)
    const pythonCode = `def calculate_sum(a, b):
    # This is a comment
    return a + b
`;
    const resCode = core.perceive(pythonCode);
    assertTest("Real-time Code Detection Recognition", resCode.stance === "joyful_scholar", `Stance: ${resCode.stance}`);
    assertTest("Code Analysis Synaptic Pulse Voltage Boost", resCode.pulse === 2.8, `Pulse: ${resCode.pulse}`);
    assertTest("Code Review Content Verification", resCode.text.includes("코드 및 알고리즘 정밀 분석") && resCode.text.includes("Python"), `Response snippet: ${resCode.text.substring(0, 100)}`);

    // Test 5: Self-Reflection & Memory Recall (cognitive enhancement check)
    // Wisdom bank has elements from previous runs
    const resReflection = core.perceive("그동안 축적된 지혜성찰 정보를 보여줘.");
    assertTest("Self-Reflection Stance", resReflection.stance === "wise_companion");
    assertTest("Self-Reflection Response Verification", resReflection.text.includes("지혜 성찰") && resReflection.text.includes("인격적 성숙도"), `Response snippet: ${resReflection.text.substring(0, 100)}`);

    console.log("--------------------------------------------------");
    console.log(`COGNITIVE VERIFICATION RESULT: ${passedTests}/${totalTests} Passed`);
    console.log("==================================================");

    if (passedTests === totalTests) {
        process.exit(0);
    } else {
        process.exit(1);
    }
}

runCognitiveTest();
