<?php
/**
 * Naver Search Advisor Crawl Request API integration (PHP)
 */

$access_token = "여기에_발급받은_액세스_토큰을_입력하세요";
$target_url = "https://www.your-site.com/new-post";

$api_url = "https://apis.naver.com/searchadvisor/crawl-request/submit.json";

// 헤더 설정 (Bearer 뒤에 띄어쓰기 1칸 필수)
$headers = array(
    "Content-Type: application/json",
    "Authorization: Bearer " . $access_token
);

// 데이터 설정
$data = array(
    "urls" => array(
        array(
            "url" => $target_url,
            "type" => "update" // 수집 요청: update, 삭제 요청: delete
        )
    )
);

// curl 초기화 및 옵션 설정
$ch = curl_init($api_url);
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 10);

// 실행 및 결과 응답 받기
$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);

if (curl_errno($ch)) {
    echo "❌ Curl 에러 발생: " . curl_error($ch) . "\n";
} else {
    if ($http_code == 200) {
        $result = json_decode($response, true);
        echo "✅ 수집 요청 성공!\n";
        print_r($result);
    } else {
        echo "❌ API 에러 발생 (상태 코드: " . $http_code . ")\n";
        echo "에러 상세 내용: " . $response . "\n";
    }
}

curl_close($ch);
?>
