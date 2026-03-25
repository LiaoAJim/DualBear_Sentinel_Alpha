/**
 * AI 引擎選單組件 (Provider Selector Component)
 * 選擇要使用的 AI 分析引擎
 * 
 * @module ProviderSelector
 * @version 1.0.0
 */

const ProviderSelector = (function() {
    'use strict';
    
    // 可用的 AI 引擎
    const PROVIDERS = {
        auto: { name: 'Auto', icon: '⚙️', description: '自動選擇最佳引擎' },
        gemini: { name: 'Gemini', icon: '✨', description: 'Google Gemini 2.0 Flash' },
        nvidia: { name: 'NVIDIA', icon: '⚡', description: 'NVIDIA NIM Llama 3.1' },
        rule: { name: '規則引擎', icon: '📋', description: '本地規則分析，零成本' }
    };
    
    // DOM 元素緩存
    let selectElement = null;
    let currentProvider = 'auto';
    let changeCallbacks = [];
    
    /**
     * 初始化組件
     */
    function init() {
        selectElement = document.getElementById('provider-select');
        
        if (!selectElement) {
            console.warn('[ProviderSelector] 找不到 DOM 元素 #provider-select');
            return false;
        }
        
        // 綁定 change 事件
        selectElement.addEventListener('change', handleChange);
        
        // 讀取 localStorage 中的保存值
        const saved = localStorage.getItem('dualbear_provider');
        if (saved && PROVIDERS[saved]) {
            selectElement.value = saved;
            currentProvider = saved;
        }
        
        console.log('[ProviderSelector] 已初始化，當前引擎:', currentProvider);
        return true;
    }
    
    /**
     * 處理變更事件
     */
    function handleChange() {
        currentProvider = selectElement.value;
        
        // 保存到 localStorage
        localStorage.setItem('dualbear_provider', currentProvider);
        
        console.log('[ProviderSelector] 引擎已變更:', currentProvider);
        
        // 觸發回調
        changeCallbacks.forEach(cb => {
            try {
                cb(currentProvider);
            } catch (e) {
                console.error('[ProviderSelector] 回調執行錯誤:', e);
            }
        });
        
        // 派發自訂事件
        selectElement.dispatchEvent(new CustomEvent('provider-change', {
            detail: { provider: currentProvider, info: PROVIDERS[currentProvider] }
        }));
    }
    /**
     * 獲取當前選中的引擎
     * @returns {string} 引擎代碼
     */
    function getProvider() {
        return currentProvider;
    }
    
    /**
     * 設定引擎
     * @param {string} provider - 引擎代碼
     */
    function setProvider(provider) {
        if (!PROVIDERS[provider]) {
            console.warn('[ProviderSelector] 未知的引擎:', provider);
            return false;
        }
        
        if (selectElement) {
            selectElement.value = provider;
        }
        currentProvider = provider;
        localStorage.setItem('dualbear_provider', provider);
        
        return true;
    }
    
    /**
     * 獲取引擎資訊
     * @param {string} provider - 引擎代碼 (可選，默认当前)
     * @returns {Object} 引擎資訊
     */
    function getProviderInfo(provider = currentProvider) {
        return PROVIDERS[provider] || null;
    }
    
    /**
     * 註冊變更回調
     * @param {Function} callback - 回調函數
     */
    function onChange(callback) {
        if (typeof callback === 'function') {
            changeCallbacks.push(callback);
        }
    }
    
    /**
     * 移除回調
     * @param {Function} callback - 回調函數
     */
    function offChange(callback) {
        const index = changeCallbacks.indexOf(callback);
        if (index > -1) {
            changeCallbacks.splice(index, 1);
        }
    }
    
    /**
     * 獲取所有可用引擎
     * @returns {Object} 引擎列表
     */
    function getAllProviders() {
        return { ...PROVIDERS };
    }
    
    // 自動初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // 公開 API
    return {
        getProvider,
        setProvider,
        getProviderInfo,
        getAllProviders,
        onChange,
        offChange,
        init
    };
})();

// 向後相容性
function getProvider() {
    return ProviderSelector.getProvider();
}
