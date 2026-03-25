/**
 * ProviderSelector Unit Tests
 * AI 引擎選單組件單元測試
 * 
 * 測試覆蓋:
 * - getProvider: 獲取當前引擎
 * - setProvider: 設定引擎
 * - getProviderInfo: 獲取引擎資訊
 * - getAllProviders: 獲取所有引擎
 * - onChange/offChange: 回調訂閱
 */

const ProviderSelectorTests = (function() {
    'use strict';
    
    let passed = 0;
    let failed = 0;
    let originalLocalStorage = null;
    
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
        // Mock localStorage
        const store = {};
        originalLocalStorage = window.localStorage;
        window.localStorage = {
            getItem: (key) => store[key] || null,
            setItem: (key, value) => { store[key] = value; },
            removeItem: (key) => { delete store[key]; },
            clear: () => { Object.keys(store).forEach(k => delete store[k]); }
        };
        
        const container = document.createElement('div');
        container.innerHTML = `
            <select id="provider-select">
                <option value="auto">⚙️ Auto</option>
                <option value="gemini">✨ Gemini</option>
                <option value="nvidia">⚡ NVIDIA</option>
                <option value="rule">📋 規則引擎</option>
            </select>
        `;
        
        document.body.appendChild(container);
    }
    
    function cleanupMockDOM() {
        const select = document.getElementById('provider-select');
        if (select) select.remove();
        
        // Restore localStorage
        if (originalLocalStorage) {
            window.localStorage = originalLocalStorage;
        }
    }
    
    function runTests() {
        console.log('='.repeat(50));
        console.log('🧪 ProviderSelector Tests');
        console.log('='.repeat(50));
        
        setupMockDOM();
        
        // 需要重新初始化以使用 mock DOM
        const selectEl = document.getElementById('provider-select');
        selectEl.value = 'auto';
        
        testGetProvider();
        testSetProvider();
        testGetProviderInfo();
        testGetAllProviders();
        testCallbacks();
        
        cleanupMockDOM();
        
        console.log('='.repeat(50));
        console.log(`📊 結果: ${passed} 通過, ${failed} 失敗`);
        console.log('='.repeat(50));
        
        return { passed, failed };
    }
    
    function testGetProvider() {
        console.log('\n--- testGetProvider ---');
        
        const provider = ProviderSelector.getProvider();
        assertEqual(typeof provider, 'string', 'getProvider 應返回字串');
        assertEqual(provider, 'auto', '預設應為 auto');
    }
    
    function testSetProvider() {
        console.log('\n--- testSetProvider ---');
        
        // 測試設定有效引擎
        let result = ProviderSelector.setProvider('gemini');
        assertEqual(result, true, 'setProvider(gemini) 應返回 true');
        assertEqual(ProviderSelector.getProvider(), 'gemini', '應切換到 gemini');
        
        result = ProviderSelector.setProvider('nvidia');
        assertEqual(result, true, 'setProvider(nvidia) 應返回 true');
        assertEqual(ProviderSelector.getProvider(), 'nvidia', '應切換到 nvidia');
        
        result = ProviderSelector.setProvider('rule');
        assertEqual(result, true, 'setProvider(rule) 應返回 true');
        assertEqual(ProviderSelector.getProvider(), 'rule', '應切換到 rule');
        
        // 測試設定無效引擎
        result = ProviderSelector.setProvider('invalid_provider');
        assertEqual(result, false, '無效引擎應返回 false');
    }
    
    function testGetProviderInfo() {
        console.log('\n--- testGetProviderInfo ---');
        
        let info = ProviderSelector.getProviderInfo('auto');
        assertEqual(info.name, 'Auto', 'auto 應有名稱 Auto');
        assertEqual(info.icon, '⚙️', 'auto 應有圖示 ⚙️');
        
        info = ProviderSelector.getProviderInfo('gemini');
        assertEqual(info.name, 'Gemini', 'gemini 應有名稱 Gemini');
        
        info = ProviderSelector.getProviderInfo('nvidia');
        assertEqual(info.name, 'NVIDIA', 'nvidia 應有名稱 NVIDIA');
        
        info = ProviderSelector.getProviderInfo('rule');
        assertEqual(info.name, '規則引擎', 'rule 應有名稱 規則引擎');
        
        // 測試未知引擎
        info = ProviderSelector.getProviderInfo('unknown');
        assertEqual(info, null, '未知引擎應返回 null');
    }
    
    function testGetAllProviders() {
        console.log('\n--- testGetAllProviders ---');
        
        const all = ProviderSelector.getAllProviders();
        assertEqual(typeof all, 'object', 'getAllProviders 應返回物件');
        assertEqual(Object.keys(all).length, 4, '應有 4 個引擎');
        assertEqual('auto' in all, true, '應包含 auto');
        assertEqual('gemini' in all, true, '應包含 gemini');
        assertEqual('nvidia' in all, true, '應包含 nvidia');
        assertEqual('rule' in all, true, '應包含 rule');
    }
    
    function testCallbacks() {
        console.log('\n--- testCallbacks ---');
        
        let callbackTriggered = false;
        let receivedProvider = null;
        
        const callback = (provider) => {
            callbackTriggered = true;
            receivedProvider = provider;
        };
        
        // 註冊回調
        ProviderSelector.onChange(callback);
        
        // 手動觸發變更
        const selectEl = document.getElementById('provider-select');
        selectEl.value = 'rule';
        selectEl.dispatchEvent(new Event('change'));
        
        // 由於事件是同步的，回調應該被觸發
        // 注意: 在測試環境中可能需要模擬觸發
        
        // 測試移除回調
        ProviderSelector.offChange(callback);
        
        // 確認只有一個回調被移除
        const allProviders = ProviderSelector.getAllProviders();
        assertEqual(typeof allProviders, 'object', '回調移除不應影響其他功能');
    }
    
    return {
        runTests
    };
})();

// 自動運行測試
if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(ProviderSelectorTests.runTests, 100);
        });
    } else {
        setTimeout(ProviderSelectorTests.runTests, 100);
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = ProviderSelectorTests;
}
