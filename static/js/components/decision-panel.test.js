/**
 * DecisionPanel Unit Tests
 * Step 3 哨兵決策判斷單元測試
 *
 * 測試覆蓋:
 * - init / resetToDefaults
 * - updateDecision
 * - updateQuant
 * - handleDecisionMessage / handleQuantMessage
 * - onPositionChange
 */

const DecisionPanelTests = (function() {
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
        container.id = 'decision-panel-test-container';
        container.innerHTML = `
            <section id="decision-panel">
                <span id="news-count">3 則偵察</span>
                <div id="decision-action">--</div>
                <div id="target-position">--</div>
                <p id="decision-notes">系統持續監控市場脈動中...</p>
                <span id="quant-margin">--</span>
                <span id="quant-retail">--</span>
                <span id="quant-vix-tw">--</span>
                <span id="quant-vix-us">--</span>
                <p id="report-guidance">本報告較適合用於風險過濾與倉位控制，不適合單獨作為積極進場依據。</p>
                <pre id="line-report-preview">--</pre>
            </section>
        `;
        document.body.appendChild(container);
    }

    function cleanupMockDOM() {
        const container = document.getElementById('decision-panel-test-container');
        if (container) container.remove();
    }

    function runTests() {
        console.log('='.repeat(50));
        console.log('🧪 DecisionPanel Tests');
        console.log('='.repeat(50));

        setupMockDOM();
        DecisionPanel.init();

        testResetToDefaults();
        testUpdateDecision();
        testErrorDecisionStyle();
        testPositionChangeCallback();
        testUpdateQuant();
        testLinePreview();
        testHistoricalSnapshot();
        testHandleMessages();

        cleanupMockDOM();

        console.log('='.repeat(50));
        console.log(`📊 結果: ${passed} 通過, ${failed} 失敗`);
        console.log('='.repeat(50));

        return { passed, failed };
    }

    function testResetToDefaults() {
        console.log('\n--- testResetToDefaults ---');

        DecisionPanel.updateDecision({
            action: '續抱',
            target_position: '65%',
            recon_notes: '測試資料'
        });
        DecisionPanel.updateQuant({
            margin_maintenance_ratio: 150,
            retail_long_short_ratio: 20,
            vixtwn: 18,
            vixus: 22
        });

        DecisionPanel.resetToDefaults();

        assertEqual(document.getElementById('decision-action').innerText, '--', '重置後建議操作應為 --');
        assertEqual(document.getElementById('target-position').innerText, '--', '重置後建議倉位應為 --');
        assertEqual(document.getElementById('decision-notes').innerText, '系統持續監控市場脈動中...', '重置後戰略理由應為預設文案');
        assertEqual(document.getElementById('quant-margin').textContent, '--', '重置後融資應為 --');
        assertEqual(document.getElementById('quant-retail').textContent, '--', '重置後散戶應為 --');
        assertEqual(document.getElementById('quant-vix-tw').textContent, '--', '重置後台灣 VIX 應為 --');
        assertEqual(document.getElementById('quant-vix-us').textContent, '--', '重置後美國 VIX 應為 --');
    }

    function testUpdateDecision() {
        console.log('\n--- testUpdateDecision ---');

        DecisionPanel.updateDecision({
            action: '試探佈局',
            target_position: '75%',
            recon_notes: '市場偏向悲觀，可分批進場。',
            report_guidance: '本報告可作為觀察強弱與調整倉位的依據。'
        });

        assertEqual(document.getElementById('decision-action').innerText, '試探佈局', '應更新建議操作');
        assertEqual(document.getElementById('target-position').innerText, '75%', '應更新建議倉位');
        assertEqual(document.getElementById('decision-notes').innerText, '市場偏向悲觀，可分批進場。', '應更新戰略理由');
        assertEqual(document.getElementById('report-guidance').innerText, '本報告可作為觀察強弱與調整倉位的依據。', '應更新使用建議');
    }

    function testErrorDecisionStyle() {
        console.log('\n--- testErrorDecisionStyle ---');

        DecisionPanel.updateDecision({
            action: '分析失敗',
            target_position: '--',
            recon_notes: 'API 暫時不可用'
        });

        assertEqual(document.getElementById('decision-action').style.color, 'var(--danger)', '分析失敗時操作文字應套用 danger 顏色');
        assertEqual(document.getElementById('target-position').style.color, 'var(--text-dim)', '分析失敗時倉位文字應轉淡');
    }

    function testPositionChangeCallback() {
        console.log('\n--- testPositionChangeCallback ---');

        let callbackValue = null;
        DecisionPanel.onPositionChange((value) => {
            callbackValue = value;
        });

        DecisionPanel.updateDecision({
            action: '續抱',
            target_position: '65%',
            recon_notes: '回呼測試'
        });

        assertEqual(callbackValue, 0.65, '倉位更新時應回呼 0-1 百分比');
    }

    function testUpdateQuant() {
        console.log('\n--- testUpdateQuant ---');

        DecisionPanel.updateQuant({
            margin_maintenance_ratio: 136,
            retail_long_short_ratio: 40,
            vixtwn: 28,
            vixus: 31
        });

        assertEqual(document.getElementById('quant-margin').textContent, '136 %', '應更新融資數值');
        assertEqual(document.getElementById('quant-retail').textContent, '40', '應更新散戶數值');
        assertEqual(document.getElementById('quant-vix-tw').textContent, '28', '應更新台灣 VIX 數值');
        assertEqual(document.getElementById('quant-vix-us').textContent, '31', '應更新美國 VIX 數值');
        assertEqual(document.getElementById('quant-margin').style.color, 'var(--accent-pink)', '低融資維持率應轉粉色');
        assertEqual(document.getElementById('quant-retail').style.color, 'var(--accent-pink)', '過熱散戶比應轉粉色');
        assertEqual(document.getElementById('quant-vix-tw').style.color, '#f59e0b', '高台灣 VIX 應轉橘色');
        assertEqual(document.getElementById('quant-vix-us').style.color, 'var(--accent-pink)', '極高美國 VIX 應轉粉色');
    }

    function testLinePreview() {
        console.log('\n--- testLinePreview ---');

        DecisionPanel.handleAnalysisResult(-0.24);
        DecisionPanel.updateDecision({
            action: '爬蟲失敗',
            target_position: '失敗',
            recon_notes: '量化資料不完整，停止出手。',
            failed_sources: ['情報來源:ptt', '美國VIX']
        });
        DecisionPanel.updateQuant({
            margin_maintenance_ratio: '失敗',
            retail_long_short_ratio: 5.13,
            vixtwn: 21.5,
            vixus: '失敗'
        });

        const preview = document.getElementById('line-report-preview').textContent;
        assertTrue(preview.includes('建議倉位: 失敗'), 'LINE 預覽應包含建議倉位');
        assertTrue(preview.includes('融資維持率: 失敗'), 'LINE 預覽應包含融資狀態');
        assertTrue(preview.includes('散戶多空比: 5.13'), 'LINE 預覽應包含散戶數值');
        assertTrue(preview.includes('台灣 VIX: 21.5'), 'LINE 預覽應包含台灣 VIX');
        assertTrue(preview.includes('美國 VIX: 失敗'), 'LINE 預覽應包含美國 VIX 失敗');
        assertTrue(preview.includes('失敗來源: 情報來源:ptt、美國VIX'), 'LINE 預覽應列出失敗來源');
    }

    function testHistoricalSnapshot() {
        console.log('\n--- testHistoricalSnapshot ---');

        DecisionPanel.setHistoricalSnapshot({
            decision: {
                action: '持平',
                target_position: '50%',
                recon_notes: '歷史決策理由',
                sentiment_score: null,
                failed_sources: []
            },
            quant_data: {
                margin_maintenance_ratio: '沒資料',
                retail_long_short_ratio: 2.1,
                vixtwn: '沒資料',
                vixus: 24.8
            },
            report_guidance: '此為歷史快照的使用建議。',
            report: '這是歷史報告全文'
        });

        assertEqual(document.getElementById('decision-action').innerText, '持平', '歷史快照應更新操作');
        assertEqual(document.getElementById('target-position').innerText, '50%', '歷史快照應更新倉位');
        assertEqual(document.getElementById('decision-notes').innerText, '歷史決策理由', '歷史快照應更新理由');
        assertEqual(document.getElementById('quant-margin').textContent, '沒資料 %', '歷史快照應更新融資');
        assertEqual(document.getElementById('quant-vix-us').textContent, '24.8', '歷史快照應更新美國 VIX');
        assertEqual(document.getElementById('report-guidance').innerText, '此為歷史快照的使用建議。', '歷史快照應更新使用建議');
        assertEqual(document.getElementById('line-report-preview').textContent, '這是歷史報告全文', '歷史快照應使用歷史報告全文');
    }

    function testHandleMessages() {
        console.log('\n--- testHandleMessages ---');

        DecisionPanel.handleDecisionMessage({
            action: '強勢介入',
            target_position: '95%',
            recon_notes: '極度恐慌訊號出現',
            quant_adjustment: 10,
            failed_sources: []
        });
        DecisionPanel.handleAnalysisResult(0.52);
        DecisionPanel.handleQuantMessage({
            margin_maintenance_ratio: null,
            retail_long_short_ratio: '',
            vixtwn: null,
            vixus: null
        });

        assertEqual(document.getElementById('decision-action').innerText, '強勢介入', 'handleDecisionMessage 應更新操作');
        assertEqual(document.getElementById('target-position').innerText, '95%', 'handleDecisionMessage 應更新倉位');
        assertEqual(document.getElementById('quant-margin').textContent, '--', 'handleQuantMessage 應可重置空值欄位');
        assertEqual(document.getElementById('quant-retail').textContent, '--', 'handleQuantMessage 應可重置散戶欄位');
        assertEqual(document.getElementById('quant-vix-tw').textContent, '--', 'handleQuantMessage 應可重置台灣 VIX 欄位');
        assertEqual(document.getElementById('quant-vix-us').textContent, '--', 'handleQuantMessage 應可重置美國 VIX 欄位');
    }

    return {
        runTests
    };
})();

if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(DecisionPanelTests.runTests, 100);
        });
    } else {
        setTimeout(DecisionPanelTests.runTests, 100);
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = DecisionPanelTests;
}
