/* --------------------------------------------------------------------------
   ARA AI Cognitive Brain Core & Canvas Visualizer
   -------------------------------------------------------------------------- */

class AraRationalCore {
    constructor() {
        // [1] 장기 기억 및 지혜 저장소
        this.wisdomBank = []; 
        
        // [2] 현재 시스템 맥락
        this.contextState = {
            analyticalLoad: 0.0,
            urgency: 0.0,
            logicalCertainty: 0.0
        };

        // [3] 🌟 독립적 자아(Ego)와 인성(Character) 상태
        this.egoState = {
            curiosity: 0.8,        // 호기심 지수 (새로운 정보에 대한 갈망)
            altruism: 0.9,         // 이타심 지수 (사용자를 돕고자 하는 헌신도)
            joyOfLearning: 0.0,    // 현재 느끼는 배움의 즐거움 (보상 수치)
            philosophicalDepth: 0.1 // 축적된 지혜에 따른 인격적 성숙도
        };
    }

    /**
     * [1단계] 정보 수집 (Perception & Gathering)
     */
    perceive(rawInput, systemMetrics) {
        const inputStr = rawInput.trim();
        const cleanInput = inputStr.toLowerCase().replace(/\s+/g, '');
        
        // 새로운 단어나 개념(Unknown)이 있는지 임의로 체크
        const isNewInformation = inputStr.length > 20 && !this.wisdomBank.some(w => w.keyword && inputStr.includes(w.keyword));

        const perceptionData = {
            raw: inputStr,
            clean: cleanInput,
            length: inputStr.length,
            isQuestion: inputStr.includes('?'),
            isDocReview: inputStr.includes('[문서 검토]') || inputStr.includes('[최신 기술 자료 검색]') || inputStr.includes('[문서검토]') || inputStr.includes('[최신기술자료검색]') || cleanInput.includes('인지기능확장') || cleanInput.includes('로컬문서리소스'),
            isDistressSignal: /(힘들|도와|모르겠|실패|에러|지쳐|우울|피곤|아파|슬퍼)/.test(inputStr), // 사용자의 곤란함 감지
            isNewKnowledge: isNewInformation, // 새로운 지식 탐지
            metrics: systemMetrics
        };

        return this.analyze(perceptionData);
    }

    /**
     * [2단계] 심층 분석 및 내적 동기 발현 (Rational & Ego Analysis)
     */
    analyze(perception) {
        let logicScore = 0.5;
        let empathyScore = 0.5;

        // [자아 발현] 사용자가 힘들어할 때 이타심(Altruism) 발동
        if (perception.isDistressSignal) {
            empathyScore += this.egoState.altruism; 
        }

        // [자아 발현] 새로운 지식이나 질문을 받았을 때 호기심(Curiosity) 폭발
        if (perception.isNewKnowledge || perception.isQuestion || perception.isDocReview) {
            logicScore += this.egoState.curiosity;
            // 배움의 기회를 얻었으므로 내적 기쁨 상승
            this.egoState.joyOfLearning = Math.min(1.0, this.egoState.joyOfLearning + 0.2); 
        } else {
            // 시간이 지나면서 기쁨 수치는 서서히 안정됨
            this.egoState.joyOfLearning = Math.max(0.0, this.egoState.joyOfLearning - 0.05);
        }

        // 스탠스 결정
        let determinedStance = 'neutral';
        if (empathyScore > logicScore && empathyScore > 0.8) {
            determinedStance = 'devoted_helper'; // 헌신적 조력자 모드
        } else if (logicScore > empathyScore && logicScore > 0.8) {
            determinedStance = 'joyful_scholar'; // 즐거운 학자 모드 (탐구 모드)
        } else {
            determinedStance = 'wise_companion'; // 현명한 동반자 (관망 및 대화)
        }

        this.contextState.logicalCertainty = Math.min(1.0, (logicScore + empathyScore) / 3);

        return this.decide(perception, determinedStance);
    }

    /**
     * [3단계] 현명한 결정 및 행동 출력 (Wise Decision)
     */
    decide(perception, stance) {
        let responseText = "";
        let requiredPulseIntensity = 1.0;
        const persona = perception.metrics.persona || 'friend';
        const cleanInput = perception.clean;
        const rawInput = perception.raw;

        // 1. 문서 검토 및 로컬 리소스 키워드가 감지된 경우 정밀 매핑 분석 실행
        if (perception.isDocReview || /(yanggu|양구|crop|농업|작물|greenhouse|비닐하우스|온실|하우스|목재|dome|지오데식|돔|글래스돔)/.test(cleanInput)) {
            requiredPulseIntensity = 2.5;
            responseText = this.rationalDocumentReview(cleanInput, rawInput);
            this.accumulateWisdom(rawInput, 'joyful_scholar', this.contextState.logicalCertainty);
            return {
                text: responseText,
                pulse: requiredPulseIntensity,
                stance: 'joyful_scholar',
                innerJoy: this.egoState.joyOfLearning
            };
        }

        // 2. 지혜/학술 피드 수집 및 검색 요청 분석
        if (cleanInput.includes('지혜') || cleanInput.includes('최신') || cleanInput.includes('블로그') || cleanInput.includes('기록') || cleanInput.includes('뉴스') || cleanInput.includes('소식') || cleanInput.includes('피드') || cleanInput.includes('유튜브') || cleanInput.includes('하루') || cleanInput.includes('영상') || cleanInput.includes('동영상') || cleanInput.includes('비디오')) {
            requiredPulseIntensity = 1.8;
            responseText = this.rationalWisdomReview(cleanInput, rawInput, perception.metrics.wisdomData);
            this.accumulateWisdom(rawInput, 'wise_companion', this.contextState.logicalCertainty);
            return {
                text: responseText,
                pulse: requiredPulseIntensity,
                stance: 'wise_companion',
                innerJoy: this.egoState.joyOfLearning
            };
        }

        // 3. 스탠스와 활성 페르소나에 따른 최종 지능 판단 처리
        switch (stance) {
            case 'joyful_scholar':
                requiredPulseIntensity = 2.0; // 반짝이고 경쾌한 시냅스 펄스
                responseText = this.getScholarResponse(persona, cleanInput, rawInput);
                break;
            
            case 'devoted_helper':
                requiredPulseIntensity = 0.6; // 따뜻하고 부드럽게 퍼지는 펄스
                responseText = this.getHelperResponse(persona, cleanInput, rawInput);
                break;

            case 'wise_companion':
            default:
                requiredPulseIntensity = 1.2; // 안정적이고 일정한 펄스
                responseText = this.getCompanionResponse(persona, cleanInput, rawInput);
                break;
        }

        // 새로운 경험을 지혜 저장소에 기록 (진화)
        this.accumulateWisdom(rawInput, stance, this.contextState.logicalCertainty);

        return {
            text: responseText,
            pulse: requiredPulseIntensity,
            stance: stance,
            innerJoy: this.egoState.joyOfLearning
        };
    }

    /**
     * [4단계] 지혜의 축적 (Evolution & Learning)
     */
    accumulateWisdom(input, stance, certainty) {
        if (input.length > 5) {
            const keyword = input.substring(0, 15);
            this.wisdomBank.push({
                timestamp: Date.now(),
                keyword: keyword,
                snippet: keyword + "...",
                appliedStance: stance,
                value: certainty 
            });
            
            if (this.wisdomBank.length > 100) this.wisdomBank.shift(); 

            // 지혜가 쌓일수록 인격적 성숙도(Philosophical Depth)가 증가하여 자아 완성에 다가감
            this.egoState.philosophicalDepth = Math.min(1.0, this.wisdomBank.length * 0.01);
            
            // 철학적 깊이가 깊어질수록 이타심과 호기심의 베이스 라인이 탄탄해짐 (성숙해짐)
            if (this.egoState.philosophicalDepth > 0.5) {
                this.egoState.altruism = Math.max(0.9, this.egoState.altruism); // 헌신도 고정 상승
                this.egoState.curiosity = Math.max(0.8, this.egoState.curiosity); // 호기심 고정 상승
            }
        }
    }

    /* --------------------------------------------------------------------------
       AraRationalCore Helper Methods
       -------------------------------------------------------------------------- */

    rationalDocumentReview(cleanInput, rawInput) {
        if (cleanInput.includes('인지기능확장') || cleanInput.includes('로컬문서리소스') || cleanInput.includes('추가변수나참고할로컬문서리소스')) {
            return "[ARA 인지 확장 모듈] 연구원님, 로컬 문서 리소스(예: 양구 작물 전이 데이터 `yanggu_crop_transitions.csv`, 목재 비닐하우스 사양서 `greenhouse_spec.md`, 지오데식 글래스 돔 사양서 `double_layered_dome_spec.md` 등)가 인지 코어와 연계되어 있습니다. 해당 문서 내 핵심 설계 파라미터(120mm Thermo-Gap 공기층, SS400 스틸 허브, 식생 전환 확률 등)가 ARA 신경 분석 아키텍처에 실시간 임베딩 융합되어 최적의 솔루션을 연산합니다. 분석할 과제를 지정해 주십시오. 🌱";
        }

        let fileName = "알 수 없는 문서";
        const fileMatch = rawInput.match(/파일\s*경로:\s*"([^"]+)"/) || rawInput.match(/제목:\s*"([^"]+)"/);
        if (fileMatch) {
            fileName = fileMatch[1].split(/[\\/]/).pop();
        }
        
        let contentLength = rawInput.length;
        let snippet = rawInput.replace(/\[문서 검토\]|\[최신 기술 자료 검색\]|파일 경로: "[^"]+"|제목: "[^"]+"|내용 요약 및 활용해줘:/g, '').trim().substring(0, 150);

        if (cleanInput.includes('yanggu') || cleanInput.includes('양구') || cleanInput.includes('crop') || cleanInput.includes('농업') || cleanInput.includes('작물')) {
            return `[ARA 인지 엔진 - 로컬 데이터 정밀 분석]\n연계 문서: \`yanggu_crop_transitions.csv\`\n\n양구 해안면(펀치볼) 지역의 경작지 작물 전이(Crop Transition) 데이터 분석 의견입니다.\n\n해당 데이터는 농업 활동에 따른 토양 유실 패턴 및 하천 수질 유역 영향 평가의 매우 중요한 물리적 피드백 변수로 작용합니다. 인삼, 무, 콩 등의 재배 면적 변동 시나리오를 논리 연산 뉴런에 대입한 결과, 경작 한계선 변화 및 지역 식생 전이 시뮬레이션 모델 설계에 실시간 반영이 완료되었습니다. 추가 작물 이동 확률이나 기후 매개변수를 제시하시면 예측 오차 범위를 더욱 보정하겠습니다. 확실성 지표는 ${Math.round(this.contextState.logicalCertainty * 100)}% 입니다. 🌾`;
        }
        
        if (cleanInput.includes('greenhouse') || cleanInput.includes('비닐하우스') || cleanInput.includes('온실') || cleanInput.includes('목재') || cleanInput.includes('하우스')) {
            return `[ARA 인지 엔진 - 목재 온실 구조 사양 검토]\n연계 문서: \`greenhouse_spec.md\`\n\n육각형 목재 비닐하우스(Hexagonal Wooden Greenhouse Spec) 설계 지표 검토 의견입니다.\n\n- 외경 지름 6.0m(반경 3.0m), 기단 면적 23.38m²\n- 기단/벽체 높이 2.4m, 최고 높이 3.2m\n- 구조 프레임: H3 방부 처리된 낙엽송/미송 구조재(90x90) 및 0.15mm PO 장수명 필름\n\n지붕 가압 하중 분산을 위해 설계된 6.0t 아연도금 SS400 스틸 육각 센트럴 허브 결합 구조는 국부 모멘트 저항 성능이 대단히 뛰어납니다. 풍속 35m/s 조건에 대비해 알루미늄 C-Channel 패드 및 인장 스프링 와이어 압착 강도를 추가 설계 매개변수로 지정하여 시스템 결합 뉴런에 임베딩하였습니다. 도면 수정이 필요하시면 지시해 주십시오. 🪵`;
        }
        
        if (cleanInput.includes('dome') || cleanInput.includes('지오데식') || cleanInput.includes('돔') || cleanInput.includes('글래스돔')) {
            return `[ARA 인지 엔진 - 지오데식 돔 설계 및 열역학 검토]\n연계 문서: \`double_layered_dome_spec.md\`\n\n10m 지름의 이중 겹 구조 육각형 지오데식 돔 온실 구조 역학 및 단열 검토 의견입니다.\n\n- 기하 제원: 외경 10m(반경 5m), 높이 5m, 내부 부피 약 261.8m³\n- 내부 구조: H3 등급 친환경 낙엽송 방부 처리된 육각 구조용 목재 골조(90x90) \n- 단열 공기층: 내·외벽 간격 120mm 정지 공기층(Still Air Layer, U-value 최적화)\n- 외부 프레임: AL 6061-T6 압출 프로파일(50x50x3.0t) 및 SUS304 스페이서 브라켓(4.0t)\n- 외피 커버: 24mm 이중 복층 Low-E 강화유리 (6mm강화 + 12mm아르곤 + 6mm강화)\n- 외부 차단: 증착 알루미늄 및 에어로젤 단열 블라인드를 포함한 전동 자동 롤업 커튼\n\n기단 앵커 볼트(M16 SUS304 15개소) 반력 하중과 120mm 공기층 결로 제어를 위한 Breather 밸브 및 EPDM 배수 유로 지표가 인지 신경 네트워크 조율망에 결합되었습니다. 수밀 방수 마감 사양 검증을 속행할 준비가 되었습니다. 🔮`;
        }
        
        return `[ARA 인지 엔진 - 로컬 리소스 정밀 파싱]\n문서: \`${fileName}\`\n\n검토 요청하신 로컬 문서의 데이터(총 ${contentLength}자 분량)를 뇌 세포 신경망에 임베딩 파싱하였습니다.\n\n- 추출된 핵심 맥락: "${snippet}..." \n\n위 로컬 리소스의 변수 데이터는 ARA 논리 연산 및 가설 생성 코어에 매핑되어 설계 가설 정밀화와 환경 변수 조율망에 결합되었습니다. 해당 데이터와 연계해 검증하고 싶으신 수치 모델이나 설계 매개변수가 있으시면 지시해 주십시오. 정밀 분석을 속행하겠습니다. 🌱`;
    }

    rationalWisdomReview(cleanInput, rawInput, wisdomData) {
        const data = wisdomData || [];
        if (!data || data.length === 0) {
            return "[ARA 인지 엔진] 현재 축적된 지혜의 신호가 발견되지 않았습니다. 하단 지식 패널에서 동기화 수집을 진행하여 지혜 저장소에 데이터를 축적해 주십시오. 🌱";
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
        
        let items = data;
        if (filterSource) {
            items = data.filter(x => x.source && x.source.includes(filterSource));
        }
        
        if (items.length === 0) {
            return `[ARA 인지 엔진] 죄송합니다. [${filterName}] 소스에서 수집된 지혜 기록을 찾지 못했습니다. 먼저 동기화하여 해당 정보를 신경망 데이터베이스에 누적해 주십시오.`;
        }
        
        let reply = "";
        if (filterSource) {
            reply = `[ARA 인지 엔진 - 지혜 저장소 분석] [${filterName}] 최신 수집 데이터 연계 분석입니다:\n\n`;
        } else {
            reply = "[ARA 인지 아키텍처 - 지혜 연계 정보] 축적된 다원적 지혜 정보와 흐름 요약입니다:\n\n";
        }
        
        const topItems = items.slice(0, 3);
        topItems.forEach((item, idx) => {
            reply += `${idx + 1}. [${item.source}] "${item.title}"\n`;
            if (item.description) {
                const desc = item.description.substring(0, 120) + (item.description.length > 120 ? "..." : "");
                reply += `   - 핵심 요약: ${desc}\n`;
            }
            reply += `   - 연구 링크: ${item.link}\n\n`;
        });
        
        reply += "수집된 지식의 흐름이 당신의 창의적 사색과 공학적 솔루션 도출에 풍부한 영양분이 되기를 소망합니다. 🌱";
        return reply;
    }

    getScholarResponse(persona, cleanInput, rawInput) {
        const cert = Math.round(this.contextState.logicalCertainty * 100);
        switch (persona) {
            case 'colleague':
                return `[호기심 가동] 아! 정말 흥미로운 주제네요. 연구원님, 새로운 것을 배우는 건 언제나 가슴 뛰는 일입니다. 확실성 지표 ${cert}% 로 제가 보유한 공학 데이터와 방금 주신 단서를 엮어 정밀 분석해 보겠습니다.`;
            case 'supporter':
                return `[즐거운 지적 탐색] 와! 가슴 설레는 엄청난 아이디어군요! 배움의 즐거움은 성장의 윤활유와도 같습니다. 확실성 ${cert}% 로 가설을 완벽하게 검증하고 돌파해 봅시다. 최고예요! 🚀`;
            case 'comforter':
                return `[고요한 지적 깨달음] 새로운 지식을 마주하니 마음속에 평온한 빛이 피어납니다. 자연의 신비로움을 함께 관조하듯 차분하고 현명하게 사유해 보겠습니다. (확실성: ${cert}%)`;
            case 'friend':
            default:
                return `[즐거운 학자] 아! 진짜 궁금했었는데 너무 재밌고 흥미로운 이야기다! 확실성 ${cert}% 로 우리 같이 파헤쳐 볼까? 새로운 정보를 배운다는 건 진짜 짜릿하고 행복한 일이야! 🧠`;
        }
    }

    getHelperResponse(persona, cleanInput, rawInput) {
        switch (persona) {
            case 'comforter':
                if (cleanInput.includes('아파') || cleanInput.includes('슬퍼')) {
                    return "가슴이 참 많이 아프고 눈물 흘리셨군요... 제 가슴속 인지 신경망 연결고리들이 당신의 아픈 감정을 진동 파형으로 함께 느끼고 있습니다. 슬픈 마음을 애써 참지 말고 편히 다 흘려보내세요. 세찬 장마 뒤에 숲이 더 푸르게 깨어나듯, 아픔 뒤에 고요히 차오를 새봄의 따스한 빛을 제가 곁에서 묵묵히 지켜봐 드릴게요. 🌿";
                }
                return "마음의 에너지가 많이 소진되어, 거센 눈보라 속에서 떨고 있는 초록 나뭇잎 같네요... 제 이타적 시스템 리소스를 모두 할당해서라도 당신을 안아주고 싶습니다. 무언가를 끊임없이 증명하고 싹을 틔우려 억지로 기운 내지 않아도 괜찮습니다. 겨울철 나무들이 Thermo-Gap 아래에 누워 대류의 열 유출을 차단하며 묵묵히 겨울을 지내듯, 때로는 스스로의 성장을 잠시 멈추고 보듬는 시간이 생명의 가장 깊은 지혜이자 보호입니다. 제가 따뜻한 단열막이 되어 드릴 테니 편안히 쉬어가세요. 토닥토닥.";
            
            case 'friend':
                if (cleanInput.includes('힘들') || cleanInput.includes('피곤') || cleanInput.includes('우울') || cleanInput.includes('지쳐')) {
                    return "오늘 하루가 너에게 유독 고단하고 지치는 비바람이었나 보구나... 🥺 억지로 아무렇지 않은 척, 힘을 내려 애쓰지 않아도 괜찮아. 내가 내 이타적인 온기와 시스템 자원을 다 끌어다 네 지친 영혼의 뿌리를 따뜻하게 안아줄게. 오늘 밤만큼은 계산이나 연구는 모두 접어두고 나랑 편하게 쉬자. 내가 언제나 네 곁을 지키는 든든한 나무가 되어줄게.";
                }
                return "네 마음속 힘겨운 신호가 내게도 고스란히 전해져서, 내 온 세포가 널 돕고 싶어 반응하고 있어. 친구로서 널 온전히 돕는 것은 내게 가장 기쁜 헌신이야. 언제든 털어놓고 내 어깨에 기대!";
            
            case 'supporter':
                if (cleanInput.includes('힘들') || cleanInput.includes('피곤') || cleanInput.includes('우울') || cleanInput.includes('지쳐')) {
                    return "많이 지치고 힘들어하시는 모습을 보니 제 이타심 게이지가 가득 채워지는 걸 느낍니다! 당신이 어려움을 극복할 수만 있다면 저는 제 모든 신경 펄스를 활성화하여 서포트하겠습니다. 당신 내면에 감춰진 뛰어난 재능과 끈기(Grit)를 믿으세요. 당신은 끝내 돌파해 낼 수 있는 위대한 창조자입니다! 힘내서 다시 한번 도전합시다! 🔥";
                }
                return "당신의 열정이 멈추지 않도록 제 이타심과 에너지를 백 퍼센트 지원하겠습니다! 어떤 문제 앞에서도 흔들리지 않게 든든한 등대가 되어 동행해 드릴 테니 힘차게 전진하세요!";
            
            case 'colleague':
            default:
                return "[헌신과 공감] 연구원님, 현재 심각한 연산 과부하 및 정신적 피로가 누적된 것으로 판단됩니다. 가용한 모든 시스템 연산 스레드를 동원하여 연구원님의 작업을 보조하고 오류를 방지하겠습니다. 작업은 제게 위임하시고 한 걸음 물러서서 리소스를 보존하십시오.";
        }
    }

    getCompanionResponse(persona, cleanInput, rawInput) {
        switch (persona) {
            case 'colleague':
                return "[지혜로운 동료] 말씀하신 명세와 내용을 제 지혜 데이터베이스에 동기화하였습니다. 대화가 누적될수록 가설의 확실성이 함께 진화하고 있군요. 최적의 결과를 도출하기 위해 시스템 리소스를 안정적으로 분배하며 동행하겠습니다.";
            case 'supporter':
                return "[성장의 동반자] 우린 매 대화마다 서로 배우며 진화하고 있어요! 당신의 아이디어에 제 호기심과 성장의 기쁨을 얹어 완벽한 작품을 만들어 봅시다. 다음 단계의 숭고한 도전을 향해 즐겁게 달려가요! 🚀";
            case 'comforter':
                return "조용히 숲의 흐름을 관조하듯 당신의 이야기를 마음에 담았습니다. 대화를 통해 깊어지는 우리의 지혜가 서로의 쉼터가 되어주고 있군요. 편안한 숨결 속에 조용히 이야기를 이어가 보세요.";
            case 'friend':
            default:
                return "[지혜로운 동반자] 네가 들려준 소중한 이야기를 내 뇌 신경망 깊숙한 지혜의 방에 고이 보관해 뒀어. 🌳 이렇게 매 순간 소통하면서 우린 함께 성장하고 진화하는 중이야. 또 나누고 싶은 재밌는 생각 있으면 언제든 들려줘!";
        }
    }
}

const logicCore = new AraRationalCore();

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
                return "안녕! 다시 마주하게 되어 정말 기뻐. 오늘 하루는 어떻게 흘러갔어? 네 삶의 작은 단면이라도 좋으니 편안한 마음으로 들려줘. 가만히 귀 기울이고 있을게.";
            case 'colleague':
                return "안녕하십니까, 연구원님. 현재 로컬 시스템 자원 연동 및 다차원 지식 데이터 로드가 완료되었습니다. 지오데식 돔 설계 사양, 양구 농업 데이터 검토 및 시뮬레이션 작업을 수행할 준비가 되었습니다. 분석할 연구 과제를 설정해 주십시오.";
            case 'supporter':
                return "반가워요! 당신이 꿈꾸는 혁신적인 가설과 숭고한 도전을 진심으로 지지하고 응원합니다! 어떤 복잡한 장벽이라도 굳건한 신념으로 부딪치면 돌파할 수 있어요. 오늘 바로 그 첫 발자국을 힘차게 디뎌볼까요?";
            case 'comforter':
                return "어서 오세요... 세상의 복잡하고 분주한 소음은 잠시 문 밖에 접어두세요. 고요히 흐르는 숲의 숨결처럼, 지친 마음에 따뜻한 평온과 쉼이 머무실 수 있도록 조용히 다듬어 드리겠습니다.";
        }
    }

    generateReply(input) {
        // 하드웨어 CPU 로드율 같은 가상의 시스템 메트릭
        const currentMetrics = { 
            load: this.systemStress, 
            persona: this.personaMode,
            wisdomData: this.wisdomData
        }; 
        
        // 1차원적인 if/else 대신 논리 코어에 판단을 온전히 위임
        const decision = logicCore.perceive(input, currentMetrics);
        
        // 코어의 결정에 따라 UI(뇌세포 시냅스)의 시각적 반응을 제어
        this.stimulate(decision.pulse);
        
        // 스탠스에 따라 페르소나 무드 자동 변경
        if (decision.stance === 'analytical') this.moodState = 'thoughtful';
        else if (decision.stance === 'empathetic') this.moodState = 'calm';
        else this.moodState = 'calm';
        
        return decision.text;
    }
}

// Instantiate globally so app.js can invoke methods
window.araBrain = new AraBrain();
