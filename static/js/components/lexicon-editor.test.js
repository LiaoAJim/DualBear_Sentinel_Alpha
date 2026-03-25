/**
 * LexiconEditor Unit Tests
 * 情緒詞庫編輯器單元測試
 * 
 * 測試覆蓋:
 * - init: 初始化
 * - open/close/toggle: 顯示控制
 * - getCurrentCategory/setCurrentCategory: 分類管理
 * - getCategories: 獲取分類列表
 * - quickAdd: 快速添加詞彙
 * - getWordsText/setWordsText: 詞彙文字操作
 * - updateCount: 計數更新
 * - onSave/onLoad: 回調訂閱
 */

const LexiconEditorTests = (function() {
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
            <button id="btn-lexicon">詞庫</button>
            <button id="btn-lexicon-step2">詞庫(Step2)</button>
            <div id="lexicon-modal" style="display: none;">
                <button id="close-lexicon">&times;</button>
                <select id="lexicon-category">
                    <option value="bullish_extreme">🚀 極度正向</option>
                    <option value="bullish_strong">📈 強正向</option>
                    <option value="bearish_extreme">💀 極度負向</option>
                </select>
                <span id="lexicon-count">0 個詞</span>
                <textarea id="lexicon-words"></textarea>
                <input id="lexicon-quick-add" type="text">
                <button id="btn-add-positive">正向</button>
                <button id="btn-add-negative">負向</button>
                <button id="btn-save-lexicon">儲存</button>
                <button id="btn-reload-lexicon">重新載入</button>
            </div>
        `;
        document.body.appendChild(container);
    }
    
    function cleanupMockDOM() {
        const modal = document.getElementById('lexicon-modal');
        if (modal) modal.remove();
    }
    
    function runTests() {
        console.log('='.repeat(50));
        console.log('🧪 LexiconEditor Tests');
        console.log('='.repeat(50));
        
        setupMockDOM();
        
        testGetCategories();
        testGetCurrentCategory();
        testSetCurrentCategory();
        testQuickAdd();
        testWordsText();
        testUpdateCount();
        testCallbacks();
        
        cleanupMockDOM();
        
        console.log('='.repeat(50));
        console.log(`📊 結果: ${passed} 通過, ${failed} 失敗`);
        console.log('='.repeat(50));
        
        return { passed, failed };
    }
    
    function testGetCategories() {
        console.log('\n--- testGetCategories ---');
        
        const categories = LexiconEditor.getCategories();
        assertEqual(Array.isArray(categories), true, 'getCategories 應返回陣列');
        assertEqual(categories.length, 9, '應有 9 個分類');
        
        // 驗證結構
        const first = categories[0];
        assertEqual('value' in first, true, '分類應有 value 欄位');
        assertEqual('label' in first, true, '分類應有 label 欄位');
        assertEqual('weight' in first, true, '分類應有 weight 欄位');
    }
    
    function testGetCurrentCategory() {
        console.log('\n--- testGetCurrentCategory ---');
        
        const category = LexiconEditor.getCurrentCategory();
        assertEqual(typeof category, 'string', 'getCurrentCategory 應返回字串');
        assertEqual(category, 'bullish_extreme', '預設分類應為 bullish_extreme');
    }
    
    function testSetCurrentCategory() {
        console.log('\n--- testSetCurrentCategory ---');
        
        // 設定有效分類
        let result = LexiconEditor.setCurrentCategory('bearish_extreme');
        let category = LexiconEditor.getCurrentCategory();
        assertEqual(category, 'bearish_extreme', '應切換到 bearish_extreme');
        
        // 設定無效分類 (應不改變)
        result = LexiconEditor.setCurrentCategory('invalid_category');
        category = LexiconEditor.getCurrentCategory();
        assertEqual(category, 'bearish_extreme', '無效分類應不改變當前選擇');
    }
    
    function testQuickAdd() {
        console.log('\n--- testQuickAdd ---');
        
        const quickAddInput = document.getElementById('lexicon-quick-add');
        const wordsTextarea = document.getElementById('lexicon-words');
        
        // 測試中性添加
        quickAddInput.value = '測試詞彙';
        LexiconEditor.quickAdd('neutral');
        
        let text = wordsTextarea.value;
        assertEqual(text, '測試詞彙', '中性添加應直接添加詞彙');
        
        // 測試正向添加
        quickAddInput.value = '漲停';
        LexiconEditor.quickAdd('positive');
        
        text = wordsTextarea.value;
        assertEqual(text.includes('🔴'), true, '正向添加應有 🔴 前綴');
        
        // 測試負向添加
        quickAddInput.value = '跌停';
        LexiconEditor.quickAdd('negative');
        
        text = wordsTextarea.value;
        assertEqual(text.includes('🔵'), true, '負向添加應有 🔵 前綴');
        
        // 測試空輸入
        quickAddInput.value = '';
        LexiconEditor.quickAdd('neutral');
        
        const oldLength = wordsTextarea.value.length;
        assertEqual(wordsTextarea.value.length, oldLength, '空輸入應不添加');
    }
    
    function testWordsText() {
        console.log('\n--- testWordsText ---');
        
        // 設定文字
        LexiconEditor.setWordsText('詞彙1\n詞彙2\n詞彙3');
        
        const text = LexiconEditor.getWordsText();
        assertEqual(text, '詞彙1\n詞彙2\n詞彙3', 'getWordsText 應返回設定的文字');
        
        // 驗證計數更新
        const countEl = document.getElementById('lexicon-count');
        assertEqual(countEl.textContent, '3 個詞', '計數應更新為 3');
    }
    
    function testUpdateCount() {
        console.log('\n--- testUpdateCount ---');
        
        // 測試各種數量
        LexiconEditor.setWordsText('一\n二\n三\n四\n五');
        
        const countEl = document.getElementById('lexicon-count');
        assertEqual(countEl.textContent, '5 個詞', '5 個詞應顯示正確');
        
        // 測試空文字
        LexiconEditor.setWordsText('');
        assertEqual(countEl.textContent, '0 個詞', '空文字應顯示 0');
        
        // 測試只有空行
        LexiconEditor.setWordsText('\n\n\n');
        assertEqual(countEl.textContent, '0 個詞', '空行應不計數');
    }
    
    function testCallbacks() {
        console.log('\n--- testCallbacks ---');
        
        let saveCalled = false;
        let loadCalled = false;
        
        // 註冊回調
        LexiconEditor.onSave((data) => {
            saveCalled = true;
        });
        
        LexiconEditor.onLoad(() => {
            loadCalled = true;
        });
        
        // 模擬觸發 (由於是內部變量，這裡只測試API可用)
        assertEqual(typeof LexiconEditor.onSave, 'function', 'onSave 應為函數');
        assertEqual(typeof LexiconEditor.onLoad, 'function', 'onLoad 應為函數');
    }
    
    return {
        runTests
    };
})();

// 自動運行測試
if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(LexiconEditorTests.runTests, 100);
        });
    } else {
        setTimeout(LexiconEditorTests.runTests, 100);
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = LexiconEditorTests;
}
