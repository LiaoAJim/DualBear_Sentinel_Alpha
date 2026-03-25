/**
 * DecisionPanel Module
 * Step 3: 哨兵決策判斷 Panel
 */

const DecisionPanel = (function() {
    'use strict';

    let decisionActionEl = null;
    let targetPositionEl = null;
    let decisionNotesEl = null;
    let quantMarginEl = null;
    let quantRetailEl = null;
    let quantVixTwEl = null;
    let quantVixUsEl = null;
    let reportGuidanceEl = null;
    let lineReportPreviewEl = null;
    let decisionLogEl = null;

    const DEFAULTS = {
        action: '--',
        position: '--',
        notes: '系統持續監控市場脈動中...',
        margin: '--',
        retail: '--',
        vixTw: '--',
        vixUs: '--',
        guidance: '本報告較適合用於風險過濾與倉位控制，不適合單獨作為積極進場依據。',
        preview: '--'
    };

    let onPositionChangeCallback = null;
    let currentSentimentScore = null;
    let currentDecision = {
        action: DEFAULTS.action,
        target_position: DEFAULTS.position,
        recon_notes: DEFAULTS.notes,
        failed_sources: []
    };
    let currentQuant = {
        margin_maintenance_ratio: null,
        retail_long_short_ratio: null,
        vixtwn: null,
        vixus: null
    };
    let fixedPreviewText = null;
    let logEntries = [];

    function init() {
        decisionActionEl = document.getElementById('decision-action');
        targetPositionEl = document.getElementById('target-position');
        decisionNotesEl = document.getElementById('decision-notes');
        quantMarginEl = document.getElementById('quant-margin');
        quantRetailEl = document.getElementById('quant-retail');
        quantVixTwEl = document.getElementById('quant-vix-tw');
        quantVixUsEl = document.getElementById('quant-vix-us');
        reportGuidanceEl = document.getElementById('report-guidance');
        lineReportPreviewEl = document.getElementById('line-report-preview');
        decisionLogEl = document.getElementById('decision-log');

        renderGuidance();
        renderLinePreview();
        renderLogs();
        console.log('[DecisionPanel] Initialized');
        return this;
    }

    function renderLogs() {
        if (!decisionLogEl) return;
        if (logEntries.length === 0) {
            decisionLogEl.innerHTML = '<div class="log-entry system">等待 Step 3 量化偵察啟動。</div>';
            return;
        }

        decisionLogEl.innerHTML = logEntries
            .slice(-40)
            .reverse()
            .map((log) => `<div class="log-entry ${log.type}"><span class="log-timestamp">[${log.time}]</span> ${log.message}</div>`)
            .join('');
    }

    function addLog(message, type = 'info') {
        const now = new Date();
        const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
        logEntries.push({ time: timeStr, message, type });
        if (logEntries.length > 80) {
            logEntries = logEntries.slice(-80);
        }
        renderLogs();
    }

    function resetLogs() {
        logEntries = [];
        renderLogs();
    }

    function getIntelligenceCount() {
        if (typeof IntelligencePanel !== 'undefined' && IntelligencePanel.getNewsCount) {
            return IntelligencePanel.getNewsCount();
        }

        const newsCountEl = document.getElementById('news-count');
        if (!newsCountEl) return 0;
        const match = (newsCountEl.textContent || '').match(/(\d+)/);
        return match ? parseInt(match[1], 10) : 0;
    }

    function formatScore(score) {
        if (score === null || score === undefined || score === '') {
            return { text: 'N/A', label: '分析失敗' };
        }
        const numericScore = Number(score);
        if (Number.isNaN(numericScore)) {
            return { text: 'N/A', label: '分析失敗' };
        }
        return {
            text: numericScore.toFixed(2),
            label: numericScore > 0 ? '利多' : numericScore < 0 ? '利空' : '中性'
        };
    }

    function formatMetric(value, suffix = '') {
        if (value === '失敗') return '失敗';
        if (value === null || value === undefined || value === '') return '--';
        return `${value}${suffix}`;
    }

    function renderMetric(el, value, suffix, colorResolver) {
        if (!el) return;
        if (value === '失敗') {
            el.textContent = '失敗';
            el.style.color = 'var(--danger)';
            return;
        }
        if (value === null || value === undefined || value === '') {
            el.textContent = '--';
            el.style.color = '';
            return;
        }

        el.textContent = `${value}${suffix}`;
        const numericValue = parseFloat(value);
        el.style.color = Number.isNaN(numericValue) ? '' : colorResolver(numericValue);
    }

    function getVixColor(vix) {
        if (vix >= 30) return 'var(--accent-pink)';
        if (vix >= 25) return '#f59e0b';
        if (vix < 15) return '#10b981';
        return 'var(--accent-blue)';
    }

    function buildGuidanceText() {
        const action = currentDecision.action || '';
        const failedSources = currentDecision.failed_sources || [];
        const score = currentSentimentScore;
        const scoreNeutral = score === null || score === undefined || Math.abs(Number(score)) < 0.2;
        const numericTw = parseFloat(currentQuant.vixtwn);
        const numericUs = parseFloat(currentQuant.vixus);
        const highVix = (!Number.isNaN(numericTw) && numericTw >= 25) || (!Number.isNaN(numericUs) && numericUs >= 25);

        if (failedSources.length > 0) {
            return '本次資料存在缺口，較適合用於風險提醒，不適合單獨作為選股或槓桿依據。 建議用途：降低風險、排除弱勢、觀察逆勢強股。';
        }
        if (action === '持平' || action === '持平 (已修正)' || (scoreNeutral && highVix)) {
            return '本報告較適合用於風險過濾與倉位控制，不適合單獨作為積極進場依據。 建議用途：降低風險、排除弱勢、觀察逆勢強股。';
        }
        if (action.startsWith('減碼')) {
            return '本報告偏向風險降溫訊號，較適合降低追價與重倉風險，不宜單靠單日敘事進場。 建議用途：降低風險、排除弱勢、觀察逆勢強股。';
        }
        return '本報告可作為觀察強弱與調整倉位的依據，但仍不建議單靠情緒分數進行槓桿交易。 建議用途：降低風險、排除弱勢、觀察逆勢強股。';
    }

    function renderGuidance(customText = null) {
        if (!reportGuidanceEl) return;
        reportGuidanceEl.innerText = customText || buildGuidanceText();
    }

    function renderLinePreview() {
        if (!lineReportPreviewEl) return;
        if (fixedPreviewText !== null) {
            lineReportPreviewEl.textContent = fixedPreviewText;
            return;
        }

        const now = new Date();
        const pad = (value) => String(value).padStart(2, '0');
        const timestamp = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}`;
        const count = getIntelligenceCount();
        const score = formatScore(currentSentimentScore);
        const failedSources = currentDecision.failed_sources || [];
        const failureBlock = failedSources.length > 0 ? `⚠️ 失敗來源: ${failedSources.join('、')}\n` : '';
        const guidanceText = buildGuidanceText();

        lineReportPreviewEl.textContent =
            `📊 DualBear 哨兵正式戰報\n\n` +
            `🕒 時間: ${timestamp}\n` +
            `📡 偵察情報數: ${count} 則\n` +
            `💡 最終情緒: ${score.text} (${score.label})\n\n` +
            `【決策摘要】\n` +
            `🛡️ 建議操作: ${currentDecision.action || DEFAULTS.action}\n` +
            `🎯 建議倉位: ${currentDecision.target_position || DEFAULTS.position}\n\n` +
            `【量化指標】\n` +
            `💳 融資維持率: ${formatMetric(currentQuant.margin_maintenance_ratio, ' %')}\n` +
            `👥 散戶多空比: ${formatMetric(currentQuant.retail_long_short_ratio)}\n` +
            `🇹🇼 台灣 VIX: ${formatMetric(currentQuant.vixtwn)}\n` +
            `🇺🇸 美國 VIX: ${formatMetric(currentQuant.vixus)}\n\n` +
            `【戰略理由】\n` +
            `${currentDecision.recon_notes || DEFAULTS.notes}\n` +
            `${failureBlock}\n` +
            `【使用建議】\n` +
            `${guidanceText}\n\n` +
            `DualBear Sentinel Alpha`;
    }

    function resetToDefaults() {
        currentSentimentScore = null;
        fixedPreviewText = null;
        resetLogs();
        currentDecision = {
            action: DEFAULTS.action,
            target_position: DEFAULTS.position,
            recon_notes: DEFAULTS.notes,
            failed_sources: []
        };
        currentQuant = {
            margin_maintenance_ratio: null,
            retail_long_short_ratio: null,
            vixtwn: null,
            vixus: null
        };

        updateDecision(currentDecision);
        updateQuant(currentQuant);
        renderGuidance(DEFAULTS.guidance);
        renderLinePreview();
        console.log('[DecisionPanel] Reset to defaults');
    }

    function updateDecision(data) {
        if (!data) return;
        if (data.report_text !== undefined) {
            fixedPreviewText = data.report_text || null;
        }

        currentDecision = {
            ...currentDecision,
            ...data,
            failed_sources: Array.isArray(data.failed_sources) ? data.failed_sources : (currentDecision.failed_sources || [])
        };

        if (decisionActionEl && data.action !== undefined) {
            decisionActionEl.innerText = data.action;
            if (data.action === '分析失敗' || data.action === '爬蟲失敗') {
                decisionActionEl.style.color = 'var(--danger)';
            } else {
                decisionActionEl.style.color = '';
            }
        }

        if (targetPositionEl && data.target_position !== undefined) {
            targetPositionEl.innerText = data.target_position;
            if (data.action === '分析失敗' || data.action === '爬蟲失敗') {
                targetPositionEl.style.color = 'var(--text-dim)';
            } else {
                targetPositionEl.style.color = '';
            }
        }

        if (decisionNotesEl && data.recon_notes !== undefined) {
            decisionNotesEl.innerText = data.recon_notes;
        }

        renderGuidance(data.report_guidance);

        if (data.target_position && onPositionChangeCallback) {
            const match = data.target_position.match(/(\d+)%/);
            if (match) {
                onPositionChangeCallback(parseInt(match[1], 10) / 100);
            }
        }

        renderLinePreview();
        console.log('[DecisionPanel] Updated decision:', currentDecision.action, currentDecision.target_position);
    }

    function updateQuant(data) {
        if (!data) return;

        currentQuant = {
            ...currentQuant,
            ...data
        };

        renderMetric(quantMarginEl, data.margin_maintenance_ratio, ' %', (value) => {
            if (value < 140) return 'var(--accent-pink)';
            if (value > 165) return 'var(--accent-purple)';
            return 'var(--accent-blue)';
        });

        renderMetric(quantRetailEl, data.retail_long_short_ratio, '', (value) => {
            if (Math.abs(value) > 30) return 'var(--accent-pink)';
            return 'var(--accent-blue)';
        });

        renderMetric(quantVixTwEl, data.vixtwn, '', getVixColor);
        renderMetric(quantVixUsEl, data.vixus, '', getVixColor);

        renderLinePreview();
        console.log('[DecisionPanel] Updated quant data');
    }

    function handleAnalysisResult(score) {
        currentSentimentScore = score;
        if (fixedPreviewText === null) {
            renderLinePreview();
        }
    }

    function setHistoricalSnapshot(historyData) {
        resetToDefaults();

        const decision = historyData?.decision || {
            action: '沒資料',
            target_position: '沒資料',
            recon_notes: '此歷史檔未保存決策資料。',
            failed_sources: []
        };
        const quant = historyData?.quant_data || {
            margin_maintenance_ratio: '沒資料',
            retail_long_short_ratio: '沒資料',
            vixtwn: '沒資料',
            vixus: '沒資料'
        };

        handleAnalysisResult(historyData?.decision?.sentiment_score ?? null);
        updateDecision({
            ...decision,
            report_guidance: historyData?.report_guidance || '此歷史檔沒有可用的歷史決策資料。',
            report_text: historyData?.report || '沒資料'
        });
        updateQuant(quant);

        renderLinePreview();
    }

    function onPositionChange(callback) {
        onPositionChangeCallback = callback;
    }

    function getState() {
        return {
            action: decisionActionEl?.innerText || '--',
            position: targetPositionEl?.innerText || '--',
            notes: decisionNotesEl?.innerText || DEFAULTS.notes,
            margin: quantMarginEl?.innerText || '--',
            retail: quantRetailEl?.innerText || '--',
            vixTw: quantVixTwEl?.innerText || '--',
            vixUs: quantVixUsEl?.innerText || '--',
            guidance: reportGuidanceEl?.innerText || DEFAULTS.guidance,
            preview: lineReportPreviewEl?.textContent || '--'
        };
    }

    function handleDecisionMessage(data) {
        updateDecision({
            action: data.action,
            target_position: data.target_position,
            recon_notes: data.recon_notes,
            failed_sources: data.failed_sources || [],
            report_guidance: data.report_guidance
        });

        if (data.sentiment_score !== undefined) {
            handleAnalysisResult(data.sentiment_score);
        }
    }

    function handleQuantMessage(data) {
        updateQuant(data);
    }

    return {
        init,
        resetToDefaults,
        updateDecision,
        updateQuant,
        handleAnalysisResult,
        setHistoricalSnapshot,
        onPositionChange,
        getState,
        handleDecisionMessage,
        handleQuantMessage,
        addLog,
        resetLogs,
        DEFAULTS
    };
})();

if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => DecisionPanel.init());
    } else if (document.getElementById('decision-panel')) {
        DecisionPanel.init();
    }
}
