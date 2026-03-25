/**
 * Intelligence Panel Unit Tests
 * 運行方式: 在瀏覽器控制台執行 或 使用 Node.js + jsdom
 * 
 * 測試覆蓋:
 * - addNewsItem: 新聞項目新增
 * - addNewsBatch: 批量新增
 * - clearNews: 清除新聞
 * - getNewsCount: 取得數量
 * - setMaxItems: 設定最大數量
 */

const TestRunner = (function() {
    'use strict';
    
    let passed = 0;
    let failed = 0;
    let results = [];
    
    function assert(condition, message) {
        if (condition) {
            passed++;
            results.push({ status: 'PASS', message });
            console.log(`✅ PASS: ${message}`);
        } else {
            failed++;
            results.push({ status: 'FAIL', message });
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
    
    function assertTrue(condition, message) {
        assert(condition === true, message);
    }
    
    function assertFalse(condition, message) {
        assert(condition === false, message);
    }
    
    function runTests() {
        console.log('='.repeat(50));
        console.log('🧪 Intelligence Panel Tests');
        console.log('='.repeat(50));
        
        // 建立模擬 DOM
        setupMockDOM();
        
        // 執行測試
        testAddNewsItem();
        testAddNewsBatch();
        testClearNews();
        testGetNewsCount();
        testSetMaxItems();
        
        // 輸出結果
        console.log('='.repeat(50));
        console.log(`📊 結果: ${passed} 通過, ${failed} 失敗`);
        console.log('='.repeat(50));
        
        return { passed, failed, results };
    }
    
    function setupMockDOM() {
        // 建立模擬 DOM 元素
        const mockFeed = document.createElement('div');
        mockFeed.id = 'intelligence-feed';
        mockFeed.innerHTML = '<div class="empty-state"><p>等待偵察數據導入...</p></div>';
        
        const mockCount = document.createElement('span');
        mockCount.id = 'news-count';
        mockCount.textContent = '0 則偵察';
        
        document.body.appendChild(mockFeed);
        document.body.appendChild(mockCount);
        
        // 重新初始化模組
        if (IntelligencePanel && IntelligencePanel.init) {
            IntelligencePanel.init();
        }
    }
    
    function testAddNewsItem() {
        console.log('\n--- testAddNewsItem ---');
        
        // 清空
        IntelligencePanel.clearNews();
        
        // 測試新增單一新聞
        IntelligencePanel.addNewsItem({
            source: 'Anue',
            title: '測試新聞標題',
            date: '2024-01-15',
            url: 'https://example.com'
        });
        
        const count = IntelligencePanel.getNewsCount();
        assertEqual(count, 1, '新增後數量應為 1');
        
        // 測試空狀態被移除
        const emptyState = document.getElementById('intelligence-feed').querySelector('.empty-state');
        assertTrue(emptyState === null, '空狀態應該被移除');
    }
    
    function testAddNewsBatch() {
        console.log('\n--- testAddNewsBatch ---');
        
        // 清空
        IntelligencePanel.clearNews();
        
        // 測試批量新增
        const batchData = [
            { source: 'PTT', title: '新聞 1', date: '2024-01-14' },
            { source: 'Yahoo', title: '新聞 2', date: '2024-01-13' },
            { source: 'Anue', title: '新聞 3', date: '2024-01-12' }
        ];
        
        IntelligencePanel.addNewsBatch(batchData);
        
        const count = IntelligencePanel.getNewsCount();
        assertEqual(count, 3, '批量新增後數量應為 3');
    }
    
    function testClearNews() {
        console.log('\n--- testClearNews ---');
        
        // 先新增一筆
        IntelligencePanel.addNewsItem({
            source: 'Test',
            title: '測試',
            url: 'https://test.com'
        });
        
        // 清除
        IntelligencePanel.clearNews();
        
        const count = IntelligencePanel.getNewsCount();
        assertEqual(count, 0, '清除後數量應為 0');
        
        // 驗證空狀態恢復
        const emptyState = document.getElementById('intelligence-feed').querySelector('.empty-state');
        assertTrue(emptyState !== null, '空狀態應該恢復');
    }
    
    function testGetNewsCount() {
        console.log('\n--- testGetNewsCount ---');
        
        IntelligencePanel.clearNews();
        
        assertEqual(IntelligencePanel.getNewsCount(), 0, '初始數量為 0');
        
        IntelligencePanel.addNewsItem({ source: 'A', title: 'T1' });
        assertEqual(IntelligencePanel.getNewsCount(), 1, '新增後數量為 1');
        
        IntelligencePanel.addNewsItem({ source: 'B', title: 'T2' });
        assertEqual(IntelligencePanel.getNewsCount(), 2, '再新增後數量為 2');
    }
    
    function testSetMaxItems() {
        console.log('\n--- testSetMaxItems ---');
        
        IntelligencePanel.clearNews();
        
        // 設定最大值為 2
        IntelligencePanel.setMaxItems(2);
        
        // 新增 3 筆
        IntelligencePanel.addNewsItem({ source: 'A', title: 'T1' });
        IntelligencePanel.addNewsItem({ source: 'B', title: 'T2' });
        IntelligencePanel.addNewsItem({ source: 'C', title: 'T3' });
        
        const count = IntelligencePanel.getNewsCount();
        assertEqual(count, 2, '超過最大值後應為 2');
    }
    
    return {
        runTests,
        assert,
        assertEqual,
        assertTrue,
        assertFalse
    };
})();

// 自動運行測試 (如果在瀏覽器環境)
if (typeof document !== 'undefined') {
    // 延遲執行確保 DOM 載入
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(TestRunner.runTests, 100);
        });
    } else {
        setTimeout(TestRunner.runTests, 100);
    }
}

// Export for Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TestRunner;
}
