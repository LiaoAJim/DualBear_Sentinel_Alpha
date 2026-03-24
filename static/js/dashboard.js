document.addEventListener('DOMContentLoaded', () => {
    console.log('[Dashboard] JavaScript 已載入!');

    // 🏗️ 欄位順序管理系統 (Persistent Column Ordering)
    let panelOrder = JSON.parse(localStorage.getItem('dualbear_panel_order')) || [
        'intelligence-panel', 
        'sentiment-panel', 
        'decision-panel', 
        'asset-panel', 
        'backtest-panel'
    ];
    let selectedPanelId = null;

    const btnOrderLeft = document.getElementById('btn-order-left');
    const btnOrderRight = document.getElementById('btn-order-right');

    function initColumnOrdering() {
        applyPanelOrder();
        
        // 為所有面板添加點選選中邏輯
        panelOrder.forEach(id => {
            const panel = document.getElementById(id);
            if (panel) {
                panel.classList.add('selectable');
                panel.addEventListener('click', (e) => {
                    // 如果點擊的是面板內部的按鈕或輸入框，不要選中 (除非是點在空處)
                    const interactiveTags = ['BUTTON', 'INPUT', 'SELECT', 'A', 'TEXTAREA', 'I'];
                    if (interactiveTags.includes(e.target.tagName)) return;
                    
                    selectPanel(id);
                });
            }
        });

        if (btnOrderLeft) {
            btnOrderLeft.onclick = () => movePanel('left');
        }
        if (btnOrderRight) {
            btnOrderRight.onclick = () => movePanel('right');
        }
        
        updateOrderButtonsState();
    }

    function selectPanel(id) {
        if (selectedPanelId === id) {
            selectedPanelId = null; // 再次點擊取消選中
        } else {
            selectedPanelId = id;
        }
        
        panelOrder.forEach(pId => {
            const panel = document.getElementById(pId);
            if (panel) {
                panel.classList.toggle('selected', pId === selectedPanelId);
            }
        });
        
        updateOrderButtonsState();
        if (selectedPanelId) {
            const title = document.getElementById(id).querySelector('.panel-title').innerText.trim();
            addLog(`📍 已選好欄位：${title}，可使用左/右按鈕調整其順序。`, 'system');
        }
    }

    function movePanel(direction) {
        if (!selectedPanelId) return;
        
        const currentIndex = panelOrder.indexOf(selectedPanelId);
        let targetIndex = -1;
        
        if (direction === 'left' && currentIndex > 0) {
            targetIndex = currentIndex - 1;
        } else if (direction === 'right' && currentIndex < panelOrder.length - 1) {
            targetIndex = currentIndex + 1;
        }
        
        if (targetIndex !== -1) {
            // 交換位置
            [panelOrder[currentIndex], panelOrder[targetIndex]] = [panelOrder[targetIndex], panelOrder[currentIndex]];
            localStorage.setItem('dualbear_panel_order', JSON.stringify(panelOrder));
            applyPanelOrder();
            updateOrderButtonsState();
            saveSettings(); // 🆕 同步儲存至伺服器設定
            
            // 🛡️ 防禦性滾動：僅移動 main-grid 的水平捲軸，防止整個視窗位移
            const grid = document.getElementById('main-grid');
            const panel = document.getElementById(selectedPanelId);
            if (grid && panel) {
                const panelLeft = panel.offsetLeft;
                const panelWidth = panel.offsetWidth;
                const gridWidth = grid.offsetWidth;
                const targetScroll = panelLeft - (gridWidth / 2) + (panelWidth / 2);
                
                grid.scrollTo({
                    left: targetScroll,
                    behavior: 'smooth'
                });
            }
        }
    }

    function applyPanelOrder() {
        panelOrder.forEach((id, index) => {
            const panel = document.getElementById(id);
            if (panel) {
                panel.style.order = index;
            }
        });
    }

    function updateOrderButtonsState() {
        if (!btnOrderLeft || !btnOrderRight) return;
        
        if (!selectedPanelId) {
            btnOrderLeft.disabled = true;
            btnOrderRight.disabled = true;
            return;
        }
        
        const index = panelOrder.indexOf(selectedPanelId);
        btnOrderLeft.disabled = (index === 0);
        btnOrderRight.disabled = (index === panelOrder.length - 1);
    }

    // 調試：檢查關鍵元素是否存在
    const elements = ['btn-lexicon', 'btn-targets', 'btn-manual', 'btn-add-leverage2', 'custom-confirm-modal', 'lexicon-modal', 'targets-modal', 'manual-modal', 'leverage2-modal', 'toggle-sort', 'btn-order-left', 'btn-order-right'];
    elements.forEach(id => {
        const el = document.getElementById(id);
        console.log(`[元素檢查] #${id}: ${el ? '✓ 存在' : '✗ 不存在'}`);
    });

    initColumnOrdering();
    
    const newsFeed = document.getElementById('intelligence-feed');
    const newsCount = document.getElementById('news-count');
    const scoreValue = document.getElementById('current-score');
    const scoreLabel = document.getElementById('sentiment-flavor');
    const gaugeProgress = document.getElementById('gauge-progress');
    const aiThought = document.getElementById('ai-thought');
    const decisionAction = document.getElementById('decision-action');
    const targetPosition = document.getElementById('target-position');
    const decisionNotes = document.getElementById('decision-notes');
    const systemLogs = document.getElementById('system-logs');
    const connectionStatus = document.getElementById('conn-status'); // 修正為正確的 ID
    const clearLogsBtn = document.getElementById('clear-logs');
    const toggleSortBtn = document.getElementById('toggle-sort');
    const sortText = document.getElementById('sort-text');
    
    // 統計元素
    const statTotal = document.getElementById('stat-total');
    const statSuccess = document.getElementById('stat-success');
    const statFailure = document.getElementById('stat-failure');

    // 圓形進度條長度 (2 * PI * R)
    const CIRCUMFERENCE = 282.7;
    let allLogs = []; // 🆕 全量日誌儲存
    let sortDesc = true; // true = 新-舊 (新到上), false = 舊-新 (舊到上)

    // 渲染日誌列表
    function renderLogs() {
        systemLogs.innerHTML = '';
        const logsToRender = sortDesc ? [...allLogs].reverse() : allLogs;
        logsToRender.forEach((log) => {
            const entry = document.createElement('div');
            entry.className = 'log-entry info';
            entry.innerHTML = `<span style="opacity: 0.5;">${log}</span>`;
            systemLogs.appendChild(entry);
        });
        if (sortDesc) {
            systemLogs.scrollTop = 0;
        } else {
            systemLogs.scrollTop = systemLogs.scrollHeight;
        }
    }

    // 排序切換按鈕
    toggleSortBtn.addEventListener('click', () => {
        sortDesc = !sortDesc;
        sortText.textContent = sortDesc ? '新>舊' : '舊>新';
        renderLogs();
    });

    function addLog(message, type = 'info') {
        const entry = document.createElement('div');
        const now = new Date();
        const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
        
        // 同步存入全量陣列
        allLogs.push(`[${timeStr}] ${message}`);

        entry.className = `log-entry ${type}`;
        entry.innerHTML = `<span style="opacity: 0.5;">[${timeStr}]</span> ${message}`;
        
        if (sortDesc) {
            systemLogs.insertBefore(entry, systemLogs.firstChild);
            systemLogs.scrollTop = 0;
            if (systemLogs.children.length > 150) {
                systemLogs.removeChild(systemLogs.lastChild);
            }
        } else {
            systemLogs.appendChild(entry);
            systemLogs.scrollTop = systemLogs.scrollHeight;
            if (systemLogs.children.length > 150) {
                systemLogs.removeChild(systemLogs.firstChild);
            }
        }
    }

    function updateStepper(stepId) {
        const steps = ['idle', 'scouting', 'analyzing', 'reporting'];
        let activeFound = false;
        
        steps.forEach(s => {
            const el = document.getElementById(`step-${s}`);
            if (s === stepId) {
                el.className = 'step active';
                activeFound = true;
            } else if (!activeFound) {
                el.className = 'step completed';
            } else {
                el.className = 'step';
            }
        });
    }

    function updateGauge(score) {
        if (score === null || score === undefined) {
            gaugeProgress.style.strokeDashoffset = CIRCUMFERENCE; // 清空進度
            scoreValue.innerText = "N/A";
            scoreLabel.innerText = "分析失敗";
            scoreLabel.style.color = "var(--danger)";
            return;
        }

        // 將 -1.0 ~ 1.0 的分數映射到 0 ~ 100%
        const percentage = (score + 1) / 2;
        const offset = CIRCUMFERENCE - (percentage * CIRCUMFERENCE);
        gaugeProgress.style.strokeDashoffset = offset;
        
        // 數字動畫
        scoreValue.innerText = score.toFixed(2);
        
        // 顏色動態變化 (利多偏藍, 利空偏紅)
        if (score > 0.2) {
            scoreLabel.innerText = "偏向利多";
            scoreLabel.style.color = "var(--accent-blue)";
        } else if (score < -0.2) {
            scoreLabel.innerText = "偏向利空";
            scoreLabel.style.color = "var(--accent-pink)";
        } else {
            scoreLabel.innerText = "市場中性";
            scoreLabel.style.color = "var(--text-dim)";
        }
    }

    function addNewsItem(data) {
        const emptyState = newsFeed.querySelector('.empty-state');
        if (emptyState) emptyState.remove();

        const item = document.createElement('div');
        item.className = 'news-item';
        
        // 動態處理來源 Class
        const sourceName = data.source || '未知來源';
        const sourceClass = `source-${sourceName.toLowerCase().split(' ')[0]}`; // 取第一個詞
        
        item.innerHTML = `
            <div class="news-item-header">
                <span class="news-source ${sourceClass}">${sourceName}</span>
                <span class="news-date">${data.date || '今'}</span>
            </div>
            <div class="news-title">${data.title}</div>
            ${data.author ? `<div class="news-author"><i class="fas fa-user-circle"></i> ${data.author}</div>` : ''}
        `;
        
        // 增加點擊跳轉功能 (同時兼容 link 與 url 欄位)
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
        if (newsFeed.children.length > 50) {
            newsFeed.removeChild(newsFeed.lastChild);
        }
        
        newsCount.innerText = `${newsFeed.children.length} 則偵察`;
    }

    clearLogsBtn.addEventListener('click', () => {
        systemLogs.innerHTML = '<div class="log-entry system">日誌已清除。</div>';
    });

    // 📐 全局水平縮放邏輯 (戰略分界線)
    const mainGrid = document.getElementById('main-grid');
    const resizer1 = document.getElementById('resizer-1');
    const resizer2 = document.getElementById('resizer-2');
    let isResizingLeft = false;
    let isResizingRight = false;

    if (resizer1 && resizer2) {
        resizer1.addEventListener('mousedown', () => { isResizingLeft = true; document.body.style.cursor = 'col-resize'; });
        resizer2.addEventListener('mousedown', () => { isResizingRight = true; document.body.style.cursor = 'col-resize'; });

        document.addEventListener('mousemove', (e) => {
            if (!isResizingLeft && !isResizingRight) return;
            const containerRect = mainGrid.getBoundingClientRect();
            let columns = getComputedStyle(mainGrid).gridTemplateColumns.split(' ');

            if (isResizingLeft) {
                const newWidth = e.clientX - containerRect.left;
                if (newWidth > 200 && newWidth < 500) columns[0] = `${newWidth}px`;
            } else if (isResizingRight) {
                const newWidth = containerRect.right - e.clientX;
                if (newWidth > 300 && newWidth < 600) columns[4] = `${newWidth}px`;
            }
            mainGrid.style.gridTemplateColumns = columns.join(' ');
        });

        document.addEventListener('mouseup', () => {
            isResizingLeft = isResizingRight = false;
            document.body.style.cursor = 'default';
        });
    }

    // --- 資產配置與手冊邏輯 ---
    let currentTargetPositionPercent = 0.5; // 哨兵建議 (預設 50%)
    
    const btnManual = document.getElementById('btn-manual');
    const manualModal = document.getElementById('manual-modal');
    const closeManual = document.getElementById('close-manual');
    
    const inputSpareCash = document.getElementById('input-spare-cash');
    const inputCurrentStock = document.getElementById('input-current-stock');
    const inputLongTerm = document.getElementById('input-longterm-percent'); // 🆕 長期持有佔比
    
    const labelTotalAsset = document.getElementById('label-total-asset');
    const labelCurrentBeta = document.getElementById('label-current-beta'); // 🆕 目前 Beta 曝險
    const targetStockValueEl = document.getElementById('target-stock-value');
    const suggestCashValueEl = document.getElementById('suggest-cash-value');
    const suggestActionEl = document.getElementById('calc-suggest-action');
    const providerSelect = document.getElementById('provider-select'); // 🆕 AI 引擎選擇

    // 🆕 監聽 AI 引擎變更並儲存
    if (providerSelect) {
        providerSelect.addEventListener('change', () => {
            console.log('[設定] AI引擎已變更:', providerSelect.value);
            saveSettings();
        });
    }

    // 💾 持久化功能 (使用 API + localStorage 雙重備份)
    window.saveSettings = function() {
        // 確保能讀取到最新的 input 值
        const cashVal = document.getElementById('input-spare-cash')?.value || '500000';
        const stockVal = document.getElementById('input-current-stock')?.value || '500000';
        const longTermVal = document.getElementById('input-longterm-percent')?.value || '50';
        const providerVal = document.getElementById('provider-select')?.value || 'auto';

        const settings = {
            cash: cashVal,
            stock: stockVal,
            longterm: longTermVal,
            provider: providerVal,
            leverage2: leverage2Items,
            panelOrder: panelOrder // 🆕 儲存欄位順序
        };
        console.log('[設定] 正在執行儲存...', settings);
        
        // 同時備份到 localStorage (同步)
        localStorage.setItem('dualbear_asset_settings', JSON.stringify(settings));
        
        // 非同步儲存到 API (背景執行)
        return fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        })
        .then(resp => resp.json())
        .then(res => {
            if (res.status === 'success') {
                console.log('[設定] API 儲存成功');
            } else {
                console.warn('[設定] API 儲存異常:', res.message);
            }
        })
        .catch(e => console.error('[設定] API 儲存失敗:', e));
    }

    async function loadSettings() {
        console.log('[設定] 正在載入設定...');
        console.log('[設定] leverage2Items 初始值:', leverage2Items);
        
        // 先嘗試從 API 讀取
        try {
            const resp = await fetch('/api/settings');
            if (resp.ok) {
                const settings = await resp.json();
                console.log('[設定] 從 API 取得:', JSON.stringify(settings));
                if (inputSpareCash) inputSpareCash.value = settings.cash || '500000';
                if (inputCurrentStock) inputCurrentStock.value = settings.stock || '500000';
                if (inputLongTerm) inputLongTerm.value = settings.longterm || '50';
                if (providerSelect) providerSelect.value = settings.provider || 'auto';
                
                // 🆕 載入欄位順序
                if (settings.panelOrder && Array.isArray(settings.panelOrder)) {
                    panelOrder = settings.panelOrder;
                    localStorage.setItem('dualbear_panel_order', JSON.stringify(panelOrder));
                    applyPanelOrder();
                }

                console.log('[設定] leverage2 資料:', settings.leverage2);
                if (settings.leverage2 && Array.isArray(settings.leverage2)) {
                    leverage2Items = settings.leverage2;
                    console.log('[設定] ✅ 已載入正2資料:', leverage2Items.length, '筆');
                    updateLeverage2Display();
                } else {
                    console.log('[設定] ⚠️ 無正2資料或格式錯誤');
                }
                console.log('[設定] 從 API 載入成功!');
                updateAssetCalculations();
                initLeverage2();
                return;
            }
        } catch (e) {
            console.log('[設定] ❌ API 讀取失敗:', e);
        }
        
        // 降級到 localStorage
        const saved = localStorage.getItem('dualbear_asset_settings');
        console.log('[設定] localStorage 資料:', saved);
        if (saved) {
            try {
                const settings = JSON.parse(saved);
                if (inputSpareCash) inputSpareCash.value = settings.cash || '500000';
                if (inputCurrentStock) inputCurrentStock.value = settings.stock || '500000';
                if (inputLongTerm) inputLongTerm.value = settings.longterm || '50';
                if (providerSelect) providerSelect.value = settings.provider || 'auto';
                console.log('[設定] leverage2 資料(ls):', settings.leverage2);
                if (settings.leverage2 && Array.isArray(settings.leverage2)) {
                    leverage2Items = settings.leverage2;
                    console.log('[設定] 已載入正2資料(ls):', leverage2Items.length, '筆');
                    updateLeverage2Display();
                }
            } catch (e) {
                console.log('[設定] localStorage 解析失敗:', e);
            }
        }
        updateAssetCalculations();
        initLeverage2();
    }

    // 💡 手冊彈窗
    if (btnManual) btnManual.onclick = () => manualModal.classList.add('show');
    if (closeManual) closeManual.onclick = () => manualModal.classList.remove('show');
    
    // 💡 核心演算法：(總資產 * 長期比例) + (剩餘可用 * 哨兵建議%)
    window.updateAssetCalculations = function() {
        const spareCashInput = document.getElementById('input-spare-cash');
        const currentStockInput = document.getElementById('input-current-stock');
        const longTermInput = document.getElementById('input-longterm-percent');
        
        if (!spareCashInput || !currentStockInput) return;

        const spareCash = parseFloat(spareCashInput.value) || 0;
        const currentStock = parseFloat(currentStockInput.value) || 0;
        const longTermRate = (parseFloat(longTermInput ? longTermInput.value : 50) || 0) / 100;
        
        // 🆕 取得正2加重曝險部分 (由於「目前持股」已包含市值，這裡取得 1x 市值的加權額度)
        const leverage2ExtraWeight = getLeverage2Total();
        
        // 當前總資產 = 閒置資金 + 持股市值 (持股已包含正2的本金部分)
        const totalAsset = spareCash + currentStock;
        
        // 總曝險市值 = 持股市值 (1x) + 正2加重額 (額外的 1x) = 達成 2x 曝險效果
        const exposureValue = currentStock + leverage2ExtraWeight;
        
        // Beta = 曝險市值 / 當前總資產
        const currentBeta = totalAsset > 0 ? (exposureValue / totalAsset) : 0;
        
        labelTotalAsset.innerText = `$ ${totalAsset.toLocaleString()}`;
        
        // 1. 長期鎖定不變部分
        const coreHolding = totalAsset * longTermRate;
        // 2. 戰術跟隨部分 (針對剩餘的 1 - longTermRate 進行分配)
        const logicalPool = totalAsset - coreHolding;
        const tacticalHolding = logicalPool * currentTargetPositionPercent;
        
        // 3. 最終目標
        const finalTargetValue = coreHolding + tacticalHolding;
        const suggestCash = totalAsset - finalTargetValue;
        const diff = finalTargetValue - exposureValue;

        // UI 更新
        targetStockValueEl.innerText = `$ ${finalTargetValue.toLocaleString(undefined, {maximumFractionDigits: 0})}`;
        if (suggestCashValueEl) suggestCashValueEl.innerText = `$ ${suggestCash.toLocaleString(undefined, {maximumFractionDigits: 0})}`;
        
        // 🆕 更新曝險市值顯示
        const labelExposureValue = document.getElementById('label-exposure-value');
        if (labelExposureValue) {
            labelExposureValue.innerText = '$' + exposureValue.toLocaleString();
        }

        if (labelCurrentBeta) {
            labelCurrentBeta.innerText = currentBeta.toFixed(2);
            // 根據曝險程度改變顏色 (Beta>1 表示有槓桿曝險)
            labelCurrentBeta.style.color = currentBeta > 1.1 ? 'var(--accent-pink)' : (currentBeta > 1 ? '#f59e0b' : '#fff');
        }

        if (Math.abs(diff) < 1000) {
            suggestActionEl.innerText = "無需調整";
            suggestActionEl.style.color = "var(--text-dim)";
        } else if (diff > 0) {
            suggestActionEl.innerText = `加碼 $${Math.abs(diff).toLocaleString(undefined, {maximumFractionDigits: 0})}`;
            suggestActionEl.style.color = "var(--accent-blue)";
        } else {
            suggestActionEl.innerText = `減碼 $${Math.abs(diff).toLocaleString(undefined, {maximumFractionDigits: 0})}`;
            suggestActionEl.style.color = "var(--accent-pink)";
        }
        
        saveSettings(); // 同步儲存
    }

    if (inputSpareCash && inputCurrentStock) {
        [inputSpareCash, inputCurrentStock, inputLongTerm].forEach(input => {
            if (input) input.addEventListener('input', updateAssetCalculations);
        });
    }

    // 初始化讀取
    loadSettings().then(() => {
        console.log('[設定] 初始化完成');
        loadTargets(); // 🆕 同時載入標的清單
    });

    // 📡 WebSocket 連線 (儀表板大腦通訊)
    let socket;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 20;
    let wsAutoReconnect = true; // 控制是否自動重連

    function handleUpdate(data) {
        if (data.type === 'log') {
            addLog(data.content, data.level || 'info');
        } else if (data.type === 'status') {
            updateStepper(data.step);
        } else if (data.type === 'intelligence') {
            addNewsItem(data.content);
            const src = data.content.source || '未知';
            addLog(`[${src}] 蒐集情報: ${data.content.title}`, 'scout');
        } else if (data.type === 'quant_data') {
            updateQuantUI(data);
            addLog('籌碼面偵察完成，量化指標已同步。', 'scout');
        } else if (data.type === 'vix_data') {
            // VIX 恐慌指數顯示
            const vixEl = document.getElementById('quant-vix');
            if (vixEl && data.value) {
                vixEl.textContent = data.value;
                const vVal = parseFloat(data.value);
                // 根據 VIX 數值變色
                if (vVal >= 30) {
                    vixEl.style.color = 'var(--accent-pink)';  // 恐慌
                } else if (vVal >= 25) {
                    vixEl.style.color = '#f59e0b';  // 緊張
                } else if (vVal < 15) {
                    vixEl.style.color = '#10b981';  // 極度樂觀
                } else {
                    vixEl.style.color = 'var(--accent-blue)';  // 正常
                }
            }
            // 同時更新情緒面板的 VIX 提示
            if (data.interpretation) {
                addLog(`📊 VIX: ${data.value} (${data.interpretation})`, 'scout');
            }
        } else if (data.type === 'analysis_start') {
            aiThought.innerText = `正在解析："${data.title}"...`;
            addLog(`AI 分析中: ${data.title}`, 'ai');
        } else if (data.type === 'analysis_stats') {
            if (statTotal) statTotal.innerText = data.total;
            if (statSuccess) statSuccess.innerText = data.success;
            if (statFailure) statFailure.innerText = data.failure;
        } else if (data.type === 'analysis_result') {
            updateGauge(data.final_score);
            addLog(`最終情緒分數判定: ${data.final_score.toFixed(2)}`, 'success');
        } else if (data.type === 'decision') {
            decisionAction.innerText = data.action;
            targetPosition.innerText = data.target_position;
            decisionNotes.innerText = data.recon_notes;
            
            // 處理「分析失敗」樣式
            if (data.action === "分析失敗") {
                decisionAction.style.color = "var(--danger)";
                targetPosition.style.color = "var(--text-dim)";
            } else {
                decisionAction.style.color = ""; // 恢復 CSS 定義
                targetPosition.style.color = "";
            }

            // 更新資產配置比例
            const match = data.target_position.match(/(\d+)%/);
            if (match) {
                currentTargetPositionPercent = parseInt(match[1]) / 100;
                updateAssetCalculations();
            }

            // 處理可能存在的調整資訊
            if (data.quant_adjustment) {
                const adjText = data.quant_adjustment > 0 ? `+${data.quant_adjustment}%` : `${data.quant_adjustment}%`;
                addLog(`哨兵策略：量化指標介入修正了 ${adjText} 的倉位佈置。`, 'system');
            }

            aiThought.innerText = "分析任務完成，哨兵持續監報量能中。";
            addLog(`決策生成完成: ${data.action}`, 'success');
            
            // 更新報告時間戳為當前時間
            const reportTimestamp = document.getElementById('report-timestamp');
            if (reportTimestamp) {
                const now = new Date();
                const timeStr = now.toLocaleString('zh-TW', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                });
                reportTimestamp.innerHTML = `<i class="fas fa-clock" style="margin-right: 4px;"></i>${timeStr}`;
                reportTimestamp.style.display = 'block';
            }
            
            resetRunButton();
            
            // 🚫 任務完成後停止自動重連，避免視窗閃爍
            wsAutoReconnect = false;
        }
    }

    function connectWS() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        console.log(`📡 正在建立戰略鏈路: ${wsUrl}...`);
        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            console.log('✅ 戰略鏈路已鎖定，數據同步中...');
            connectionStatus.classList.remove('disconnect');
            connectionStatus.classList.add('online');
            connectionStatus.querySelector('.status-text').innerText = '系統線上';
            addLog('核心連線成功 (戰略傳輸穩定)', 'success');
            reconnectAttempts = 0;
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleUpdate(data);
        };

        socket.onclose = () => {
            console.log('❌ 鏈路失聯...');
            connectionStatus.classList.remove('online');
            connectionStatus.classList.add('disconnect');
            connectionStatus.querySelector('.status-text').innerText = '斷開連線';
            
            // 只在允許重連且未超限時重連
            if (wsAutoReconnect && reconnectAttempts < maxReconnectAttempts) {
                reconnectAttempts++;
                console.log(`🔄 等待重連... (${reconnectAttempts}/${maxReconnectAttempts})`);
                setTimeout(connectWS, 3000); // 3秒後重連（增加間隔減少閃爍）
            } else if (!wsAutoReconnect) {
                console.log('⏹️ 任務已完成，停止自動重連');
                addLog('📍 任務完成，等待下次執行...', 'system');
            } else {
                addLog("💤 連線已斷開，可點擊「立即執行」重啟任務", "info");
            }
        };

        socket.onerror = (err) => {
            console.error('Socket Error:', err);
        };
    }

    // 啟動首波連線
    connectWS();

    let isRunning = false;

    function resetRunButton() {
        isRunning = false;
        btnRun.disabled = false;
        btnRun.innerHTML = '<i class="fas fa-play"></i> 立即執行';
        btnRun.style.background = ''; // 恢復 CSS 定義的樣式
        
        // 清除報告時間戳
        const reportTimestamp = document.getElementById('report-timestamp');
        if (reportTimestamp) {
            reportTimestamp.style.display = 'none';
        }
    }

    // --- 初始化控制按鈕 ---
    const btnRun = document.getElementById('btn-run');
    const btnHistory = document.getElementById('btn-history');
    const btnCloseHistory = document.getElementById('close-history');
    const historyDrawer = document.getElementById('history-drawer');
    const historyList = document.getElementById('history-list');

    // 💡 執行與停止任務
    btnRun.onclick = async () => {
        if (!isRunning) {
            startRecon();
        } else {
            stopRecon();
        }
    };

    async function startRecon() {
        btnRun.disabled = true;
        btnRun.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 啟動中...';
        
        // 🆕 清除報告時間戳（準備載入新報告）
        const reportTimestamp = document.getElementById('report-timestamp');
        if (reportTimestamp) {
            reportTimestamp.style.display = 'none';
        }
        
        // 🆕 獲取使用者選擇的 AI 引擎（已在上方定義 providerSelect）
        const preferred = providerSelect ? providerSelect.value : 'auto';

        // 🚀 任務啟動時啟用 WebSocket 重連
        wsAutoReconnect = true;
        reconnectAttempts = 0;
        
        // 如果 WebSocket 已斷開，重新連接
        if (!socket || socket.readyState === WebSocket.CLOSED) {
            connectWS();
        }

        addLog(`戰略任務啟動 (引擎指定: ${preferred})...`, "system");
        
        try {
            const response = await fetch('/api/run', { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ preferred_provider: preferred })
            });
            const result = await response.json();
            
            if (result.status === 'started') {
                isRunning = true;
                btnRun.disabled = false;
                btnRun.innerHTML = '<i class="fas fa-stop-circle"></i> 停止執行';
                btnRun.style.background = 'linear-gradient(135deg, #ff4b2b 0%, #ff416c 100%)';
                addLog(`偵察進程已啟動 (PID: ${result.pid})`, "success");
            } else {
                addLog(`啟動失敗: ${result.message}`, "error");
                resetRunButton();
            }
        } catch (err) {
            addLog(`請求發生錯誤: ${err}`, "error");
            resetRunButton();
        }
    }

    async function stopRecon() {
        btnRun.disabled = true;
        btnRun.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 停止中...';
        try {
            const response = await fetch('/api/stop', { method: 'POST' });
            const result = await response.json();
            if (result.status === 'stopped') {
                addLog("🛑 哨兵任務已由使用者手動中止。", "warning");
                resetRunButton();
            } else {
                addLog("目前沒有正在執行的任務。", "info");
                resetRunButton();
            }
        } catch (err) {
            addLog(`停止請求失敗: ${err}`, "error");
            resetRunButton();
        }
    }

    // 💡 歷史檔案邏輯
    btnHistory.onclick = async () => {
        historyDrawer.classList.add('active');
        loadHistoryList();
    };

    btnCloseHistory.onclick = () => {
        historyDrawer.classList.remove('active');
    };

    // --- 回測驗證邏輯（第五欄面板）---
    const backtestSymbolInline = document.getElementById('backtest-symbol-inline');
    const btnRunBacktestInline = document.getElementById('btn-run-backtest-inline');
    const backtestResultsInline = document.getElementById('backtest-results-inline');
    const btnTargetsInline = document.getElementById('btn-targets-inline');

    // 回測函數（僅用於第五欄面板）
    async function runBacktestInline() {
        const symbol = backtestSymbolInline.value;
        const btn = btnRunBacktestInline;
        const resultsEl = backtestResultsInline;
        
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 回測中...';
        resultsEl.innerHTML = '<div class="loading-spinner">正在分析歷史數據與股價...</div>';
        
        try {
            const response = await fetch(`/api/backtest?symbol=${encodeURIComponent(symbol)}`);
            const result = await response.json();
            
            if (result.status === 'error') {
                resultsEl.innerHTML = `
                    <div style="text-align: center; padding: 20px; color: #ef4444;">
                        <i class="fas fa-exclamation-triangle" style="font-size: 32px;"></i>
                        <p style="margin-top: 10px; font-size: 12px;">回測失敗</p>
                        <p style="font-size: 11px; color: var(--text-dim); margin-top: 8px;">${result.message}</p>
                    </div>
                `;
            } else if (result.status === 'insufficient_data') {
                resultsEl.innerHTML = `
                    <div style="text-align: center; padding: 20px;">
                        <i class="fas fa-hourglass-half" style="font-size: 36px; color: #f59e0b; opacity: 0.7;"></i>
                        <p style="margin-top: 10px; color: #f59e0b; font-weight: 700; font-size: 12px;">歷史資料不足</p>
                        <p style="font-size: 11px; color: var(--text-dim); margin-top: 8px;">${result.message}</p>
                        <p style="font-size: 10px; color: var(--text-dim); margin-top: 10px;">💡 ${result.suggestion}</p>
                    </div>
                `;
            } else {
                resultsEl.innerHTML = renderBacktestResults(result);
            }
        } catch (err) {
            resultsEl.innerHTML = `
                <div style="text-align: center; padding: 20px; color: #ef4444;">
                    <i class="fas fa-times-circle" style="font-size: 32px;"></i>
                    <p style="margin-top: 10px; font-size: 12px;">連線失敗: ${err}</p>
                </div>
            `;
        }
        
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-play"></i> 回測';
    }

    // 第五欄回測按鈕
    if (btnRunBacktestInline) {
        btnRunBacktestInline.onclick = runBacktestInline;
    }

    // 第五欄標的管理按鈕 -> 開啟 targets modal
    if (btnTargetsInline) {
        console.log('[DEBUG] 綁定 btnTargetsInline click');
        btnTargetsInline.onclick = () => {
            console.log('[DEBUG] btnTargetsInline 被點擊');
            const targetsModal = document.getElementById('targets-modal');
            console.log('[DEBUG] targetsModal:', targetsModal);
            if (targetsModal) {
                targetsModal.style.display = 'flex';
                targetsModal.classList.add('show');
            }
        };
    } else {
        console.log('[DEBUG] btnTargetsInline 為 null!');
    }

    function renderBacktestResults(result) {
        const bullish = result.bullish || {};
        const bearish = result.bearish || {};
        const neutral = result.neutral || {};
        
        const getColor = (rate) => rate >= 60 ? '#10b981' : (rate >= 50 ? '#f59e0b' : '#ef4444');
        
        return `
            <div style="padding: 15px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <span style="color: var(--text-dim); font-size: 12px;">符號: ${result.symbol}</span>
                    <span style="color: var(--text-dim); font-size: 11px;">有效交易: ${result.valid_trades} 筆</span>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 20px;">
                    <!-- 情緒正向 -->
                    <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 12px; padding: 15px; text-align: center;">
                        <div style="font-size: 11px; color: #10b981; margin-bottom: 8px;">📈 情緒正向</div>
                        <div style="font-size: 28px; font-weight: 900; color: ${getColor(bullish.win_rate)};">${bullish.win_rate?.toFixed(0) || 0}%</div>
                        <div style="font-size: 10px; color: var(--text-dim);">勝率</div>
                        <div style="margin-top: 10px; font-size: 11px; color: #fff;">平均 ${bullish.avg_return?.toFixed(2) || 0}%</div>
                        <div style="font-size: 10px; color: var(--text-dim);">交易 ${bullish.count || 0} 次</div>
                    </div>
                    
                    <!-- 情緒中性 -->
                    <div style="background: rgba(107, 114, 128, 0.1); border: 1px solid rgba(107, 114, 128, 0.2); border-radius: 12px; padding: 15px; text-align: center;">
                        <div style="font-size: 11px; color: #9ca3af; margin-bottom: 8px;">⚖️ 情緒中性</div>
                        <div style="font-size: 28px; font-weight: 900; color: ${getColor(neutral.win_rate)};">${neutral.win_rate?.toFixed(0) || 0}%</div>
                        <div style="font-size: 10px; color: var(--text-dim);">勝率</div>
                        <div style="margin-top: 10px; font-size: 11px; color: #fff;">平均 ${neutral.avg_return?.toFixed(2) || 0}%</div>
                        <div style="font-size: 10px; color: var(--text-dim);">交易 ${neutral.count || 0} 次</div>
                    </div>
                    
                    <!-- 情緒負向 -->
                    <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 12px; padding: 15px; text-align: center;">
                        <div style="font-size: 11px; color: #ef4444; margin-bottom: 8px;">📉 情緒負向</div>
                        <div style="font-size: 28px; font-weight: 900; color: ${getColor(bearish.win_rate)};">${bearish.win_rate?.toFixed(0) || 0}%</div>
                        <div style="font-size: 10px; color: var(--text-dim);">勝率</div>
                        <div style="margin-top: 10px; font-size: 11px; color: #fff;">平均 ${bearish.avg_return?.toFixed(2) || 0}%</div>
                        <div style="font-size: 10px; color: var(--text-dim);">交易 ${bearish.count || 0} 次</div>
                    </div>
                </div>
                
                <!-- 結論 -->
                <div style="background: rgba(0,0,0,0.3); border-radius: 8px; padding: 12px; margin-top: 15px;">
                    <div style="font-size: 11px; color: var(--text-dim); margin-bottom: 8px;">🎯 回測結論</div>
                    ${bullish.count > 0 && bearish.count > 0 ? (
                        bullish.win_rate > bearish.win_rate ?
                        `<div style="color: #10b981; font-size: 12px;"><i class="fas fa-check-circle"></i> 規則引擎有效！情緒正向時勝率(${bullish.win_rate.toFixed(1)}%) > 情緒負向時(${bearish.win_rate.toFixed(1)}%)</div>` :
                        `<div style="color: #f59e0b; font-size: 12px;"><i class="fas fa-exclamation-triangle"></i> 規則引擎可能需要調整。情緒正向時勝率(${bullish.win_rate.toFixed(1)}%) <= 情緒負向時(${bearish.win_rate.toFixed(1)}%)</div>`
                    ) : `<div style="color: var(--text-dim); font-size: 12px;">數據不足，需要更多歷史記錄</div>`}
                </div>
            </div>
        `;
    }

    async function loadHistoryList() {
        historyList.innerHTML = '<div class="loading-spinner">載入檔案中...</div>';
        try {
            const response = await fetch('/api/history');
            const data = await response.json();
            
            if (data.dates && data.dates.length > 0) {
                historyList.innerHTML = '';
                data.dates.forEach(item => {
                    // 支援新格式（物件）和舊格式（字串）
                    const rawDate = typeof item === 'string' ? item : item.date;
                    const stats = typeof item === 'object' ? (item.analysis_stats || {}) : {};
                    const sentiment = typeof item === 'object' ? item.sentiment_score : null;
                    
                    // 解析 2026-03-19_143005 -> 2026-03-19 14:30:05
                    const parts = rawDate.split('_');
                    const datePart = parts[0];
                    let timePart = "";
                    if (parts[1]) {
                        timePart = `${parts[1].substring(0,2)}:${parts[1].substring(2,4)}:${parts[1].substring(4,6)}`;
                    }
                    
                    // 根據情緒分數設定顏色
                    let scoreColor = 'var(--text-dim)';
                    let scoreText = '';
                    if (sentiment !== null && sentiment !== undefined) {
                        scoreColor = sentiment > 0.5 ? '#10b981' : (sentiment < 0.3 ? '#ef4444' : '#f59e0b');
                        scoreText = sentiment.toFixed(2);
                    }
                    
                    // 計算可靠度百分比
                    const total = stats.total || 0;
                    const success = stats.success || 0;
                    const failure = stats.failure || 0;
                    const successRate = total > 0 ? Math.round((success / total) * 100) : 0;

                    const historyItem = document.createElement('div');
                    historyItem.className = 'history-item';
                    historyItem.style.display = 'flex';
                    historyItem.style.justifyContent = 'space-between';
                    historyItem.style.alignItems = 'center';
                    
                    historyItem.innerHTML = `
                        <div class="history-info" style="cursor: pointer; flex: 1;">
                            <span class="date-text" style="font-weight: 700; color: #fff;">${datePart}</span>
                            <span class="time-text" style="font-size: 11px; color: var(--accent-blue); display: block; margin-top: 2px;">${timePart}</span>
                            <span style="font-size: 10px; color: ${scoreColor};">情緒 ${scoreText}</span>
                        </div>
                        <div class="history-stats" style="text-align: center; padding: 0 10px; min-width: 70px;">
                            <span style="font-size: 9px; color: var(--text-dim);">可信度</span><br>
                            <span class="stats-badge" style="
                                display: inline-block;
                                font-size: 11px;
                                font-weight: 700;
                                padding: 2px 6px;
                                border-radius: 4px;
                                background: ${successRate >= 90 ? 'rgba(16, 185, 129, 0.2)' : (successRate >= 70 ? 'rgba(245, 158, 11, 0.2)' : 'rgba(239, 68, 68, 0.2)')};
                                color: ${successRate >= 90 ? '#10b981' : (successRate >= 70 ? '#f59e0b' : '#ef4444')};
                            ">${successRate}%</span>
                            <div style="font-size: 9px; color: var(--text-dim); margin-top: 2px;">${stats.total || 0}/${stats.success || 0}/${stats.failure || 0}</div>
                        </div>
                        <div class="history-actions" style="display: flex; align-items: center; gap: 15px;">
                            <span class="count-badge" style="cursor: pointer; color: var(--accent-blue); font-size: 12px;">查看 <i class="fas fa-chevron-right"></i></span>
                            <button class="delete-history-btn" title="刪除此報告" style="background: transparent; border: none; color: #ff4b2b; cursor: pointer; padding: 5px; opacity: 0.6; transition: all 0.2s;">
                                <i class="fas fa-trash-alt"></i>
                            </button>
                        </div>
                    `;

                    // 點擊左側文字 -> 載入詳情
                    historyItem.querySelector('.history-info').onclick = () => loadHistoryDetail(rawDate);
                    historyItem.querySelector('.count-badge').onclick = () => loadHistoryDetail(rawDate);
                    
                    // 點擊垃圾桶 -> 刪除
                    const delBtn = historyItem.querySelector('.delete-history-btn');
                    delBtn.onmouseover = () => delBtn.style.opacity = "1";
                    delBtn.onmouseout = () => delBtn.style.opacity = "0.6";
                    delBtn.onclick = async (e) => {
                        e.stopPropagation(); // 防止觸發載入
                        const confirmed = await window.openCustomConfirm(`⚠️ 確定要永久刪除這份報告嗎？<br><span style="font-size:12px; color:var(--text-dim)">${datePart} ${timePart}</span>`);
                        
                        if (confirmed) {
                            try {
                                const resp = await fetch(`/api/history/${rawDate}`, { method: 'DELETE' });
                                const res = await resp.json();
                                if (res.status === 'success') {
                                    historyItem.style.opacity = '0';
                                    historyItem.style.transform = 'translateX(20px)';
                                    setTimeout(() => historyItem.remove(), 300);
                                    addLog(`已刪除歷史報告：${rawDate}`, 'warning');
                                } else {
                                    addLog(`刪除失敗: ${res.message}`, "error");
                                }
                            } catch (err) {
                                addLog(`連線失敗: ${err}`, "error");
                            }
                        }
                    };

                    historyList.appendChild(historyItem);
                });
            } else {
                historyList.innerHTML = '<div class="empty-state" style="padding: 40px; text-align: center; color: var(--text-dim);">目前尚無歷史戰略數據</div>';
            }
        } catch (err) {
            historyList.innerHTML = '<div class="error-state">載入失敗</div>';
        }
    }

    async function loadHistoryDetail(date) {
        historyDrawer.classList.remove('active');
        addLog(`正在載入歷史戰略報告: ${date}...`, "system");
        
        try {
            const response = await fetch(`/api/history/${date}`);
            const data = await response.json();
            
            // 清空當前畫面
            newsFeed.innerHTML = '';
            updateGauge(0);
            
            // 顯示報告時間戳
            const reportTimestamp = document.getElementById('report-timestamp');
            if (reportTimestamp) {
                // 解析 2026-03-19_180222 -> 2026-03-19 18:02:22
                const parts = date.split('_');
                const datePart = parts[0];
                let timePart = "";
                if (parts[1]) {
                    timePart = `${parts[1].substring(0,2)}:${parts[1].substring(2,4)}:${parts[1].substring(4,6)}`;
                }
                reportTimestamp.innerHTML = `<i class="fas fa-history" style="margin-right: 4px;"></i>${datePart} ${timePart}`;
                reportTimestamp.style.display = 'block';
            }
            
            // 渲染歷史智能
            if (data.intelligence) {
                // 由後往前加，保持最新在上的視覺感
                data.intelligence.forEach(item => addNewsItem(item));
            }
            
            // 渲染歷史決策
            if (data.decision) {
                updateGauge(data.decision.sentiment_score || 0);
                // 更新決策面板
                decisionAction.innerText = data.decision.action;
                targetPosition.innerText = data.decision.target_position;
                decisionNotes.innerText = data.decision.recon_notes;
                aiThought.innerText = `讀取歷史檔案 [${date}] 完成。`;
            }
            
            // 更新分析統計（如果歷史檔案有這個資料）
            if (data.analysis_stats) {
                const stats = data.analysis_stats;
                if (statTotal) statTotal.innerText = stats.total || 0;
                if (statSuccess) statSuccess.innerText = stats.success || 0;
                if (statFailure) statFailure.innerText = stats.failure || 0;
                addLog(`📊 歷史統計: 總計 ${stats.total || 0} / 成功 ${stats.success || 0} / 失敗 ${stats.failure || 0}`, 'scout');
            }
            
            // 恢復量化數據（融資、散戶、VIX）
            if (data.quant_data) {
                updateQuantUI(data.quant_data);
                addLog(`📈 歷史量化數據: 融資 ${data.quant_data.margin_maintenance_ratio || '--'}%, 散戶 ${data.quant_data.retail_long_short_ratio || '--'}, VIX ${data.quant_data.vixtwn || '--'}`, 'scout');
            }
            
            addLog(`✅ 成功載入 ${date} 的歷史盤型。`, "success");
        } catch (err) {
            addLog(`載入詳情失敗: ${err}`, "error");
        }
    }

    // --- 極致自適應：使用 ResizeObserver 動態調整字體 ---
    const scoreVal = document.getElementById('current-score');
    const scoreLbl = document.getElementById('sentiment-flavor');
    const gaugeContainer = document.querySelector('.gauge-container');

    const resizeObserver = new ResizeObserver(entries => {
        for (let entry of entries) {
            const { width, height } = entry.contentRect;
            const size = Math.min(width, height);
            
            // 動態計算字體大小 (根據容器大小的比例)
            scoreVal.style.fontSize = `${size * 0.22}px`;
            scoreLbl.style.fontSize = `${size * 0.06}px`;
            
            // 同時調整 AI 思考泡泡的間距與字體
            const thoughtBubble = document.querySelector('.sentiment-display .ai-thought-bubble');
            if (thoughtBubble) {
                thoughtBubble.style.fontSize = `${Math.max(10, size * 0.05)}px`;
                thoughtBubble.style.marginTop = `${size * 0.05}px`;
            }
        }
    });

    if (gaugeContainer) resizeObserver.observe(gaugeContainer);

    const resizer = document.getElementById('log-resizer');
    const logPanel = document.getElementById('log-panel-container');
    const sentimentDisplay = document.querySelector('.sentiment-display');
    const centerPanel = sentimentDisplay.parentElement;

    let isResizing = false;

    if (resizer) {
    resizer.addEventListener('mousedown', (e) => {
        isResizing = true;
        document.body.style.cursor = 'ns-resize';
        e.preventDefault();
        
        // 第一次點擊時，記錄並固定當前高度，確保後續調整生效
        if (!logPanel.style.height) {
            logPanel.style.height = `${logPanel.clientHeight}px`;
            logPanel.style.flex = "none";
        }
    });

    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        
        const panelRect = centerPanel.getBoundingClientRect();
        const headerHeight = 50; // header 高度
        const offsetY = e.clientY - panelRect.top;
        const newHeight = panelRect.height - offsetY;

        // 限制最小高度為 100px，最高高度為面版總高扣除 header 與情緒面版低標 (150px)
        const minHeight = 100;
        const maxHeight = panelRect.height - 150 - 50; 

        if (newHeight > minHeight && newHeight < maxHeight) {
            logPanel.style.height = `${newHeight}px`;
        }
    });

    document.addEventListener('mouseup', () => {
        isResizing = false;
        document.body.style.cursor = '';
    });
    }

    function updateQuantUI(data) {
        if (!data) return;
        
        const marginEl = document.getElementById('quant-margin');
        const retailEl = document.getElementById('quant-retail');
        const vixEl = document.getElementById('quant-vix');

        if (marginEl) {
            const margin = data.margin_maintenance_ratio || '--';
            marginEl.textContent = margin + ' %';
            // 變色邏輯
            const mVal = parseFloat(margin);
            if (mVal < 140) marginEl.style.color = 'var(--accent-pink)';
            else if (mVal > 165) marginEl.style.color = 'var(--accent-purple)';
            else marginEl.style.color = 'var(--accent-blue)';
        }

        if (retailEl) {
            const retail = data.retail_long_short_ratio || '--';
            retailEl.textContent = retail;
            const rVal = parseFloat(retail);
            if (Math.abs(rVal) > 30) retailEl.style.color = 'var(--accent-pink)';
            else retailEl.style.color = 'var(--accent-blue)';
        }

        if (vixEl) {
            const vix = data.vixtwn || '--';
            vixEl.textContent = vix;
            const vVal = parseFloat(vix);
            if (vVal > 25) vixEl.style.color = 'var(--accent-pink)';
            else vixEl.style.color = 'var(--accent-blue)';
        }
    }

    // ℹ️ openCustomConfirm 已移至 DOMContentLoaded 外部（見檔案最下方）
});

// ═══════════════════════════════════════════════════════════════
// 🌐 全域工具函數 (必須在 DOMContentLoaded 外部，確保 inline onclick 能找到)
// ═══════════════════════════════════════════════════════════════

// 🛡️ 自定義 Promise Confirm（取代瀏覽器醜陋原生彈窗）
window.openCustomConfirm = function(message) {
    console.log("🛠️ 喚起確認彈窗:", message);
    const modal = document.getElementById('custom-confirm-modal');
    const msgEl  = document.getElementById('confirm-message');
    const btnOk  = document.getElementById('confirm-ok');
    const btnCancel = document.getElementById('confirm-cancel');

    if (!modal) {
        console.error("❌ 找不到 custom-confirm-modal 元素");
        return Promise.resolve(window.confirm(message.replace(/<br>/g, '\n')));
    }

    msgEl.innerHTML = message;
    modal.classList.add('show'); // 使用 class 顯示

    return new Promise((resolve) => {
        const cleanup = (val) => {
            console.log("🛡️ 確認對話框結束，結果:", val);
            modal.classList.remove('show'); // 使用 class 隱藏
            btnOk.onclick = null;
            btnCancel.onclick = null;
            modal.onclick = null;
            resolve(val);
        };
        btnOk.onclick     = (e) => { e.stopPropagation(); cleanup(true); };
        btnCancel.onclick = (e) => { e.stopPropagation(); cleanup(false); };
        modal.onclick     = (e) => { if (e.target === modal) cleanup(false); };
    });
};

// ═══════════════════════════════════════════════════════════════
// 📊 正2 (槓桿ETF) 功能邏輯
// ═══════════════════════════════════════════════════════════════

// 台灣常見正2 ETF 列表
const leverage2ETFList = {
    // 正2 槓桿ETF
    "00631L": "期元大S&P 500正2",
    "00633L": "期富邦NASDAQ正2",
    "00636L": "期國泰20年美債正2",
    "00637L": "期元大滬深300正2",
    "00641L": "期富邦印度正2",
    "00646L": "期元大S&P 500正2",
    "00647L": "期元大S&P 500正2",
    "00753L": "期中信300正2",
    "00757L": "期國泰費城半導體正2",
    "00851L": "期國泰20年美債正2",
    "00852L": "期中信關鍵食品正2",
    "00891L": "期中信特選科技指數正2",
    "00900L": "期富邦臺灣創新版正2",
    "00902L": "期群益台灣科技優息正2",
    "00904L": "期元大全球AI浪潮正2",
    "00908L": "期中信半導體供應鏈正2",
    "00913L": "期國泰台灣上市50正2",
    // 1倍 ETF (也常被當作正2持有)
    "00646": "元大S&P 500",
    "00662": "富邦NASDAQ",
    "00850": "期元大台灣高股息",
    "00878": "國泰永續高股息"
};

// 正2 狀態（支援多筆）
let leverage2Items = [];  // [{symbol, name, value}, ...]
let selectedLeverage2Index = -1; // 選中的索引

// 初始化正2功能
function initLeverage2() {
    const btnAddLeverage2 = document.getElementById('btn-add-leverage2');
    const leverage2Modal = document.getElementById('leverage2-modal');
    const closeBtn = document.getElementById('close-leverage2');
    const btnCancel = document.getElementById('leverage2-cancel');
    const btnConfirm = document.getElementById('leverage2-confirm');
    const newSymbolInput = document.getElementById('new-leverage2-symbol');
    const newNameInput = document.getElementById('new-leverage2-name');
    const newValueInput = document.getElementById('new-leverage2-value');
    const btnAddItem = document.getElementById('btn-add-leverage2-item');
    const symbolSuggestions = document.getElementById('leverage2-symbol-suggestions');
    
    // 點擊新增按鈕
    if (btnAddLeverage2) {
        btnAddLeverage2.onclick = () => {
            renderLeverage2List();
            leverage2Modal.style.display = 'flex';
            leverage2Modal.classList.add('show');
        };
    }
    
    // 關閉
    if (closeBtn) {
        closeBtn.onclick = () => {
            leverage2Modal.style.display = 'none';
            leverage2Modal.classList.remove('show');
        };
    }
    
    // 取消
    if (btnCancel) {
        btnCancel.onclick = () => {
            leverage2Modal.style.display = 'none';
            leverage2Modal.classList.remove('show');
        };
    }
    
    // 確認
    if (btnConfirm) {
        btnConfirm.onclick = () => {
            leverage2Modal.style.display = 'none';
            leverage2Modal.classList.remove('show');
            updateLeverage2Display();
            updateAssetCalculations();
            saveSettings();
        };
    }
    
    // 代號輸入建議
    if (newSymbolInput) {
        newSymbolInput.oninput = () => {
            const query = newSymbolInput.value.trim().toUpperCase();
            if (!query) {
                if (symbolSuggestions) symbolSuggestions.style.display = 'none';
                return;
            }
            
            // 搜尋正2 ETF 列表
            const entries = Object.entries(leverage2ETFList);
            const matches = entries.filter(([sym, name]) => 
                sym.includes(query) || name.includes(query)
            ).slice(0, 8);
            
            if (matches.length > 0) {
                symbolSuggestions.innerHTML = matches.map(([sym, name]) => `
                    <div onclick="selectLeverage2Symbol('${sym}', '${name}')" style="padding: 8px 12px; cursor: pointer; border-bottom: 1px solid rgba(255,255,255,0.05); color: #fff; font-size: 12px;">
                        <span style="color: #f59e0b; font-weight: 700;">${sym}</span>
                        <span style="color: #888; margin-left: 8px;">${name}</span>
                    </div>
                `).join('');
                symbolSuggestions.style.display = 'block';
                
                // 自動帶入第一個名稱
                if (newNameInput && matches[0]) {
                    newNameInput.value = matches[0][1];
                }
            } else {
                if (symbolSuggestions) symbolSuggestions.style.display = 'none';
            }
        };
        
        // 點擊外部關閉建議
        document.addEventListener('mousedown', function closeLev2Suggestions(e) {
            if (!newSymbolInput.contains(e.target) && (!symbolSuggestions || !symbolSuggestions.contains(e.target))) {
                if (symbolSuggestions) symbolSuggestions.style.display = 'none';
                document.removeEventListener('mousedown', closeLev2Suggestions);
            }
        });
    }
    
    // 添加按鈕
    if (btnAddItem) {
        btnAddItem.onclick = () => {
            const symbol = newSymbolInput.value.trim().toUpperCase();
            const nameInput = newNameInput.value.trim();
            const value = parseFloat(newValueInput.value) || 0;
            
            if (!symbol) {
                newSymbolInput.style.borderColor = '#ef4444';
                return;
            }
            newSymbolInput.style.borderColor = '';
            
            // 使用輸入的名稱，若為空則自動產生
            const name = nameInput || leverage2ETFList[symbol] || symbol;
            leverage2Items.push({ symbol, name, value });
            renderLeverage2List();
            saveSettings();
            
            // 清空輸入
            newSymbolInput.value = '';
            newNameInput.value = '';
            newValueInput.value = '';
            newSymbolInput.focus();
        };
    }
    
    // Enter 鍵新增
    if (newSymbolInput && newValueInput) {
        newValueInput.onkeydown = (e) => {
            if (e.key === 'Enter' && btnAddItem) btnAddItem.click();
        };
    }
}

// 渲染正2列表
function renderLeverage2List() {
    const list = document.getElementById('leverage2-list');
    if (!list) return;
    
    if (leverage2Items.length === 0) {
        selectedLeverage2Index = -1;
        list.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-dim); font-size: 11px;">尚無正2資料</div>';
        return;
    }
    
    list.innerHTML = leverage2Items.map((item, index) => {
        const displayName = item.name || leverage2ETFList[item.symbol] || item.symbol;
        const isSelected = index === selectedLeverage2Index;
        return `
        <div onclick="selectLeverage2(${index})" style="
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            padding: 8px 12px; 
            border-bottom: 1px solid rgba(255,255,255,0.05); 
            background: ${isSelected ? 'rgba(245, 158, 11, 0.25)' : (index % 2 === 0 ? 'rgba(255,255,255,0.02)' : 'transparent')}; 
            cursor: pointer;
            transition: background 0.15s;
            border-left: 3px solid ${isSelected ? '#f59e0b' : 'transparent'};
        ">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="color: #555; font-size: 10px; min-width: 18px;">${index + 1}</span>
                <div>
                    <div style="color: #fff; font-size: 12px; font-weight: 700;">${item.symbol}</div>
                    <div style="color: #f59e0b; font-size: 10px; opacity: 0.8;">${displayName}</div>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <input type="number" value="${item.value}" onclick="event.stopPropagation()" onchange="updateLeverage2Value(${index}, this.value)" style="
                    width: 100px; 
                    background: rgba(0,0,0,0.3); 
                    border: 1px solid rgba(245, 158, 11, 0.3); 
                    color: #f59e0b; 
                    padding: 4px 8px; 
                    border-radius: 4px; 
                    font-size: 12px; 
                    font-weight: 700;
                    text-align: right;
                ">
                <button onclick="event.stopPropagation(); removeLeverage2Item(${index})" style="background: transparent; border: none; color: #ef4444; cursor: pointer; padding: 5px;">
                    <i class="fas fa-trash-alt"></i>
                </button>
            </div>
        </div>
    `}).join('');
}

window.selectLeverage2 = (index) => {
    selectedLeverage2Index = index;
    renderLeverage2List();
};

window.updateLeverage2Value = (index, value) => {
    leverage2Items[index].value = parseFloat(value) || 0;
    saveSettings();
};

window.moveLeverage2Up = () => {
    if (selectedLeverage2Index > 0) {
        const temp = leverage2Items[selectedLeverage2Index];
        leverage2Items[selectedLeverage2Index] = leverage2Items[selectedLeverage2Index - 1];
        leverage2Items[selectedLeverage2Index - 1] = temp;
        selectedLeverage2Index--;
        renderLeverage2List();
    }
};

window.moveLeverage2Down = () => {
    if (selectedLeverage2Index >= 0 && selectedLeverage2Index < leverage2Items.length - 1) {
        const temp = leverage2Items[selectedLeverage2Index];
        leverage2Items[selectedLeverage2Index] = leverage2Items[selectedLeverage2Index + 1];
        leverage2Items[selectedLeverage2Index + 1] = temp;
        selectedLeverage2Index++;
        renderLeverage2List();
    }
};

// 開啟正2表單
function openLeverage2Form(index) {
    const formModal = document.getElementById('leverage2-form-modal');
    const formSymbol = document.getElementById('form-leverage2-symbol');
    const formValue = document.getElementById('form-leverage2-value');
    const formTitle = document.getElementById('leverage2-form-title');
    const btnSave = document.getElementById('form-leverage2-save');
    const btnCancel = document.getElementById('form-leverage2-cancel');
    const leverage2Suggestions = document.getElementById('leverage2-suggestions');
    
    const isEdit = index !== null && leverage2Items[index];
    
    // 填充資料
    formTitle.textContent = isEdit ? '編輯' : '新增';
    formSymbol.value = isEdit ? leverage2Items[index].symbol : '';
    formValue.value = isEdit ? leverage2Items[index].value : '';
    
    // 顯示
    formModal.classList.add('show');
    formSymbol.focus();
    
    // 代號輸入建議
    formSymbol.oninput = () => {
        const query = formSymbol.value.trim().toUpperCase();
        if (!query) {
            leverage2Suggestions.style.display = 'none';
            return;
        }
        
        // 搜尋正2 ETF 列表
        const entries = Object.entries(leverage2ETFList);
        const matches = entries.filter(([sym, name]) => 
            sym.includes(query) || name.includes(query)
        ).slice(0, 8);
        
        if (matches.length > 0) {
            leverage2Suggestions.innerHTML = matches.map(([sym, name]) => `
                <div onclick="selectLeverage2Suggestion('${sym}', '${name}')" style="padding: 8px 12px; cursor: pointer; border-bottom: 1px solid rgba(255,255,255,0.05); color: #fff; font-size: 12px;">
                    <span style="color: #f59e0b; font-weight: 700;">${sym}</span>
                    <span style="color: #888; margin-left: 8px;">${name}</span>
                </div>
            `).join('');
            leverage2Suggestions.style.display = 'block';
        } else {
            leverage2Suggestions.style.display = 'none';
        }
    };
    
    // 點擊外部關閉建議
    document.addEventListener('mousedown', function closeLeverage2Suggestions(e) {
        if (!formSymbol.contains(e.target) && !leverage2Suggestions.contains(e.target)) {
            leverage2Suggestions.style.display = 'none';
            document.removeEventListener('mousedown', closeLeverage2Suggestions);
        }
    });
    
    // 儲存
    btnSave.onclick = () => {
        const symbol = formSymbol.value.trim().toUpperCase();
        const value = parseFloat(formValue.value) || 0;
        
        if (!symbol) {
            formSymbol.style.borderColor = '#ef4444';
            return;
        }
        formSymbol.style.borderColor = '';
        
        // 從列表取得名稱，若沒有則用 symbol
        const name = leverage2ETFList[symbol] || symbol;
        
        if (isEdit) {
            leverage2Items[index] = { symbol, name, value };
        } else {
            leverage2Items.push({ symbol, name, value });
        }
        
        formModal.classList.remove('show');
        renderLeverage2List();
        updateLeverage2Display(); // 強制觸發重算與 UI 更新
        saveSettings();
    };
    
    // 取消
    btnCancel.onclick = () => {
        formModal.classList.remove('show');
    };
}

// 刪除正2項目
function removeLeverage2Item(index) {
    leverage2Items.splice(index, 1);
    if (selectedLeverage2Index >= leverage2Items.length) {
        selectedLeverage2Index = leverage2Items.length - 1;
    }
    renderLeverage2List();
    updateLeverage2Display(); // 強制觸發重算與同步更新
    saveSettings();
}

// 更新正2顯示
function updateLeverage2Display() {
    const display = document.getElementById('leverage2-display');
    if (!display) return;
    
    const totalValue = leverage2Items.reduce((sum, item) => sum + item.value, 0);
    
    if (leverage2Items.length > 0) {
        display.classList.remove('hidden');
        display.classList.add('show');
        const info = document.getElementById('leverage2-info');
        const value = document.getElementById('leverage2-value');
        if (info) {
            info.textContent = leverage2Items.length === 1 
                ? `${leverage2Items[0].symbol} 曝險加權`
                : `${leverage2Items.length} 筆正2 (加權曝險)`;
        }
        if (value) value.textContent = '$' + totalValue.toLocaleString();
    } else {
        display.classList.remove('show');
        display.classList.add('hidden');
    }
    
    // 更新外部顯示的總值
    const mainDisplay = document.getElementById('leverage2-main-value');
    if (mainDisplay) {
        mainDisplay.textContent = totalValue > 0 ? '$' + totalValue.toLocaleString() : '--';
    }
    
    // 🆕 同步更新曝險市值和 Beta
    updateAssetCalculations();
    
    // 🆕 更新迷你清單
    renderLeverage2MiniList();
}

// 取得正2總市值
function getLeverage2Total() {
    return leverage2Items.reduce((sum, item) => sum + item.value, 0);
}

// 移除正2
function removeLeverage2() {
    leverage2Items = [];
    updateLeverage2Display();
    updateAssetCalculations();
    saveSettings();
    renderLeverage2MiniList();
}

// 展開/收折正2清單
window.toggleLeverage2List = () => {
    const listEl = document.getElementById('leverage2-list-mini');
    const iconEl = document.getElementById('leverage2-toggle-icon');
    if (!listEl) return;
    
    if (listEl.style.display === 'none') {
        listEl.style.display = 'block';
        if (iconEl) iconEl.className = 'fas fa-chevron-up';
        renderLeverage2MiniList();
    } else {
        listEl.style.display = 'none';
        if (iconEl) iconEl.className = 'fas fa-chevron-down';
    }
};

// 渲染迷你正2清單
function renderLeverage2MiniList() {
    const listEl = document.getElementById('leverage2-list-mini');
    if (!listEl) return;
    
    if (leverage2Items.length === 0) {
        listEl.innerHTML = '<div style="text-align: center; color: var(--text-dim); font-size: 10px; padding: 8px;">尚無正2資料</div>';
        return;
    }
    
    listEl.innerHTML = leverage2Items.map((item, index) => {
        const displayName = item.name || leverage2ETFList[item.symbol] || item.symbol;
        return `
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 10px;">
            <div>
                <span style="color: #fff; font-weight: 700;">${item.symbol}</span>
                <span style="color: #888; margin-left: 4px;">${displayName}</span>
            </div>
            <div style="display: flex; align-items: center; gap: 6px;">
                <span style="color: #f59e0b;">$${item.value.toLocaleString()}</span>
                <button onclick="event.stopPropagation(); removeLeverage2Item(${index})" style="background: transparent; border: none; color: #ef4444; cursor: pointer; padding: 2px; font-size: 9px;">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `}).join('');
}

// ═══════════════════════════════════════════════════════════════
// 🖱️ 全域自定義右鍵選單邏輯
// ═══════════════════════════════════════════════════════════════
const contextMenu = document.getElementById('custom-context-menu');

window.addEventListener('contextmenu', (e) => {
    e.preventDefault(); // 🛑 攔截原生選單
    
    // 取得滑鼠座標
    let left = e.pageX;
    let top = e.pageY;
    
    // 防溢出處理
    const menuWidth = 180;
    const menuHeight = 150;
    const windowWidth = window.innerWidth;
    const windowHeight = window.innerHeight;

    if (left + menuWidth > windowWidth) left = left - menuWidth;
    if (top + menuHeight > windowHeight) top = top - menuHeight;

    if (contextMenu) {
        contextMenu.style.top = `${top}px`;
        contextMenu.style.left = `${left}px`;
        contextMenu.style.display = 'block';
    }
});

// 點擊任何地方關閉選單
window.addEventListener('click', (e) => {
    if (contextMenu) contextMenu.style.display = 'none';
});

// ═══════════════════════════════════════════════════════════════
// 📖 詞庫編輯器邏輯
// ═══════════════════════════════════════════════════════════════

// 取得 DOM 元素
const lexiconModal = document.getElementById('lexicon-modal');
const btnLexicon = document.getElementById('btn-lexicon');
const closeLexicon = document.getElementById('close-lexicon');
const lexiconCategory = document.getElementById('lexicon-category');
const lexiconWords = document.getElementById('lexicon-words');
const lexiconCount = document.getElementById('lexicon-count');
const btnSaveLexicon = document.getElementById('btn-save-lexicon');
const btnReloadLexicon = document.getElementById('btn-reload-lexicon');
const lexiconQuickAdd = document.getElementById('lexicon-quick-add');
const btnAddPositive = document.getElementById('btn-add-positive');
const btnAddNegative = document.getElementById('btn-add-negative');

// 載入指定分類的詞彙（需在初始化之前定義）
async function loadLexiconCategory() {
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
            }
        }
        if (lexiconCount) {
            lexiconCount.textContent = `${(data.words || []).length} 個詞`;
        }
    } catch (err) {
        if (lexiconWords) lexiconWords.value = `# 載入失敗: ${err}`;
        if (lexiconCount) lexiconCount.textContent = '0 個詞';
    }
}

// 開啟詞庫編輯器
if (btnLexicon) {
    btnLexicon.onclick = () => {
        lexiconModal.classList.add('show');
        loadLexiconCategory();
    };
}

// 關閉詞庫編輯器
if (closeLexicon) {
    closeLexicon.onclick = () => {
        lexiconModal.classList.remove('show');
    };
}

// 點擊背景關閉
if (lexiconModal) {
    lexiconModal.onclick = (e) => {
        if (e.target === lexiconModal) {
            lexiconModal.classList.remove('show');
        }
    };
}

// 切換分類時載入該分類的詞彙
if (lexiconCategory) {
    lexiconCategory.onchange = loadLexiconCategory;
}

// 儲存詞庫
if (btnSaveLexicon) {
    btnSaveLexicon.onclick = async () => {
        const category = lexiconCategory ? lexiconCategory.value : 'bullish_extreme';
        const wordsText = lexiconWords ? lexiconWords.value : '';
        
        // 解析詞彙（每行一個）
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
            
            const result = await response.json();
            
            if (result.status === 'success') {
                addLog(`✅ 詞庫已儲存: ${result.message}`, 'success');
                loadLexiconCategory(); // 重新載入
            } else {
                addLog(`❌ 儲存失敗: ${result.message}`, 'error');
            }
        } catch (err) {
            addLog(`❌ 儲存失敗: ${err}`, 'error');
        }
    };
}

// 重新載入詞庫
if (btnReloadLexicon) {
    btnReloadLexicon.onclick = loadLexiconCategory;
}

// 快速添加詞彙
if (btnAddPositive) {
    btnAddPositive.onclick = () => quickAddWord('positive');
}

if (btnAddNegative) {
    btnAddNegative.onclick = () => quickAddWord('negative');
}

// Enter 鍵快速添加
if (lexiconQuickAdd) {
    lexiconQuickAdd.onkeypress = (e) => {
        if (e.key === 'Enter') {
            quickAddWord('neutral');
        }
    };
}

function quickAddWord(type) {
    if (!lexiconQuickAdd || !lexiconWords || !lexiconCount) return;
    
    const word = lexiconQuickAdd.value.trim();
    if (!word) return;
    
    let current = lexiconWords.value;
    const prefix = type === 'positive' ? '🔴' : (type === 'negative' ? '🔵' : '');
    const line = prefix ? `${prefix} ${word}` : word;
    
    if (current && !current.endsWith('\n')) {
        current += '\n';
    }
    lexiconWords.value = current + line;
    lexiconCount.textContent = `${lexiconWords.value.split('\n').filter(w => w.trim()).length} 個詞`;
    
    lexiconQuickAdd.value = '';
    lexiconQuickAdd.focus();
}

// 👁️ 標的管理邏輯 (Targets Management)
// 🛡️ 註：targetStockDataList 現由外部 static/js/stocks_lookup.js 提供 (全量庫)
// 如果外部庫未載入，則使用基本兜底
if (typeof targetStockDataList === 'undefined') {
    window.targetStockDataList = { "^TWII": "台股大盤", "2330.TW": "台積電" };
}

const btnTargets = document.getElementById('btn-targets');
const targetsModal = document.getElementById('targets-modal');
const closeTargets = document.getElementById('close-targets');
const btnSaveTargets = document.getElementById('btn-save-targets');
const btnAddNewTarget = document.getElementById('btn-add-new-target');
const targetsListContainer = document.getElementById('targets-list-container');
const backtestSymbolSelector = document.getElementById('backtest-symbol');
const newTargetName = document.getElementById('new-target-name');
const newTargetSymbol = document.getElementById('new-target-symbol');
const targetSuggestions = document.getElementById('target-suggestions');

let currentSelectedIndex = -1; // 追蹤鍵盤選中的建議索引
let currentTargets = [];

async function loadTargets() {
    try {
        const resp = await fetch('/api/targets');
        const data = await resp.json();
        currentTargets = data.targets || [];
        updateBacktestSymbolDropdown(); // 同步到選單
        renderTargetsList();
        console.log('[標的] 載入成功:', currentTargets.length, '筆');
    } catch (e) {
        console.error('[標的] 載入失敗:', e);
    }
}

// 🆕 同步回測下拉選單（同時更新抽屜和第五欄面板）
function updateBacktestSymbolDropdown() {
    if (backtestSymbolSelector) {
        const currentVal = backtestSymbolSelector.value;
        backtestSymbolSelector.innerHTML = '';
        currentTargets.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t.symbol;
            opt.textContent = `${t.name} (${t.symbol})`;
            backtestSymbolSelector.appendChild(opt);
        });
        // 恢復之前的選擇，如果還在的話
        if (currentVal) backtestSymbolSelector.value = currentVal;
    }
    
    // 同步更新第五欄面板的 select
    const inlineSelect = document.getElementById('backtest-symbol-inline');
    if (inlineSelect) {
        const currentValInline = inlineSelect.value;
        inlineSelect.innerHTML = '';
        currentTargets.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t.symbol;
            opt.textContent = `${t.name} (${t.symbol})`;
            inlineSelect.appendChild(opt);
        });
        // 恢復之前的選擇，如果還在的話
        if (currentValInline && currentTargets.find(t => t.symbol === currentValInline)) {
            inlineSelect.value = currentValInline;
        }
    }
}

let selectedTargetIndex = -1; // 選中的索引

function renderTargetsList() {
    if (!targetsListContainer) return;
    
    if (currentTargets.length === 0) {
        selectedTargetIndex = -1;
        targetsListContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-dim); font-size: 11px;">尚未設定標的</div>';
        return;
    }
    
    targetsListContainer.innerHTML = currentTargets.map((t, index) => `
        <div onclick="selectTarget(${index})" data-index="${index}" style="
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            padding: 8px 12px; 
            border-bottom: 1px solid rgba(255,255,255,0.05); 
            background: ${index === selectedTargetIndex ? 'rgba(168, 85, 247, 0.2)' : (index % 2 === 0 ? 'rgba(255,255,255,0.02)' : 'transparent')}; 
            cursor: pointer;
            transition: background 0.15s;
            border-left: 3px solid ${index === selectedTargetIndex ? '#a855f7' : 'transparent'};
        ">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="color: #555; font-size: 10px; min-width: 18px;">${index + 1}</span>
                <div>
                    <div style="color: #fff; font-size: 12px; font-weight: 700;">${t.name}</div>
                    <div style="color: #a855f7; font-size: 10px; opacity: 0.8;">${t.symbol}</div>
                </div>
            </div>
            <button onclick="event.stopPropagation(); deleteTarget(${index})" style="background: transparent; border: none; color: #ef4444; cursor: pointer; padding: 5px;">
                <i class="fas fa-trash-alt"></i>
            </button>
        </div>
    `).join('');
    
    updateBacktestSymbolDropdown();
}

window.selectTarget = (index) => {
    selectedTargetIndex = index;
    renderTargetsList();
};

window.deleteTarget = (index) => {
    currentTargets.splice(index, 1);
    if (selectedTargetIndex >= currentTargets.length) {
        selectedTargetIndex = currentTargets.length - 1;
    }
    renderTargetsList();
};

window.moveTargetUp = () => {
    if (selectedTargetIndex > 0) {
        const temp = currentTargets[selectedTargetIndex];
        currentTargets[selectedTargetIndex] = currentTargets[selectedTargetIndex - 1];
        currentTargets[selectedTargetIndex - 1] = temp;
        selectedTargetIndex--;
        renderTargetsList();
    }
};

window.moveTargetDown = () => {
    if (selectedTargetIndex >= 0 && selectedTargetIndex < currentTargets.length - 1) {
        const temp = currentTargets[selectedTargetIndex];
        currentTargets[selectedTargetIndex] = currentTargets[selectedTargetIndex + 1];
        currentTargets[selectedTargetIndex + 1] = temp;
        selectedTargetIndex++;
        renderTargetsList();
    }
};

if (btnTargets) {
    btnTargets.onclick = () => {
        targetsModal.style.display = 'flex';
        targetsModal.classList.add('show');
        renderTargetsList();
        if (newTargetSymbol) setTimeout(() => newTargetSymbol.focus(), 100);
    };
}

if (closeTargets) {
    closeTargets.onclick = () => {
        targetsModal.style.display = 'none';
        targetsModal.classList.remove('show');
    };
}

if (btnAddNewTarget) {
    btnAddNewTarget.onclick = () => {
        const name = newTargetName ? newTargetName.value.trim() : '';
        const symbol = newTargetSymbol ? newTargetSymbol.value.trim().toUpperCase() : '';
        
        if (!name || !symbol) {
            addLog('⚠️ 請輸入名稱與代號', 'warning');
            return;
        }
        
        currentTargets.push({ name, symbol });
        renderTargetsList();
        
        if (newTargetName) newTargetName.value = '';
        if (newTargetSymbol) newTargetSymbol.value = '';
        if (newTargetName) newTargetName.focus();
    };
}

// 🆕 代號輸入時自動產生名稱 & 顯示建議列表
if (newTargetSymbol) {
    newTargetSymbol.oninput = () => {
        const query = newTargetSymbol.value.trim().toUpperCase();
        currentSelectedIndex = -1; // 重置選中狀態
        
        if (!query) {
            if (targetSuggestions) targetSuggestions.style.display = 'none';
            return;
        }

        // 1. 搜尋建議列表 (支援代號或名稱搜尋)
        const entries = Object.entries(targetStockDataList);
        const matches = [];
        for (const [sym, name] of entries) {
            if (sym.includes(query) || name.includes(query)) {
                matches.push({ sym, name });
                if (matches.length >= 10) break; // 修改顯示數量，維持畫面簡化
            }
        }

        if (matches.length > 0) {
            targetSuggestions.innerHTML = matches.map((m, idx) => `
                <div class="suggestion-item" data-idx="${idx}" onclick="selectSuggestion('${m.sym}', '${m.name}')">
                    <span class="sym">${m.sym}</span>
                    <span class="name">${m.name}</span>
                </div>
            `).join('');
            targetSuggestions.style.display = 'block';
            
            // 自動帶入第一個名稱 (輔助顯示，不強迫修改 Input)
            if (newTargetName) newTargetName.value = matches[0].name;
        } else {
            targetSuggestions.style.display = 'none';
        }
    };

    // 鍵盤導航 (上下鍵與 Enter)
    newTargetSymbol.onkeydown = (e) => {
        const items = targetSuggestions ? targetSuggestions.querySelectorAll('.suggestion-item') : [];
        
        if (targetSuggestions && targetSuggestions.style.display !== 'none' && items.length > 0) {
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                currentSelectedIndex = (currentSelectedIndex + 1) % items.length;
                updateSuggestionHighlight(items);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                currentSelectedIndex = (currentSelectedIndex - 1 + items.length) % items.length;
                updateSuggestionHighlight(items);
            } else if (e.key === 'Enter') {
                if (currentSelectedIndex >= 0) {
                    e.preventDefault();
                    const activeItem = items[currentSelectedIndex];
                    // 模擬點擊選擇
                    activeItem.click();
                } else {
                    // 如果沒選中，看看 Input 有沒有值
                    if (newTargetSymbol.value.trim() && btnAddNewTarget) {
                        btnAddNewTarget.click();
                    }
                }
                targetSuggestions.style.display = 'none';
            } else if (e.key === 'Escape') {
                targetSuggestions.style.display = 'none';
            }
        } else if (e.key === 'Enter') {
            if (btnAddNewTarget) btnAddNewTarget.click();
        }
    };

    // 點擊外部關閉顯示框
    document.addEventListener('mousedown', (e) => {
        if (targetSuggestions && !newTargetSymbol.contains(e.target) && !targetSuggestions.contains(e.target)) {
            targetSuggestions.style.display = 'none';
        }
    });
}

function updateSuggestionHighlight(items) {
    items.forEach((item, idx) => {
        if (idx === currentSelectedIndex) {
            item.classList.add('active');
            item.scrollIntoView({ block: 'nearest' });
        } else {
            item.classList.remove('active');
        }
    });
}

// 選擇正2代號建議的全域函式
window.selectLeverage2Symbol = (symbol, name) => {
    const symInput = document.getElementById('new-leverage2-symbol');
    const nameInput = document.getElementById('new-leverage2-name');
    const suggestions = document.getElementById('leverage2-symbol-suggestions');
    if (symInput) symInput.value = symbol;
    if (nameInput) nameInput.value = name;
    if (suggestions) suggestions.style.display = 'none';
};

// 選擇建議項目的全域函式
window.selectSuggestion = (symbol, name) => {
    if (newTargetSymbol) newTargetSymbol.value = symbol;
    if (newTargetName) newTargetName.value = name;
    if (targetSuggestions) targetSuggestions.style.display = 'none';
    
    // 直接觸發添加按鈕
    if (btnAddNewTarget) btnAddNewTarget.click();
};

if (btnSaveTargets) {
    btnSaveTargets.onclick = async () => {
        // 防止重複點擊
        if (btnSaveTargets.disabled) return;
        
        const originalText = btnSaveTargets.innerHTML;
        const originalBg = btnSaveTargets.style.background;
        try {
            btnSaveTargets.disabled = true;
            btnSaveTargets.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> 儲存中...';
            
            const resp = await fetch('/api/targets', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ targets: currentTargets })
            });
            
            if (!resp.ok) {
                throw new Error(`HTTP ${resp.status}: ${resp.statusText}`);
            }
            
            const res = await resp.json();
            console.log('[標的] 儲存結果:', res);
            
            if (res.status === 'success') {
                btnSaveTargets.style.background = '#10b981';
                btnSaveTargets.innerHTML = '<i class="fas fa-check"></i> 成功';
                addLog('✅ 觀測標的已成功更新', 'success');
                
                setTimeout(() => {
                    targetsModal.classList.remove('show');
                    setTimeout(() => targetsModal.style.display = 'none', 300);
                    loadTargets();
                }, 600);
            } else {
                throw new Error(res.message || '未知錯誤');
            }
        } catch (e) {
            console.error('[標的] 儲存失敗:', e);
            addLog('❌ 儲存失敗: ' + e.message, 'error');
            btnSaveTargets.style.background = '#ef4444';
            btnSaveTargets.innerHTML = '<i class="fas fa-times"></i> 失敗';
        } finally {
            setTimeout(() => {
                btnSaveTargets.style.background = originalBg;
                btnSaveTargets.innerHTML = '<i class="fas fa-save"></i> 儲存變更';
                btnSaveTargets.disabled = false;
            }, 1500);
        }
    };
}

if (targetsModal) {
    targetsModal.onclick = (e) => {
        if (e.target === targetsModal) {
            targetsModal.style.display = 'none';
            targetsModal.classList.remove('show');
        }
    };
}
