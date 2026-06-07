package com.ara.platform.parser.util;

public class SimHashUtil {
    public static boolean isDuplicate(String text1, String text2) {
        if (text1 == null || text2 == null) return false;
        
        // 간단한 유사도 검사 (실제 환경에서는 SimHash/MinHash 알고리즘 사용)
        int minLength = Math.min(text1.length(), text2.length());
        if (minLength == 0) return false;
        
        int matchCount = 0;
        for (int i = 0; i < minLength; i++) {
            if (text1.charAt(i) == text2.charAt(i)) {
                matchCount++;
            }
        }
        
        double similarity = (double) matchCount / Math.max(text1.length(), text2.length());
        return similarity > 0.9; // 90% 이상 유사하면 중복으로 판단
    }
}
