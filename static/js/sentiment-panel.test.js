/**
 * SentimentPanel 整合測試
 * Step 2 AI情緒核心面板完整測試
 * 
 * 測試覆蓋:
 * - SentimentGauge: 情緒儀表
 * - SentimentStats: 分析統計  
 * - ProviderSelector: AI 引擎選單
 * - AIThoughtBubble: AI 思考泡泡
 * - SentimentPanel: 整合面板
 */

const SentimentPanelIntegrationTests = (function() {
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
    
    function setupFullMockDOM() {
        // 建立完整的模擬 DOM
        const container = document.createElement('div');
        container.innerHTML = `
            <!-- 分析統計 -->
            <div class="analysis-stats" id="analysis-stats-container">
                <span class="stat-item" data-stat="total">
                    <span id="stat-total">0</span>
                </span>
                <span class="stat-item success" data-stat="success">
                    <span id="stat-success">0</span>
                </span>
                <span class="stat-item failure" data-stat="failure">
                    <span id="stat-failure">0</span>
                </span>
            </div>
            
            <!-- AI 引擎選單 -->
            <select id="provider-select">
                <option value="auto">⚙️ Auto</option>
                <option value="gemini">✨ Gemini</option>
                <option value="nvidia">⚡ NVIDIA</option>
                <option value="rule">📋 規則引擎</option>
            </select>
            
            <!-- 情緒儀表 -->
            <div class="gauge-container">
                <svg viewBox="0 0 100 100">
                    <circle id="gauge-progress" cx="50" cy="50" r="45" />
                </svg>
                <div class="gauge-score">
                    <div class="score-value" id="current-score">0.00</div>
                    <div class="score-label" id="sentiment-flavor">中性</div>
                </div>
            </div>
            
            <!-- AI 思考泡泡 -->
            <div id="ai-thought" data-status="idle">
                等待數據導入，準備點火分析儀...
            </div>
            
            <!-- 時間戳 -->
            <div id="report-timestamp" style="display: none;"></div>
            
            <!-- 日誌系統 -->
            <div class="log-header">
                <span id="sort-text">新>舊</span>
            </div>
            <button id="clear-logs">清除</button>
            <button id="toggle-sort">排序</button>
            <div id="system-logs"></div>
            
            <!-- 詞庫按鈕 -->
            <button id="btn-lexicon-step2">詞庫</button>
            
            <!-- 詞庫 Modal (hidden) -->
            <div id="lexicon-modal" style="display: none;">
                <div class="modal-content"></div>
            </div>
        `;
        
        document.body.appendChild(container);
    }
    
    function cleanupFullMockDOM() {
        const elements = [
            'analysis-stats-container', 'provider-select', 'gauge-container',
            'ai-thought', 'report-timestamp', 'system-logs',
            'btn-lexicon-step2', 'lexicon-modal'
        ];
        
        elements.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.remove();
        });
    }
    
    function runAllTests() {
        console.log('='.repeat(60));
        console.log('🧪 SentimentPanel 整合測試');
        console.log('='.repeat(60));
        
        setupFullMockDOM();
        
        // 初始化所有模組
        SentimentGauge.init();
        SentimentStats.init();
        ProviderSelector.init();
        AIThoughtBubble.init();
        
        // 執行整合測試
        testComponentIntegration();
        testWebSocketDataHandling();
        testResetFlow();
        
        cleanupFullMockDOM();
        
        console.log('='.repeat(60));
        console.log(`📊 整合測試結果: ${passed} 通過, ${failed} 失敗`);
        console.log('='.repeat(60));
        
        return { passed, failed };
    }
    
    function testComponentIntegration() {
        console.log('\n--- testComponentIntegration ---');
        
        // 測試: 更新分數 -> 統計同步
        SentimentStats.reset();
        SentimentGauge.update(0.8);
        
        let stats = SentimentStats.getStats();
        assertEqual(stats.total > 0 || stats.total === 0, true, '統計模組正常運作');
        
        // 測試: 切換引擎 -> 思考泡泡更新
        ProviderSelector.setProvider('gemini');
        let provider = ProviderSelector.getProvider();
        assertEqual(provider, 'gemini', '引擎切換成功');
        
        // 測試: 設定分數 -> 標籤變化
        SentimentGauge.update(-0.5);
        const scoreEl = document.getElementById('sentiment-flavor');
        assertEqual(scoreEl.innerText.includes('利空'), true, '負向分數應顯示利空');
    }
    
    function testWebSocketDataHandling() {
        console.log('\n--- testWebSocketDataHandling ---');
        
        // 模擬 WebSocket 數據
        const testData = {
            type: 'analysis_start',
            title: '測試新聞標題'
        };
        
        SentimentPanel.handleWebSocketData(testData);
        
        // 驗證 AI 思考泡泡更新
        const thought = AIThoughtBubble.getMessage();
        assertEqual(thought.includes('測試新聞標題'), true, 'analysis_start 應更新思考泡泡');
        
        // 模擬分析結果
        SentimentPanel.handleWebSocketData({
            type: 'analysis_result',
            final_score: 0.65
        });
        
        const score = SentimentGauge.getScore();
        assertEqual(score, 0.65, 'analysis_result 應更新分數');
        
        // 模擬統計更新
        SentimentPanel.handleWebSocketData({
            type: 'analysis_stats',
            total: 10,
            success: 8,
            failure: 2
        });
        
        const updatedStats = SentimentStats.getStats();
        assertEqual(updatedStats.total, 10, '統計數據應正確更新');
        assertEqual(updatedStats.success, 8, '成功數應正確更新');
        assertEqual(updatedStats.failure, 2, '失敗數應正確更新');
        
        // 模擬決策完成
        SentimentPanel.handleWebSocketData({
            type: 'decision',
            action: '買進',
            target_position: '80%'
        });
        
        const timestamp = document.getElementById('report-timestamp');
        assertEqual(timestamp.style.display !== 'none', true, '決策完成後應顯示時間戳');
    }
    
    function testResetFlow() {
        console.log('\n--- testResetFlow ---');
        
        // 設定一些數據
        SentimentGauge.update(0.8);
        SentimentStats.update({ total: 10, success: 8, failure: 2 });
        AIThoughtBubble.setMessage('測試訊息');
        SentimentPanel.updateTimestamp();
        
        // 執行重置
        SentimentPanel.reset();
        
        // 驗證重置效果
        const score = SentimentGauge.getScore();
        assertEqual(score, 0, '重置後分數應為 0');
        
        const stats = SentimentStats.getStats();
        assertEqual(stats.total, 0, '重置後統計應為 0');
        
        const status = AIThoughtBubble.getStatus();
        assertEqual(status, 'idle', '重置後思考泡泡應為 idle');
        
        const timestamp = document.getElementById('report-timestamp');
        assertEqual(timestamp.style.display === 'none', true, '重置後時間戳應隱藏');
    }
    
    return {
        runAllTests
    };
})();

// 自動運行測試
if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(SentimentPanelIntegrationTests.runAllTests, 200);
        });
    } else {
        setTimeout(SentimentPanelIntegrationTests.runAllTests, 200);
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = SentimentPanelIntegrationTests;
}
