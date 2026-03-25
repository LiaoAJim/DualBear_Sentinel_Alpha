/**
 * 情緒儀表組件 (Sentiment Gauge Component)
 * SVG 圓形進度條顯示情緒分數
 * 
 * @module SentimentGauge
 * @version 1.0.0
 */

const SentimentGauge = (function() {
    'use strict';
    
    // 圓形進度條長度 (2 * PI * R = 2 * 3.14159 * 45 ≈ 282.7)
    const CIRCUMFERENCE = 282.7;
    
    // DOM 元素緩存
    let gaugeProgress = null;
    let scoreValue = null;
    let scoreLabel = null;
    
    /**
     * 初始化組件
     */
    function init() {
        gaugeProgress = document.getElementById('gauge-progress');
        scoreValue = document.getElementById('current-score');
        scoreLabel = document.getElementById('sentiment-flavor');
        
        if (!gaugeProgress || !scoreValue || !scoreLabel) {
            console.warn('[SentimentGauge] 找不到必要的 DOM 元素');
            return false;
        }
        
        console.log('[SentimentGauge] 已初始化');
        return true;
    }
    
    /**
     * 獲取情緒標籤文字
     * @param {number} score - 分數 (-1 到 1)
     * @returns {string} 分數標籤
     */
    function getScoreLabel(score) {
        if (score === null || score === undefined) {
            return { text: '分析失敗', color: 'var(--danger)' };
        }
        
        if (score > 0.5) {
            return { text: '極度樂觀', color: 'var(--accent-blue)' };
        } else if (score > 0.2) {
            return { text: '偏向利多', color: 'var(--accent-blue)' };
        } else if (score > -0.2) {
            return { text: '市場中性', color: 'var(--text-dim)' };
        } else if (score > -0.5) {
            return { text: '偏向利空', color: 'var(--accent-pink)' };
        } else {
            return { text: '極度悲觀', color: 'var(--accent-pink)' };
        }
    }
    
    /**
     * 更新儀表分數
     * @param {number|null} score - 分數 (-1 到 1), 為 null 時表示分析失敗
     */
    function update(score) {
        // 延遲初始化，確保 DOM 已準備好
        if (!gaugeProgress) {
            if (!init()) return;
        }
        
        if (score === null || score === undefined) {
            // 分析失敗狀態
            gaugeProgress.style.strokeDashoffset = CIRCUMFERENCE;
            scoreValue.innerText = 'N/A';
            const labelInfo = getScoreLabel(null);
            scoreLabel.innerText = labelInfo.text;
            scoreLabel.style.color = labelInfo.color;
            return;
        }
        
        // 將 -1.0 ~ 1.0 的分數映射到 0 ~ 100%
        const percentage = (score + 1) / 2;
        const offset = CIRCUMFERENCE - (percentage * CIRCUMFERENCE);
        
        // 更新進度條
        gaugeProgress.style.strokeDashoffset = offset;
        
        // 更新分數顯示
        scoreValue.innerText = score.toFixed(2);
        
        // 更新標籤
        const labelInfo = getScoreLabel(score);
        scoreLabel.innerText = labelInfo.text;
        scoreLabel.style.color = labelInfo.color;
    }
    
    /**
     * 獲取當前分數
     * @returns {number|null}
     */
    function getScore() {
        if (!scoreValue) return null;
        const text = scoreValue.innerText;
        if (text === 'N/A') return null;
        return parseFloat(text);
    }
    
    /**
     * 重置為初始狀態
     */
    function reset() {
        if (!gaugeProgress) {
            if (!init()) return;
        }
        gaugeProgress.style.strokeDashoffset = CIRCUMFERENCE;
        scoreValue.innerText = '--';
        scoreLabel.innerText = '等待分析';
        scoreLabel.style.color = 'var(--text-dim)';
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
        getScore,
        reset,
        init
    };
})();

// 向後相容性
function updateGauge(score) {
    return SentimentGauge.update(score);
}
