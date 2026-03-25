/**
 * DecisionPanel Module
 * Step 3: 哨兵決策判斷 Panel
 * 
 * Responsibilities:
 * - Display decision action (建議操作)
 * - Display target position (建議倉位)
 * - Display quant indicators (融資, 散戶, VIX)
 * - Display recon notes (戰略理由)
 */

const DecisionPanel = (function() {
    'use strict';

    // DOM Elements
    let decisionActionEl = null;
    let targetPositionEl = null;
    let decisionNotesEl = null;
    let quantMarginEl = null;
    let quantRetailEl = null;
    let quantVixEl = null;

    // Default state
    const DEFAULTS = {
        action: '--',
        position: '--',
        notes: '系統持續監控市場脈動中...',
        margin: '--',
        retail: '--',
        vix: '--'
    };

    // Callback for position percentage changes
    let onPositionChangeCallback = null;

    /**
     * Initialize the decision panel
     */
    function init() {
        decisionActionEl = document.getElementById('decision-action');
        targetPositionEl = document.getElementById('target-position');
        decisionNotesEl = document.getElementById('decision-notes');
        quantMarginEl = document.getElementById('quant-margin');
        quantRetailEl = document.getElementById('quant-retail');
        quantVixEl = document.getElementById('quant-vix');

        console.log('[DecisionPanel] Initialized');
        return this;
    }

    /**
     * Reset all values to default state
     */
    function resetToDefaults() {
        updateDecision({
            action: DEFAULTS.action,
            target_position: DEFAULTS.position,
            recon_notes: DEFAULTS.notes
        });
        
        updateQuant({
            margin_maintenance_ratio: null,
            retail_long_short_ratio: null,
            vixtwn: null
        });

        console.log('[DecisionPanel] Reset to defaults');
    }

    /**
     * Update decision display from server data
     * @param {Object} data - Decision data from WebSocket
     * @param {string} data.action - Recommended action
     * @param {string} data.target_position - Target position percentage
     * @param {string} data.recon_notes - Strategy notes
     * @param {number} [data.quant_adjustment] - Quant adjustment percentage
     */
    function updateDecision(data) {
        if (!data) return;

        if (decisionActionEl && data.action !== undefined) {
            decisionActionEl.innerText = data.action;
            
            // Handle error state styling
            if (data.action === "分析失敗") {
                decisionActionEl.style.color = "var(--danger)";
            } else {
                decisionActionEl.style.color = "";
            }
        }

        if (targetPositionEl && data.target_position !== undefined) {
            targetPositionEl.innerText = data.target_position;
            
            if (data.action === "分析失敗") {
                targetPositionEl.style.color = "var(--text-dim)";
            } else {
                targetPositionEl.style.color = "";
            }
        }

        if (decisionNotesEl && data.recon_notes !== undefined) {
            decisionNotesEl.innerText = data.recon_notes;
        }

        // Extract position percentage and trigger callback
        if (data.target_position && onPositionChangeCallback) {
            const match = data.target_position.match(/(\d+)%/);
            if (match) {
                const positionPercent = parseInt(match[1]) / 100;
                onPositionChangeCallback(positionPercent);
            }
        }

        console.log('[DecisionPanel] Updated decision:', data.action, data.target_position);
    }

    /**
     * Update quant indicators display
     * @param {Object} data - Quant data from server
     * @param {number|string} [data.margin_maintenance_ratio] - Margin maintenance ratio
     * @param {number|string} [data.retail_long_short_ratio] - Retail long/short ratio
     * @param {number|string} [data.vixtwn] - VIX TWN value
     */
    function updateQuant(data) {
        if (!data) return;

        // Update margin
        if (quantMarginEl) {
            const margin = data.margin_maintenance_ratio;
            if (margin !== null && margin !== undefined && margin !== '') {
                quantMarginEl.textContent = margin + ' %';
                const mVal = parseFloat(margin);
                if (!isNaN(mVal)) {
                    if (mVal < 140) quantMarginEl.style.color = 'var(--accent-pink)';
                    else if (mVal > 165) quantMarginEl.style.color = 'var(--accent-purple)';
                    else quantMarginEl.style.color = 'var(--accent-blue)';
                }
            } else {
                quantMarginEl.textContent = '--';
                quantMarginEl.style.color = '';
            }
        }

        // Update retail
        if (quantRetailEl) {
            const retail = data.retail_long_short_ratio;
            if (retail !== null && retail !== undefined && retail !== '') {
                quantRetailEl.textContent = retail;
                const rVal = parseFloat(retail);
                if (!isNaN(rVal)) {
                    if (Math.abs(rVal) > 30) quantRetailEl.style.color = 'var(--accent-pink)';
                    else quantRetailEl.style.color = 'var(--accent-blue)';
                }
            } else {
                quantRetailEl.textContent = '--';
                quantRetailEl.style.color = '';
            }
        }

        // Update VIX
        if (quantVixEl) {
            const vix = data.vixtwn;
            if (vix !== null && vix !== undefined && vix !== '') {
                quantVixEl.textContent = vix;
                const vVal = parseFloat(vix);
                if (!isNaN(vVal)) {
                    if (vVal >= 30) quantVixEl.style.color = 'var(--accent-pink)';
                    else if (vVal >= 25) quantVixEl.style.color = '#f59e0b';
                    else if (vVal < 15) quantVixEl.style.color = '#10b981';
                    else quantVixEl.style.color = 'var(--accent-blue)';
                }
            } else {
                quantVixEl.textContent = '--';
                quantVixEl.style.color = '';
            }
        }

        console.log('[DecisionPanel] Updated quant data');
    }

    /**
     * Set callback for position percentage changes
     * @param {Function} callback - Function to call with position percentage (0-1)
     */
    function onPositionChange(callback) {
        onPositionChangeCallback = callback;
    }

    /**
     * Get current decision state
     * @returns {Object} Current decision values
     */
    function getState() {
        return {
            action: decisionActionEl?.innerText || '--',
            position: targetPositionEl?.innerText || '--',
            notes: decisionNotesEl?.innerText || DEFAULTS.notes,
            margin: quantMarginEl?.innerText || '--',
            retail: quantRetailEl?.innerText || '--',
            vix: quantVixEl?.innerText || '--'
        };
    }

    /**
     * Handle WebSocket decision message
     * @param {Object} data - Full decision message from WebSocket
     */
    function handleDecisionMessage(data) {
        updateDecision({
            action: data.action,
            target_position: data.target_position,
            recon_notes: data.recon_notes
        });

        // Update quant if included
        if (data.quant_adjustment !== undefined) {
            console.log('[DecisionPanel] Quant adjustment:', data.quant_adjustment);
        }
    }

    /**
     * Handle WebSocket quant_data message
     * @param {Object} data - Quant data message from WebSocket
     */
    function handleQuantMessage(data) {
        updateQuant(data);
    }

    // Public API
    return {
        init,
        resetToDefaults,
        updateDecision,
        updateQuant,
        onPositionChange,
        getState,
        handleDecisionMessage,
        handleQuantMessage,
        DEFAULTS
    };
})();

// Auto-init when DOM is ready
if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => DecisionPanel.init());
    } else {
        // DOM already loaded, init immediately
        if (document.getElementById('decision-panel')) {
            DecisionPanel.init();
        }
    }
}
