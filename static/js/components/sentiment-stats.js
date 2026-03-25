/**
 * 分析統計組件 (Analysis Stats Component)
 * 顯示總分析數量、成功次數、失敗次數
 * 
 * @module SentimentStats
 * @version 1.0.0
 */

const SentimentStats = (function() {
    'use strict';
    
    // 內部狀態
    let stats = {
        total: null,
        success: null,
        failure: null
    };
    
    // DOM 元素緩存
    let statTotal = null;
    let statSuccess = null;
    let statFailure = null;
    
    /**
     * 初始化組件
     */
    function init() {
        statTotal = document.getElementById('stat-total');
        statSuccess = document.getElementById('stat-success');
        statFailure = document.getElementById('stat-failure');
        
        if (!statTotal || !statSuccess || !statFailure) {
            console.warn('[SentimentStats] 找不到必要的 DOM 元素');
            return false;
        }
        
        // 初始渲染
        render();
        
        console.log('[SentimentStats] 已初始化');
        return true;
    }
    
    /**
     * 渲染統計數據
     */
    function render() {
        if (statTotal) statTotal.innerText = stats.total ?? '-';
        if (statSuccess) statSuccess.innerText = stats.success ?? '-';
        if (statFailure) statFailure.innerText = stats.failure ?? '-';
    }
    
    /**
     * 更新統計數據
     * @param {Object} newStats - { total?: number, success?: number, failure?: number }
     */
    function update(newStats) {
        if (newStats.total !== undefined) stats.total = newStats.total;
        if (newStats.success !== undefined) stats.success = newStats.success;
        if (newStats.failure !== undefined) stats.failure = newStats.failure;
        
        render();
    }
    
    /**
     * 遞增總數
     * @param {number} count - 遞增量 (預設 1)
     */
    function incrementTotal(count = 1) {
        stats.total += count;
        render();
    }
    
    /**
     * 遞增成功數
     * @param {number} count - 遞增量 (預設 1)
     */
    function incrementSuccess(count = 1) {
        stats.success += count;
        // 成功時也會遞增總數
        stats.total += count;
        render();
    }
    
    /**
     * 遞增失敗數
     * @param {number} count - 遞增量 (預設 1)
     */
    function incrementFailure(count = 1) {
        stats.failure += count;
        // 失敗時也會遞增總數
        stats.total += count;
        render();
    }
    
    /**
     * 獲取當前統計數據
     * @returns {Object} { total, success, failure }
     */
    function getStats() {
        return { ...stats };
    }
    
    /**
     * 獲取成功率
     * @returns {number} 成功率百分比 (0-100)
     */
    function getSuccessRate() {
        if (stats.total === 0) return 0;
        return Math.round((stats.success / stats.total) * 100);
    }
    
    /**
     * 重置統計數據
     */
    function reset() {
        stats = { total: null, success: null, failure: null };
        render();
    }
    
    /**
     * 從外部數據初始化
     * @param {Object} data - { total, success, failure }
     */
    function setFromData(data) {
        if (data && typeof data === 'object') {
            stats = {
                total: data.total || 0,
                success: data.success || 0,
                failure: data.failure || 0
            };
            render();
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
        update,
        incrementTotal,
        incrementSuccess,
        incrementFailure,
        getStats,
        getSuccessRate,
        reset,
        setFromData,
        init
    };
})();
