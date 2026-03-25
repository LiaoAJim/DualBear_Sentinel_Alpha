/**
 * 情緒詞庫編輯器模組 (Lexicon Editor Module)
 * 獨立的情緒詞彙管理介面
 * 
 * @module LexiconEditor
 * @version 1.0.0
 */

const LexiconEditor = (function() {
    'use strict';
    
    // 分類選項
    const CATEGORIES = [
        { value: 'bullish_extreme', label: '🚀 極度正向 (權重 5)', weight: 5 },
        { value: 'bullish_strong', label: '📈 強正向 (權重 3)', weight: 3 },
        { value: 'bullish_mild', label: '👍 輕微正向 (權重 1)', weight: 1 },
        { value: 'bearish_extreme', label: '💀 極度負向 (權重 -5)', weight: -5 },
        { value: 'bearish_strong', label: '📉 強負向 (權重 -3)', weight: -3 },
        { value: 'bearish_mild', label: '👎 輕微負向 (權重 -1)', weight: -1 },
        { value: 'sarcasm_negative', label: '⚠️ 反諷/利空出盡 (權重 -2)', weight: -2 },
        { value: 'quant_terms', label: '📊 量化術語 (權重 2)', weight: 2 },
        { value: 'crisis_terms', label: '🚨 危機術語 (權重 -3)', weight: -3 }
    ];
    
    // DOM 元素緩存
    let lexiconModal = null;
    let btnLexicon = null;
    let closeLexicon = null;
    let lexiconCategory = null;
    let lexiconWords = null;
    let lexiconCount = null;
    let btnSaveLexicon = null;
    
    // 回調函數
    let onSaveCallback = null;
    let onLoadCallback = null;
    
    /**
     * 初始化模組
     */
    function init() {
        cacheElements();
        bindEvents();
        console.log('[LexiconEditor] 已初始化');
    }
    
    /**
     * 快取 DOM 元素
     */
    function cacheElements() {
        lexiconModal = document.getElementById('lexicon-modal');
        btnLexicon = document.getElementById('btn-lexicon');
        closeLexicon = document.getElementById('close-lexicon');
        lexiconCategory = document.getElementById('lexicon-category');
        lexiconWords = document.getElementById('lexicon-words');
        lexiconCount = document.getElementById('lexicon-count');
        btnSaveLexicon = document.getElementById('btn-save-lexicon');
    }
    
    /**
     * 綁定事件
     */
    function bindEvents() {
        // 開啟按鈕 (多個按鈕可能觸發)
        const openButtons = [
            document.getElementById('btn-lexicon'),
            document.getElementById('btn-lexicon-step2')
        ];
        
        openButtons.forEach(btn => {
            if (btn) {
                btn.addEventListener('click', open);
            }
        });
        
        // 關閉按鈕
        if (closeLexicon) {
            closeLexicon.addEventListener('click', close);
        }
        
        // 點擊背景關閉
        if (lexiconModal) {
            lexiconModal.addEventListener('click', (e) => {
                if (e.target === lexiconModal) {
                    close();
                }
            });
        }
        
        // 分類切換
        if (lexiconCategory) {
            lexiconCategory.addEventListener('change', loadCategory);
        }
        
        // 儲存按鈕
        if (btnSaveLexicon) {
            btnSaveLexicon.addEventListener('click', save);
        }
        
    }
    
    /**
     * 開啟詞庫編輯器
     */
    function open() {
        if (lexiconModal) {
            lexiconModal.classList.add('show');
            lexiconModal.style.display = 'flex';
            loadCategory();
            
            if (onLoadCallback) {
                onLoadCallback();
            }
        }
    }
    
    /**
     * 關閉詞庫編輯器
     */
    function close() {
        if (lexiconModal) {
            lexiconModal.classList.remove('show');
            lexiconModal.style.display = 'none';
        }
    }
    
    /**
     * 切換顯示狀態
     */
    function toggle() {
        if (lexiconModal) {
            if (lexiconModal.style.display === 'none' || !lexiconModal.classList.contains('show')) {
                open();
            } else {
                close();
            }
        }
    }
    
    /**
     * 載入指定分類的詞彙
     */
    async function loadCategory() {
        const category = lexiconCategory ? lexiconCategory.value : 'bullish_extreme';
        
        try {
            const response = await fetch(`/api/lexicon/${category}`);
            const data = await response.json();
            
            if (lexiconWords) {
                if (data.error) {
                    lexiconWords.value = `# 載入失敗: ${data.error}`;
                } else {
                    const words = data.words || [];
                    lexiconWords.value = words.join('\n');
                    updateCount(words.length);
                }
            }
        } catch (err) {
            if (lexiconWords) {
                lexiconWords.value = `# 載入失敗: ${err}`;
            }
            updateCount(0);
        }
    }
    
    /**
     * 儲存詞庫
     */
    async function save() {
        if (!btnSaveLexicon || !lexiconWords || !lexiconCategory) return;
        
        // 視覺回饋
        const originalText = btnSaveLexicon.innerHTML;
        btnSaveLexicon.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 儲存中...';
        btnSaveLexicon.disabled = true;
        btnSaveLexicon.style.opacity = '0.7';
        
        const category = lexiconCategory.value;
        const wordsText = lexiconWords.value;
        
        // 解析詞彙
        const words = wordsText
            .split('\n')
            .map(w => w.trim())
            .filter(w => w.length > 0);
        
        try {
            const response = await fetch(`/api/lexicon/${category}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ words: words })
            });

            let result = {};
            try {
                result = await response.json();
            } catch {
                result = {};
            }

            const saveSucceeded = response.ok && result.status !== 'error';

            if (saveSucceeded) {
                // 成功回饋
                btnSaveLexicon.innerHTML = '<i class="fas fa-check"></i> 已儲存!';
                btnSaveLexicon.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
                updateCount(words.length);
                
                // 觸發回調
                if (onSaveCallback) {
                    try {
                        onSaveCallback({ category, count: words.length });
                    } catch (callbackError) {
                        console.warn('[LexiconEditor] 儲存成功，但 onSave 回調失敗:', callbackError);
                    }
                }
            } else {
                console.error('[LexiconEditor] 詞庫儲存 API 回傳失敗:', {
                    http_ok: response.ok,
                    status: response.status,
                    result
                });
                btnSaveLexicon.innerHTML = '<i class="fas fa-times"></i> 失敗';
                btnSaveLexicon.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
            }
        } catch (err) {
            console.error('[LexiconEditor] 詞庫儲存發生例外:', err);
            btnSaveLexicon.innerHTML = '<i class="fas fa-times"></i> 失敗';
            btnSaveLexicon.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
        }
        
        // 恢復按鈕
        setTimeout(() => {
            btnSaveLexicon.innerHTML = originalText;
            btnSaveLexicon.disabled = false;
            btnSaveLexicon.style.opacity = '1';
            btnSaveLexicon.style.background = '';
        }, 1500);
    }
    
    /**
     * 更新詞彙數量顯示
     * @param {number} count
     */
    function updateCount(count) {
        if (lexiconCount) {
            lexiconCount.textContent = `${count} 個詞`;
        }
    }
    
    /**
     * 獲取當前分類
     * @returns {string}
     */
    function getCurrentCategory() {
        return lexiconCategory ? lexiconCategory.value : 'bullish_extreme';
    }
    
    /**
     * 設定當前分類
     * @param {string} category
     */
    function setCurrentCategory(category) {
        if (lexiconCategory && CATEGORIES.some(c => c.value === category)) {
            lexiconCategory.value = category;
        }
    }
    
    /**
     * 獲取所有分類
     * @returns {Array}
     */
    function getCategories() {
        return [...CATEGORIES];
    }
    
    /**
     * 註冊儲存回調
     * @param {Function} callback
     */
    function onSave(callback) {
        if (typeof callback === 'function') {
            onSaveCallback = callback;
        }
    }
    
    /**
     * 註冊載入回調
     * @param {Function} callback
     */
    function onLoad(callback) {
        if (typeof callback === 'function') {
            onLoadCallback = callback;
        }
    }
    
    /**
     * 獲取詞彙文字
     * @returns {string}
     */
    function getWordsText() {
        return lexiconWords ? lexiconWords.value : '';
    }
    
    /**
     * 設定詞彙文字
     * @param {string} text
     */
    function setWordsText(text) {
        if (lexiconWords) {
            lexiconWords.value = text;
            const count = text.split('\n').filter(w => w.trim()).length;
            updateCount(count);
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
        open,
        close,
        toggle,
        loadCategory,
        save,
        getCurrentCategory,
        setCurrentCategory,
        getCategories,
        onSave,
        onLoad,
        getWordsText,
        setWordsText,
        init
    };
})();

// 向後相容性
function loadLexiconCategory() {
    return LexiconEditor.loadCategory();
}
