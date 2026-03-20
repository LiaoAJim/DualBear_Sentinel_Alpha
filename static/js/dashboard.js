document.addEventListener('DOMContentLoaded', () => {
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

    // 圓形進度條長度 (2 * PI * R)
    const CIRCUMFERENCE = 282.7;

    function addLog(message, type = 'info') {
        const entry = document.createElement('div');
        const now = new Date();
        const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
        entry.className = `log-entry ${type}`;
        entry.innerHTML = `<span style="opacity: 0.5;">[${timeStr}]</span> ${message}`;
        systemLogs.appendChild(entry);
        systemLogs.scrollTop = systemLogs.scrollHeight;

        // 限制日誌數量
        if (systemLogs.children.length > 200) {
            systemLogs.removeChild(systemLogs.firstChild);
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
        const sourceClass = data.source.toLowerCase().includes('anue') ? 'source-anue' : 'source-ptt';
        const sourceName = data.source;
        
        item.innerHTML = `
            <div class="news-item-header">
                <span class="news-source ${sourceClass}">${sourceName}</span>
                <span class="news-date">${data.date}</span>
            </div>
            <div class="news-title">${data.title}</div>
            ${data.author ? `<div class="news-author"><i class="fas fa-user-circle"></i> ${data.author}</div>` : ''}
        `;
        
        // 增加點擊跳轉功能
        if (data.link) {
            item.style.cursor = 'pointer';
            item.title = "點擊開啟原始網頁";
            item.onclick = () => {
                window.open(data.link, '_blank');
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

    // WebSocket 連接邏輯
    let ws;
    function connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
        
        ws.onopen = () => {
            connectionStatus.classList.remove('disconnect');
            connectionStatus.classList.add('online');
            connectionStatus.querySelector('.status-text').innerText = '系統線上';
            addLog('WebSocket 連線成功', 'success');
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'log') {
                addLog(data.content, data.level || 'info');
            } else if (data.type === 'status') {
                updateStepper(data.step);
            } else if (data.type === 'intelligence') {
                addNewsItem(data.content);
                addLog(`蒐集情報: ${data.content.title}`, 'scout');
            } else if (data.type === 'analysis_start') {
                aiThought.innerText = `正在解析："${data.title}"...`;
                addLog(`AI 分析中: ${data.title}`, 'ai');
            } else if (data.type === 'analysis_result') {
                updateGauge(data.final_score);
                addLog(`最終情緒分數判定: ${data.final_score.toFixed(2)}`, 'success');
            } else if (data.type === 'decision') {
                decisionAction.innerText = data.action;
                targetPosition.innerText = data.target_position;
                decisionNotes.innerText = data.recon_notes;
                aiThought.innerText = "分析任務完成，哨兵持續監報量能中。";
                addLog(`決策生成完成: ${data.action}`, 'success');
                resetRunButton();
            }
        };

        ws.onclose = () => {
            connectionStatus.classList.remove('online');
            connectionStatus.classList.add('disconnect');
            connectionStatus.querySelector('.status-text').innerText = '連線中斷';
            addLog('連線已中斷，正在嘗試重新連線...', 'error');
            resetRunButton(); // 斷線也恢復按鈕防止卡死
            setTimeout(connect, 2000);
        };
    }

    let isRunning = false;

    function resetRunButton() {
        isRunning = false;
        btnRun.disabled = false;
        btnRun.innerHTML = '<i class="fas fa-play"></i> 立即執行';
        btnRun.style.background = ''; // 恢復 CSS 定義的樣式
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
        
        addLog("透過儀表板觸發立即偵察任務...", "system");
        
        try {
            const response = await fetch('/api/run', { method: 'POST' });
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

    async function loadHistoryList() {
        historyList.innerHTML = '<div class="loading-spinner">載入檔案中...</div>';
        try {
            const response = await fetch('/api/history');
            const data = await response.json();
            
            if (data.dates && data.dates.length > 0) {
                historyList.innerHTML = '';
                data.dates.forEach(date => {
                    const item = document.createElement('div');
                    item.className = 'history-item';
                    item.innerHTML = `
                        <span class="date-text">${date}</span>
                        <span class="count-badge">查看報告 <i class="fas fa-chevron-right"></i></span>
                    `;
                    item.onclick = () => loadHistoryDetail(date);
                    historyList.appendChild(item);
                });
            } else {
                historyList.innerHTML = '<div class="empty-state">目前尚無歷史數據</div>';
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
            
            addLog(`✅ 成功載入 ${date} 的歷史盤型。`, "success");
        } catch (err) {
            addLog(`載入詳情失敗: ${err}`, "error");
        }
    }

    connect();
});
