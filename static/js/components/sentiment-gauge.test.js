/**
 * SentimentGauge Unit Tests
 * 情緒儀表組件單元測試
 * 
 * 測試覆蓋:
 * - update: 分數更新
 * - getScore: 獲取當前分數
 * - reset: 重置狀態
 * - getScoreLabel: 分數標籤計算
 */

const SentimentGaugeTests = (function() {
    'use strict';
    
    let passed = 0;
    let failed = 0;
    
    function assert(condition, message) {
        if (condition) {
            passed++;
            console.log(`✅ PASS: ${message}`);
        } else {
            failed++;
            console.error(`❌ FAIL: ${message}`);
        }
    }
    
    function assertEqual(actual, expected, message) {
        const condition = actual === expected;
        if (!condition) {
            console.error(`   Expected: ${expected}, Got: ${actual}`);
        }
        assert(condition, message);
    }
    
    function assertClose(actual, expected, tolerance, message) {
        const condition = Math.abs(actual - expected) <= tolerance;
        if (!condition) {
            console.error(`   Expected: ${expected} (±${tolerance}), Got: ${actual}`);
        }
        assert(condition, message);
    }
    
    function setupMockDOM() {
        // 建立模擬 DOM 結構
        const container = document.createElement('div');
        container.innerHTML = `
            <div class="gauge-container">
                <svg viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="6"/>
                    <circle id="gauge-progress" cx="50" cy="50" r="45" fill="none" 
                            stroke="url(#gauge-gradient)" stroke-width="6" 
                            stroke-dasharray="282.7" stroke-dashoffset="282.7"
                            transform="rotate(-90 50 50)"/>
                </svg>
                <div class="gauge-score">
                    <div class="score-value" id="current-score">0.00</div>
                    <div class="score-label" id="sentiment-flavor">中性</div>
                </div>
            </div>
        `;
        
        document.body.appendChild(container);
    }
    
    function cleanupMockDOM() {
        const container = document.querySelector('.gauge-container');
        if (container) {
            container.remove();
        }
    }
    
    function runTests() {
        console.log('='.repeat(50));
        console.log('🧪 SentimentGauge Tests');
        console.log('='.repeat(50));
        
        setupMockDOM();
        
        // 重新初始化模組
        SentimentGauge.init();
        
        testUpdateScore();
        testGetScore();
        testScoreLabel();
        testReset();
        testNullScore();
        
        cleanupMockDOM();
        
        console.log('='.repeat(50));
        console.log(`📊 結果: ${passed} 通過, ${failed} 失敗`);
        console.log('='.repeat(50));
        
        return { passed, failed };
    }
    
    function testUpdateScore() {
        console.log('\n--- testUpdateScore ---');
        
        // 測試高分 (> 0.5)
        SentimentGauge.update(0.8);
        let scoreText = document.getElementById('current-score').innerText;
        assertEqual(scoreText, '0.80', '高分數應顯示正確的小數位');
        
        // 測試中等正向 (0.2 - 0.5)
        SentimentGauge.update(0.3);
        scoreText = document.getElementById('current-score').innerText;
        assertEqual(scoreText, '0.30', '中等分數應顯示正確');
        
        // 測試中性 (-0.2 - 0.2)
        SentimentGauge.update(0);
        scoreText = document.getElementById('current-score').innerText;
        assertEqual(scoreText, '0.00', '中性分數應為 0.00');
        
        // 測試負向
        SentimentGauge.update(-0.5);
        scoreText = document.getElementById('current-score').innerText;
        assertEqual(scoreText, '-0.50', '負向分數應顯示負值');
    }
    
    function testGetScore() {
        console.log('\n--- testGetScore ---');
        
        SentimentGauge.update(0.75);
        let score = SentimentGauge.getScore();
        assertEqual(score, 0.75, 'getScore 應返回當前分數');
        
        SentimentGauge.update(-0.25);
        score = SentimentGauge.getScore();
        assertEqual(score, -0.25, '負向分數應正確返回');
    }
    
    function testScoreLabel() {
        console.log('\n--- testScoreLabel ---');
        
        // 測試各種分數的標籤
        SentimentGauge.update(0.8);
        let label = document.getElementById('sentiment-flavor').innerText;
        assertEqual(label, '極度樂觀', '> 0.5 應為極度樂觀');
        
        SentimentGauge.update(0.3);
        label = document.getElementById('sentiment-flavor').innerText;
        assertEqual(label, '偏向利多', '0.2-0.5 應為偏向利多');
        
        SentimentGauge.update(0);
        label = document.getElementById('sentiment-flavor').innerText;
        assertEqual(label, '市場中性', '-0.2-0.2 應為市場中性');
        
        SentimentGauge.update(-0.3);
        label = document.getElementById('sentiment-flavor').innerText;
        assertEqual(label, '偏向利空', '-0.5--0.2 應為偏向利空');
        
        SentimentGauge.update(-0.8);
        label = document.getElementById('sentiment-flavor').innerText;
        assertEqual(label, '極度悲觀', '< -0.5 應為極度悲觀');
    }
    
    function testReset() {
        console.log('\n--- testReset ---');
        
        SentimentGauge.update(0.8);
        SentimentGauge.reset();
        
        let scoreText = document.getElementById('current-score').innerText;
        assertEqual(scoreText, '--', '重置後分數應為 --');
        
        let label = document.getElementById('sentiment-flavor').innerText;
        assertEqual(label, '等待分析', '重置後標籤應為等待分析');
    }
    
    function testNullScore() {
        console.log('\n--- testNullScore ---');
        
        SentimentGauge.update(null);
        
        let scoreText = document.getElementById('current-score').innerText;
        assertEqual(scoreText, 'N/A', 'null 分數應顯示 N/A');
        
        let label = document.getElementById('sentiment-flavor').innerText;
        assertEqual(label, '分析失敗', 'null 分數應顯示分析失敗');
        
        let score = SentimentGauge.getScore();
        assertEqual(score, null, 'getScore 應返回 null');
    }
    
    return {
        runTests
    };
})();

// 自動運行測試
if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            // 等待 SentimentGauge 載入
            setTimeout(SentimentGaugeTests.runTests, 100);
        });
    } else {
        setTimeout(SentimentGaugeTests.runTests, 100);
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = SentimentGaugeTests;
}
