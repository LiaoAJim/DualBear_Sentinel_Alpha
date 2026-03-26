/**
 * Intelligence Panel Module - Step 1 實時偵察情報網
 * 獨立的新聞饋送模組
 */

const IntelligencePanel = (function() {
    'use strict';
    
    let newsFeed = null;
    let newsCount = null;
    let intelligenceLog = null;
    let maxItems = 50;
    let logEntries = [];
    const reconSourceMap = {
        ptt: ['ptt', 'ptt stock'],
        anue: ['anue', '鉅亨', '鉅亨網', '鉅亨網 anue'],
        yahoo: ['yahoo', 'yahoo 股市'],
        udn: ['udn', '經濟日報', '經濟日報 udn'],
        moneydj: ['moneydj', 'moneydj'],
        ctee: ['ctee', '工商', '工商時報'],
        tianxia: ['天下', 'tianxia', '天下雜誌'],
        caixin: ['財訊', 'caixin'],
        cmoney: ['cmoney'],
        ettoday: ['東森', 'ettoday', '東森新聞'],
        tvbs: ['tvbs'],
        cna: ['中央社', 'cna'],
        wantgoo: ['玩股網', 'wantgoo']
    };
    const finishedReconSources = new Set();
    
    /**
     * 初始化面板
     */
    function init() {
        newsFeed = document.getElementById('intelligence-feed');
        newsCount = document.getElementById('news-count');
        intelligenceLog = document.getElementById('intelligence-log');
        
        if (!newsFeed || !newsCount) {
            console.warn('[IntelligencePanel] 找不到必要的 DOM 元素');
            return;
        }
        
        console.log('[IntelligencePanel] 已初始化');
    }

    function renderLogs() {
        if (!intelligenceLog) return;
        if (logEntries.length === 0) {
            intelligenceLog.innerHTML = '<div class="log-entry system">等待 Step 1 偵察任務啟動。</div>';
            return;
        }

        intelligenceLog.innerHTML = logEntries
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

    function normalizeSourceName(source) {
        return (source || '').toString().trim().toLowerCase();
    }

    function findReconSourceKey(source) {
        const normalized = normalizeSourceName(source);
        if (!normalized) return null;

        for (const [key, aliases] of Object.entries(reconSourceMap)) {
            if (aliases.some(alias => normalized.includes(alias))) {
                return key;
            }
        }
        return null;
    }

    function updateReconCompleteCount() {
        const reconCompleteCount = document.getElementById('recon-complete-count');
        if (reconCompleteCount) {
            reconCompleteCount.innerText = String(finishedReconSources.size);
        }
    }

    function markSourceComplete(source) {
        const sourceKey = findReconSourceKey(source);
        if (!sourceKey || finishedReconSources.has(sourceKey)) return;

        finishedReconSources.add(sourceKey);
        const sourceEl = document.getElementById(`src-${sourceKey}`);
        if (!sourceEl) {
            updateReconCompleteCount();
            return;
        }

        const statusEl = sourceEl.querySelector('.status');
        if (statusEl) statusEl.innerText = '✓';
        sourceEl.classList.remove('failure');
        sourceEl.classList.add('success');
        sourceEl.style.color = 'var(--accent-blue)';
        updateReconCompleteCount();
    }

    function markSourceFailed(source) {
        const sourceKey = findReconSourceKey(source);
        if (!sourceKey || finishedReconSources.has(sourceKey)) return;

        finishedReconSources.add(sourceKey);
        const sourceEl = document.getElementById(`src-${sourceKey}`);
        if (!sourceEl) {
            updateReconCompleteCount();
            return;
        }

        const statusEl = sourceEl.querySelector('.status');
        if (statusEl) statusEl.innerText = '✕';
        sourceEl.classList.remove('success');
        sourceEl.classList.add('failure');
        sourceEl.style.color = 'var(--danger)';
        updateReconCompleteCount();
    }

    function resetSourceStatus() {
        finishedReconSources.clear();
        updateReconCompleteCount();

        Object.keys(reconSourceMap).forEach((sourceKey) => {
            const sourceEl = document.getElementById(`src-${sourceKey}`);
            if (!sourceEl) return;

            const statusEl = sourceEl.querySelector('.status');
            if (statusEl) statusEl.innerText = '○';
            sourceEl.classList.remove('success', 'failure');
            sourceEl.style.color = '';
        });
    }
    
    /**
     * 新增新聞項目
     * @param {Object} data - 新聞資料物件
     * @param {string} data.source - 新聞來源 (如 'Anue', 'PTT', 'Yahoo')
     * @param {string} data.title - 新聞標題
     * @param {string} data.date - 日期文字
     * @param {string} data.url - 連結網址
     * @param {string} data.author - 作者 (可選)
     */
    function addNewsItem(data) {
        if (!newsFeed) init();
        
        const emptyState = newsFeed.querySelector('.empty-state');
        if (emptyState) emptyState.remove();
        
        const item = document.createElement('div');
        item.className = 'news-item';
        
        // 動態處理來源 Class
        const sourceName = data.source || '未知來源';
        const sourceClass = `source-${sourceName.toLowerCase().split(' ')[0]}`;
        
        item.innerHTML = `
            <div class="news-item-header">
                <span class="news-source ${sourceClass}">${sourceName}</span>
                <span class="news-date">${data.date || '今'}</span>
            </div>
            <div class="news-title">${data.title}</div>
            ${data.author ? `<div class="news-author"><i class="fas fa-user-circle"></i> ${data.author}</div>` : ''}
        `;
        
        // 增加點擊跳轉功能
        const targetUrl = data.url || data.link;
        if (targetUrl) {
            item.style.cursor = 'pointer';
            item.title = "點擊開啟原始網頁";
            item.onclick = () => {
                window.open(targetUrl, '_blank');
            };
        }
        
        newsFeed.prepend(item);
        
        // 限制顯示數量
        if (newsFeed.children.length > maxItems) {
            newsFeed.removeChild(newsFeed.children[newsFeed.children.length - 1]);
        }
        
        newsCount.innerText = `${newsFeed.children.length} 則偵察`;
    }
    
    /**
     * 清除所有新聞項目
     */
    function clearNews() {
        if (!newsFeed) init();
        
        newsFeed.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-search"></i>
                <p>等待偵察數據導入...</p>
            </div>
        `;
        
        newsCount.innerText = '- 則偵察';
        resetSourceStatus();
        resetLogs();
    }
    
    /**
     * 取得目前新聞數量
     * @returns {number}
     */
    function getNewsCount() {
        if (!newsFeed) return 0;
        const emptyState = newsFeed.querySelector('.empty-state');
        return emptyState ? 0 : newsFeed.children.length;
    }
    
    /**
     * 設定最大顯示數量
     * @param {number} max - 最大數量
     */
    function setMaxItems(max) {
        maxItems = max;
    }
    
    /**
     * 批量新增新聞項目
     * @param {Array} items - 新聞資料陣列
     */
    function addNewsBatch(items) {
        if (Array.isArray(items)) {
            items.forEach(item => addNewsItem(item));
        }
    }
    
    // 自動初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // 公開 API
    return {
        addNewsItem,
        addNewsBatch,
        clearNews,
        getNewsCount,
        setMaxItems,
        markSourceComplete,
        markSourceFailed,
        resetSourceStatus,
        addLog,
        resetLogs,
        findReconSourceKey,
        init
    };
})();

// 為了向後相容，也 export 全域函數
function addNewsItem(data) {
    return IntelligencePanel.addNewsItem(data);
}
