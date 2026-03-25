/**
 * SentimentStats Unit Tests
 * 分析統計組件單元測試
 * 
 * 測試覆蓋:
 * - update: 更新統計數據
 * - incrementTotal/Success/Failure: 遞增操作
 * - getStats: 獲取統計數據
 * - getSuccessRate: 計算成功率
 * - reset: 重置狀態
 * - setFromData: 從外部數據初始化
 */

const SentimentStatsTests = (function() {
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
    
    function setupMockDOM() {
        const container = document.createElement('div');
        container.innerHTML = `
            <div class="analysis-stats" id="analysis-stats-container">
                <span class="stat-item" data-stat="total">
                    <i class="fas fa-list-ol"></i> 
                    <span id="stat-total">0</span>
                </span>
                <span class="stat-item success" data-stat="success">
                    <i class="fas fa-check-circle"></i> 
                    <span id="stat-success">0</span>
                </span>
                <span class="stat-item failure" data-stat="failure">
                    <i class="fas fa-exclamation-triangle"></i> 
                    <span id="stat-failure">0</span>
                </span>
            </div>
        `;
        
        document.body.appendChild(container);
    }
    
    function cleanupMockDOM() {
        const container = document.getElementById('analysis-stats-container');
        if (container) {
            container.remove();
        }
    }
    
    function runTests() {
        console.log('='.repeat(50));
        console.log('🧪 SentimentStats Tests');
        console.log('='.repeat(50));
        
        setupMockDOM();
        SentimentStats.init();
        
        testInitialState();
        testUpdate();
        testIncrement();
        testGetStats();
        testSuccessRate();
        testReset();
        testSetFromData();
        
        cleanupMockDOM();
        
        console.log('='.repeat(50));
        console.log(`📊 結果: ${passed} 通過, ${failed} 失敗`);
        console.log('='.repeat(50));
        
        return { passed, failed };
    }
    
    function testInitialState() {
        console.log('\n--- testInitialState ---');
        
        const stats = SentimentStats.getStats();
        assertEqual(stats.total, 0, '初始 total 應為 0');
        assertEqual(stats.success, 0, '初始 success 應為 0');
        assertEqual(stats.failure, 0, '初始 failure 應為 0');
    }
    
    function testUpdate() {
        console.log('\n--- testUpdate ---');
        
        SentimentStats.update({ total: 10, success: 8, failure: 2 });
        
        const stats = SentimentStats.getStats();
        assertEqual(stats.total, 10, 'total 應更新為 10');
        assertEqual(stats.success, 8, 'success 應更新為 8');
        assertEqual(stats.failure, 2, 'failure 應更新為 2');
    }
    
    function testIncrement() {
        console.log('\n--- testIncrement ---');
        
        SentimentStats.reset();
        
        // 測試遞增總數
        SentimentStats.incrementTotal(5);
        let stats = SentimentStats.getStats();
        assertEqual(stats.total, 5, 'incrementTotal(5) 應使 total 為 5');
        
        // 測試遞增成功 (應同時遞增總數)
        SentimentStats.incrementSuccess(3);
        stats = SentimentStats.getStats();
        assertEqual(stats.success, 3, 'success 應為 3');
        assertEqual(stats.total, 8, 'total 應同時遞增為 8');
        
        // 測試遞增失敗 (應同時遞增總數)
        SentimentStats.incrementFailure(2);
        stats = SentimentStats.getStats();
        assertEqual(stats.failure, 2, 'failure 應為 2');
        assertEqual(stats.total, 10, 'total 應同時遞增為 10');
    }
    
    function testGetStats() {
        console.log('\n--- testGetStats ---');
        
        SentimentStats.update({ total: 15, success: 12, failure: 3 });
        
        const stats = SentimentStats.getStats();
        assertEqual(typeof stats, 'object', 'getStats 應返回物件');
        assertEqual(stats.total, 15, '返回的 total 應正確');
        assertEqual(stats.success, 12, '返回的 success 應正確');
        assertEqual(stats.failure, 3, '返回的 failure 應正確');
        
        // 確認返回的是副本而非引用
        stats.total = 999;
        const newStats = SentimentStats.getStats();
        assertEqual(newStats.total, 15, '修改副本不應影響原始數據');
    }
    
    function testSuccessRate() {
        console.log('\n--- testSuccessRate ---');
        
        SentimentStats.reset();
        assertEqual(SentimentStats.getSuccessRate(), 0, '空數據成功率應為 0%');
        
        SentimentStats.update({ total: 10, success: 8, failure: 2 });
        assertEqual(SentimentStats.getSuccessRate(), 80, '8/10 應為 80%');
        
        SentimentStats.update({ total: 3, success: 1, failure: 2 });
        assertEqual(SentimentStats.getSuccessRate(), 33, '1/3 應為 33%');
        
        SentimentStats.update({ total: 100, success: 50, failure: 50 });
        assertEqual(SentimentStats.getSuccessRate(), 50, '50/100 應為 50%');
    }
    
    function testReset() {
        console.log('\n--- testReset ---');
        
        SentimentStats.update({ total: 100, success: 80, failure: 20 });
        SentimentStats.reset();
        
        const stats = SentimentStats.getStats();
        assertEqual(stats.total, 0, '重置後 total 應為 0');
        assertEqual(stats.success, 0, '重置後 success 應為 0');
        assertEqual(stats.failure, 0, '重置後 failure 應為 0');
    }
    
    function testSetFromData() {
        console.log('\n--- testSetFromData ---');
        
        SentimentStats.setFromData({ total: 25, success: 20, failure: 5 });
        
        const stats = SentimentStats.getStats();
        assertEqual(stats.total, 25, 'setFromData 應正確設定 total');
        assertEqual(stats.success, 20, 'setFromData 應正確設定 success');
        assertEqual(stats.failure, 5, 'setFromData 應正確設定 failure');
        
        // 測試空數據
        SentimentStats.setFromData(null);
        let stats2 = SentimentStats.getStats();
        assertEqual(stats2.total, 0, 'null 數據應設為 0');
        
        // 測試部分數據
        SentimentStats.setFromData({ success: 10 });
        stats2 = SentimentStats.getStats();
        assertEqual(stats2.success, 10, '部分數據應只更新提供的欄位');
    }
    
    return {
        runTests
    };
})();

// 自動運行測試
if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(SentimentStatsTests.runTests, 100);
        });
    } else {
        setTimeout(SentimentStatsTests.runTests, 100);
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = SentimentStatsTests;
}
