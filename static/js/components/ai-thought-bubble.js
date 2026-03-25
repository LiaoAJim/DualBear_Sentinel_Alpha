/**
 * AI 思考泡泡組件 (AI Thought Bubble Component)
 * 顯示 AI 分析過程中的思考與狀態
 * 
 * @module AIThoughtBubble
 * @version 1.0.0
 */

const AIThoughtBubble = (function() {
    'use strict';
    
    // 狀態常量
    const STATUS = {
        IDLE: 'idle',
        ANALYZING: 'analyzing',
        SUCCESS: 'success',
        ERROR: 'error'
    };
    
    // 預設訊息
    const DEFAULT_MESSAGES = {
        [STATUS.IDLE]: '等待數據導入，準備點火分析儀...',
        [STATUS.ANALYZING]: '正在解析新聞內容...',
        [STATUS.SUCCESS]: '分析任務完成，哨兵持續監報量能中。',
        [STATUS.ERROR]: '分析過程發生錯誤，請檢查網路連線。'
    };
    
    // DOM 元素緩存
    let bubbleElement = null;
    let currentStatus = STATUS.IDLE;
    let currentMessage = DEFAULT_MESSAGES[STATUS.IDLE];
    
    /**
     * 初始化組件
     */
    function init() {
        bubbleElement = document.getElementById('ai-thought');
        
        if (!bubbleElement) {
            console.warn('[AIThoughtBubble] 找不到 DOM 元素 #ai-thought');
            return false;
        }
        
        // 設定初始狀態
        bubbleElement.setAttribute('data-status', currentStatus);
        
        console.log('[AIThoughtBubble] 已初始化');
        return true;
    }
    
    /**
     * 設定訊息
     * @param {string} message - 顯示的訊息
     * @param {string} status - 狀態 (可選)
     */
    function setMessage(message, status = null) {
        if (!bubbleElement) {
            if (!init()) return;
        }
        
        currentMessage = message || DEFAULT_MESSAGES[currentStatus];
        bubbleElement.innerText = currentMessage;
        
        if (status) {
            setStatus(status);
        }
    }
    
    /**
     * 設定狀態
     * @param {string} status - 狀態代碼
     */
    function setStatus(status) {
        if (!bubbleElement) {
            if (!init()) return;
        }
        
        if (!STATUS[status.toUpperCase()]) {
            console.warn('[AIThoughtBubble] 未知狀態:', status);
            return;
        }
        
        currentStatus = status.toLowerCase();
        bubbleElement.setAttribute('data-status', currentStatus);
        
        // 如果沒有自定義訊息，使用預設訊息
        if (!currentMessage || currentMessage === DEFAULT_MESSAGES[Object.keys(STATUS).find(k => STATUS[k] === currentStatus - 1)]) {
            currentMessage = DEFAULT_MESSAGES[currentStatus];
            bubbleElement.innerText = currentMessage;
        }
    }
    
    /**
     * 顯示分析中狀態
     * @param {string} title - 正在分析的新聞標題
     */
    function showAnalyzing(title = '') {
        if (title) {
            setMessage(`正在解析：「${title}」...`, STATUS.ANALYZING);
        } else {
            setMessage(DEFAULT_MESSAGES[STATUS.ANALYZING], STATUS.ANALYZING);
        }
    }
    
    /**
     * 顯示成功狀態
     * @param {string} message - 自定義訊息 (可選)
     */
    function showSuccess(message = '') {
        setMessage(message || DEFAULT_MESSAGES[STATUS.SUCCESS], STATUS.SUCCESS);
    }
    
    /**
     * 顯示錯誤狀態
     * @param {string} error - 錯誤訊息
     */
    function showError(error = '') {
        const msg = error ? `錯誤: ${error}` : DEFAULT_MESSAGES[STATUS.ERROR];
        setMessage(msg, STATUS.ERROR);
    }
    
    /**
     * 重置為空閒狀態
     */
    function reset() {
        setMessage(DEFAULT_MESSAGES[STATUS.IDLE], STATUS.IDLE);
    }
    
    /**
     * 獲取當前狀態
     * @returns {string}
     */
    function getStatus() {
        return currentStatus;
    }
    
    /**
     * 獲取當前訊息
     * @returns {string}
     */
    function getMessage() {
        return currentMessage;
    }
    
    // 自動初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // 公開 API
    return {
        setMessage,
        setStatus,
        showAnalyzing,
        showSuccess,
        showError,
        reset,
        getStatus,
        getMessage,
        STATUS,
        init
    };
})();

// 向後相容性
function updateAIThought(message) {
    if (message) {
        AIThoughtBubble.setMessage(message);
    }
}
