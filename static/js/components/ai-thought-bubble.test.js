/**
 * AIThoughtBubble Unit Tests
 * AI 思考泡泡組件單元測試
 * 
 * 測試覆蓋:
 * - setMessage: 設定訊息
 * - setStatus: 設定狀態
 * - showAnalyzing: 顯示分析中
 * - showSuccess: 顯示成功
 * - showError: 顯示錯誤
 * - reset: 重置狀態
 * - getStatus/getMessage: 獲取狀態
 */

const AIThoughtBubbleTests = (function() {
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
            <div id="ai-thought" data-status="idle">
                等待數據導入，準備點火分析儀...
            </div>
        `;
        
        document.body.appendChild(container);
    }
    
    function cleanupMockDOM() {
        const bubble = document.getElementById('ai-thought');
        if (bubble) bubble.remove();
    }
    
    function runTests() {
        console.log('='.repeat(50));
        console.log('🧪 AIThoughtBubble Tests');
        console.log('='.repeat(50));
        
        setupMockDOM();
        AIThoughtBubble.init();
        
        testInitialState();
        testSetMessage();
        testSetStatus();
        testShowAnalyzing();
        testShowSuccess();
        testShowError();
        testReset();
        testGetStatus();
        testGetMessage();
        testStatusConstant();
        
        cleanupMockDOM();
        
        console.log('='.repeat(50));
        console.log(`📊 結果: ${passed} 通過, ${failed} 失敗`);
        console.log('='.repeat(50));
        
        return { passed, failed };
    }
    
    function testInitialState() {
        console.log('\n--- testInitialState ---');
        
        const status = AIThoughtBubble.getStatus();
        assertEqual(status, 'idle', '初始狀態應為 idle');
        
        const message = AIThoughtBubble.getMessage();
        assertEqual(message.includes('等待數據導入'), true, '初始訊息應包含等待導入');
    }
    
    function testSetMessage() {
        console.log('\n--- testSetMessage ---');
        
        AIThoughtBubble.setMessage('測試訊息');
        
        const message = AIThoughtBubble.getMessage();
        assertEqual(message, '測試訊息', '應設定自定義訊息');
        
        const bubble = document.getElementById('ai-thought');
        assertEqual(bubble.innerText, '測試訊息', 'DOM 應同步更新');
    }
    
    function testSetStatus() {
        console.log('\n--- testSetStatus ---');
        
        AIThoughtBubble.setStatus('analyzing');
        
        const status = AIThoughtBubble.getStatus();
        assertEqual(status, 'analyzing', '狀態應設為 analyzing');
        
        const bubble = document.getElementById('ai-thought');
        assertEqual(bubble.getAttribute('data-status'), 'analyzing', 'data-status 屬性應同步');
        
        AIThoughtBubble.setStatus('success');
        assertEqual(AIThoughtBubble.getStatus(), 'success', '應切換到 success');
        
        AIThoughtBubble.setStatus('error');
        assertEqual(AIThoughtBubble.getStatus(), 'error', '應切換到 error');
    }
    
    function testShowAnalyzing() {
        console.log('\n--- testShowAnalyzing ---');
        
        AIThoughtBubble.showAnalyzing('測試新聞標題');
        
        const message = AIThoughtBubble.getMessage();
        assertEqual(message.includes('測試新聞標題'), true, '訊息應包含標題');
        assertEqual(message.includes('正在解析'), true, '訊息應包含正在解析');
        
        const status = AIThoughtBubble.getStatus();
        assertEqual(status, 'analyzing', '狀態應為 analyzing');
        
        // 測試無標題
        AIThoughtBubble.showAnalyzing();
        const msg2 = AIThoughtBubble.getMessage();
        assertEqual(msg2.includes('正在解析'), true, '無標題時應顯示預設訊息');
    }
    
    function testShowSuccess() {
        console.log('\n--- testShowSuccess ---');
        
        AIThoughtBubble.showSuccess();
        
        const status = AIThoughtBubble.getStatus();
        assertEqual(status, 'success', '狀態應為 success');
        
        const message = AIThoughtBubble.getMessage();
        assertEqual(message.includes('完成'), true, '成功訊息應包含完成');
        
        // 測試自定義訊息
        AIThoughtBubble.showSuccess('自定義成功訊息');
        assertEqual(AIThoughtBubble.getMessage(), '自定義成功訊息', '應顯示自定義訊息');
    }
    
    function testShowError() {
        console.log('\n--- testShowError ---');
        
        AIThoughtBubble.showError('網路連線失敗');
        
        const status = AIThoughtBubble.getStatus();
        assertEqual(status, 'error', '狀態應為 error');
        
        const message = AIThoughtBubble.getMessage();
        assertEqual(message.includes('網路連線失敗'), true, '錯誤訊息應包含錯誤內容');
        
        // 測試空錯誤
        AIThoughtBubble.showError();
        const msg2 = AIThoughtBubble.getMessage();
        assertEqual(msg2.includes('錯誤'), true, '空錯誤應顯示預設訊息');
    }
    
    function testReset() {
        console.log('\n--- testReset ---');
        
        AIThoughtBubble.setMessage('測試');
        AIThoughtBubble.setStatus('error');
        
        AIThoughtBubble.reset();
        
        const status = AIThoughtBubble.getStatus();
        assertEqual(status, 'idle', '重置後狀態應為 idle');
        
        const message = AIThoughtBubble.getMessage();
        assertEqual(message.includes('等待數據導入'), true, '重置後訊息應為預設');
    }
    
    function testGetStatus() {
        console.log('\n--- testGetStatus ---');
        
        let status = AIThoughtBubble.getStatus();
        assertEqual(typeof status, 'string', 'getStatus 應返回字串');
        
        AIThoughtBubble.setStatus('success');
        status = AIThoughtBubble.getStatus();
        assertEqual(status, 'success', '應返回當前狀態');
    }
    
    function testGetMessage() {
        console.log('\n--- testGetMessage ---');
        
        AIThoughtBubble.setMessage('測試訊息內容');
        const message = AIThoughtBubble.getMessage();
        
        assertEqual(typeof message, 'string', 'getMessage 應返回字串');
        assertEqual(message, '測試訊息內容', '應返回設定的訊息');
    }
    
    function testStatusConstant() {
        console.log('\n--- testStatusConstant ---');
        
        const STATUS = AIThoughtBubble.STATUS;
        
        assertEqual(STATUS.IDLE, 'idle', '應有 IDLE 狀態');
        assertEqual(STATUS.ANALYZING, 'analyzing', '應有 ANALYZING 狀態');
        assertEqual(STATUS.SUCCESS, 'success', '應有 SUCCESS 狀態');
        assertEqual(STATUS.ERROR, 'error', '應有 ERROR 狀態');
    }
    
    return {
        runTests
    };
})();

// 自動運行測試
if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(AIThoughtBubbleTests.runTests, 100);
        });
    } else {
        setTimeout(AIThoughtBubbleTests.runTests, 100);
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = AIThoughtBubbleTests;
}
