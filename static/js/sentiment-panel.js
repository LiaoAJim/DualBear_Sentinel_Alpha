/**
 * Step 2: AI情緒核心面板模組 (Sentiment Panel Module)
 * 整合所有情緒相關子組件的統一管理模組
 * 
 * @module SentimentPanel
 * @version 1.0.0
 * 
 * 子模組:
 * - SentimentGauge: 情緒儀表
 * - SentimentStats: 分析統計
 * - ProviderSelector: AI 引擎選單
 * - AIThoughtBubble: AI 思考泡泡
 */

const SentimentPanel = (function() {
    'use strict';
    
    // 日誌相關
    let allLogs = [];
    let sortDesc = true;
    let systemLogs = null;
    let clearLogsBtn = null;
    let toggleSortBtn = null;
    let sortText = null;
    
    /**
     * 初始化面板模組
     */
    function init() {
        console.log('[SentimentPanel] 初始化中...');
        
        // 初始化子組件
        initComponents();
        
        // 初始化日誌系統
        initLogSystem();
        
        // 綁定詞庫按鈕事件
        initLexiconButton();
        
        console.log('[SentimentPanel] 初始化完成');
    }
    
    /**
     * 初始化子組件
     */
    function initComponents() {
        // 各子組件會自動初始化
        // 這裡可以進行額外的整合配置
        
        // 監聽 provider 變更，同步到其他組件
        if (typeof ProviderSelector !== 'undefined') {
            ProviderSelector.onChange((provider) => {
                console.log('[SentimentPanel] AI 引擎變更:', provider);
            });
        }
    }
    
    /**
     * 初始化日誌系統
     */
    function initLogSystem() {
        systemLogs = document.getElementById('system-logs');
        clearLogsBtn = document.getElementById('clear-logs');
        toggleSortBtn = document.getElementById('toggle-sort');
        sortText = document.getElementById('sort-text');
        
        if (clearLogsBtn) {
            clearLogsBtn.addEventListener('click', clearLogs);
        }
        
        if (toggleSortBtn) {
            toggleSortBtn.addEventListener('click', toggleSort);
        }
        
        // 初始渲染
        renderLogs();
    }
    
    /**
     * 初始化詞庫按鈕
     */
    function initLexiconButton() {
        const lexiconBtn = document.getElementById('btn-lexicon-step2');
        if (lexiconBtn) {
            lexiconBtn.addEventListener('click', () => {
                const lexiconModal = document.getElementById('lexicon-modal');
                if (lexiconModal) {
                    lexiconModal.style.display = 'flex';
                    lexiconModal.classList.add('show');
                }
            });
        }
    }
    
    /**
     * 新增日誌
     * @param {string} message - 日誌訊息
     * @param {string} type - 日誌類型 (info, success, warning, error, system, scout, ai)
     */
    function addLog(message, type = 'info') {
        if (!systemLogs) return;
        
        const entry = document.createElement('div');
        const now = new Date();
        const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
        
        // 同步存入全量陣列
        allLogs.push(`[${timeStr}] ${message}`);
        
        // 限制陣列大小
        if (allLogs.length > 200) {
            allLogs = allLogs.slice(-200);
        }
        
        entry.className = `log-entry ${type}`;
        entry.innerHTML = `<span class="log-timestamp">[${timeStr}]</span> ${message}`;
        
        if (sortDesc) {
            systemLogs.insertBefore(entry, systemLogs.firstChild);
            systemLogs.scrollTop = 0;
            trimLogs();
        } else {
            systemLogs.appendChild(entry);
            systemLogs.scrollTop = systemLogs.scrollHeight;
            trimLogs();
        }
    }
    
    /**
     * 修剪日誌數量
     */
    function trimLogs() {
        if (!systemLogs) return;
        
        const maxLogs = 150;
        while (systemLogs.children.length > maxLogs) {
            if (sortDesc) {
                systemLogs.removeChild(systemLogs.lastChild);
            } else {
                systemLogs.removeChild(systemLogs.firstChild);
            }
        }
    }
    
    /**
     * 渲染日誌列表
     */
    function renderLogs() {
        if (!systemLogs) return;
        
        systemLogs.innerHTML = '';
        const logsToRender = sortDesc ? [...allLogs].reverse() : allLogs;
        
        logsToRender.forEach((log) => {
            const entry = document.createElement('div');
            entry.className = 'log-entry info';
            entry.innerHTML = `<span class="log-timestamp">${log}</span>`;
            systemLogs.appendChild(entry);
        });
        
        if (sortDesc) {
            systemLogs.scrollTop = 0;
        } else {
            systemLogs.scrollTop = systemLogs.scrollHeight;
        }
    }
    
    /**
     * 清除日誌
     */
    function clearLogs() {
        if (systemLogs) {
            systemLogs.innerHTML = '<div class="log-entry system">日誌已清除。</div>';
        }
        allLogs = [];
        addLog('日誌已清除。', 'system');
    }
    
    /**
     * 切換排序
     */
    function toggleSort() {
        sortDesc = !sortDesc;
        if (sortText) {
            sortText.textContent = sortDesc ? '新>舊' : '舊>新';
        }
        renderLogs();
    }
    
    /**
     * 更新報告時間戳
     * @param {Date|string} date - 日期物件或 ISO 字串
     */
    function updateTimestamp(date = null) {
        const timestampEl = document.getElementById('report-timestamp');
        if (!timestampEl) return;
        
        const now = date ? new Date(date) : new Date();
        const timeStr = now.toLocaleString('zh-TW', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        timestampEl.innerHTML = `<i class="fas fa-clock" style="margin-right: 4px;"></i>${timeStr}`;
        timestampEl.style.display = 'block';
    }
    
    /**
     * 隱藏報告時間戳
     */
    function hideTimestamp() {
        const timestampEl = document.getElementById('report-timestamp');
        if (timestampEl) {
            timestampEl.style.display = 'none';
        }
    }
    
    /**
     * 處理 WebSocket 數據
     * @param {Object} data - WebSocket 數據
     */
    function handleWebSocketData(data) {
        switch (data.type) {
            case 'log':
                addLog(data.content, data.level || 'info');
                break;
                
            case 'analysis_start':
                if (typeof AIThoughtBubble !== 'undefined') {
                    AIThoughtBubble.showAnalyzing(data.title);
                }
                addLog(`AI 分析中: ${data.title}`, 'ai');
                break;
                
            case 'analysis_stats':
                if (typeof SentimentStats !== 'undefined') {
                    SentimentStats.setFromData({
                        total: data.total,
                        success: data.success,
                        failure: data.failure
                    });
                }
                break;
                
            case 'analysis_result':
                if (typeof SentimentGauge !== 'undefined') {
                    SentimentGauge.update(data.final_score);
                }
                addLog(`最終情緒分數判定: ${data.final_score.toFixed(2)}`, 'success');
                break;
                
            case 'decision':
                // 更新時間戳
                updateTimestamp();
                
                // 更新 AI 思考泡泡
                if (typeof AIThoughtBubble !== 'undefined') {
                    AIThoughtBubble.showSuccess();
                }
                addLog(`決策生成完成: ${data.action}`, 'success');
                break;
        }
    }
    
    /**
     * 重置面板狀態
     */
    function reset() {
        if (typeof SentimentGauge !== 'undefined') {
            SentimentGauge.reset();
        }
        if (typeof SentimentStats !== 'undefined') {
            SentimentStats.reset();
        }
        if (typeof AIThoughtBubble !== 'undefined') {
            AIThoughtBubble.reset();
        }
        
        hideTimestamp();
        clearLogs();
    }
    
    // 自動初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // 公開 API
    return {
        addLog,
        clearLogs,
        toggleSort,
        updateTimestamp,
        hideTimestamp,
        handleWebSocketData,
        reset,
        init
    };
})();
