"""
測試量化情報員模組
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import patch, MagicMock
import requests
from core.quant_scout import QuantSentimentScout


class TestQuantSentimentScout:
    """QuantSentimentScout 單元測試"""

    def setup_method(self):
        """每個測試前執行"""
        self.scout = QuantSentimentScout()

    def test_initialization(self):
        """測試初始化"""
        assert self.scout is not None
        assert 'User-Agent' in self.scout.headers

    @patch.object(requests, 'get')
    def test_get_taifex_vix_success(self, mock_get):
        """測試從台期所下載檔成功取得最新台灣 VIX"""
        list_response = MagicMock()
        list_response.status_code = 200
        list_response.text = """
        <table class="table_f">
            <tr><td align="center">2026/03/25</td>
                <td align="center"><input onClick="window.open('getVixData?filesname=20260325')"></td>
            </tr>
        </table>
        """

        data_response = MagicMock()
        data_response.status_code = 200
        data_response.content = (
            "交易日期\t時間(時/分/秒/毫秒)\t臺指選擇權波動率指數\r\n"
            "20260325\t13450000\t\t\t36.31\r\n"
            "20260325\tLast 1 min AVG\t\t\t36.32\r\n"
        ).encode("cp950")

        mock_get.side_effect = [list_response, data_response]

        result = self.scout._get_taifex_vix()
        assert result == 36.32

    @patch.object(requests, 'get')
    def test_get_official_vix_success(self, mock_get):
        """測試成功取得 VIX"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'stat': 'OK',
            'data': [['2024-01-15', '18.52']]
        }
        mock_get.return_value = mock_response

        result = self.scout._get_official_vix()
        assert result == 18.52

    @patch.object(requests, 'get')
    def test_get_official_vix_api_error(self, mock_get):
        """測試 API 錯誤"""
        mock_response = MagicMock()
        mock_response.json.return_value = {'stat': 'ERROR'}
        mock_get.return_value = mock_response

        result = self.scout._get_official_vix()
        # 失敗時返回 None，避免顯示假的預設值
        assert result is None

    @patch.object(requests, 'get')
    def test_get_official_vix_network_error(self, mock_get):
        """測試網路錯誤"""
        mock_get.side_effect = Exception("Network error")

        result = self.scout._get_official_vix()
        # 失敗時返回 None，避免顯示假的預設值
        assert result is None

    @patch.object(requests, 'get')
    def test_fetch_all_indicators(self, mock_get):
        """測試完整指標獲取"""
        # Mock 所有 HTTP 請求
        def mock_requests_get(url, **kwargs):
            mock_response = MagicMock()
            if 'vixMinNew' in url:
                mock_response.status_code = 200
                mock_response.text = "getVixData?filesname=20260325"
            elif 'getVixData' in url:
                mock_response.status_code = 200
                mock_response.content = (
                    "交易日期\t時間(時/分/秒/毫秒)\t臺指選擇權波動率指數\r\n"
                    "20260325\tLast 1 min AVG\t\t\t36.32\r\n"
                ).encode("cp950")
                mock_response.text = ''
            elif 'MI_VIX' in url:
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    'stat': 'OK',
                    'data': [['2024-01-15', '20.5']]
                }
                mock_response.text = ''
            elif 'astock/margin' in url:
                mock_response.status_code = 200
                mock_response.text = '<div>融資維持率</div><div>145.5%</div>'
            elif 'retail-indicator' in url:
                mock_response.status_code = 200
                mock_response.text = '<table><tbody><tr><td>2026/03/25</td><td>33985</td><td>43673</td><td>39637</td><td>5.13</td></tr></tbody></table>'
            else:
                mock_response.status_code = 200
                mock_response.json.return_value = {}
                mock_response.text = ''
            return mock_response

        mock_get.side_effect = mock_requests_get

        with patch('core.quant_scout.VIXScout.fetch', return_value={
            'status': 'success',
            'value': 27.35
        }):
            result = self.scout.fetch_all_indicators()
        
        assert 'timestamp' in result
        assert 'margin_maintenance_ratio' in result
        assert 'retail_long_short_ratio' in result
        assert 'vixtwn' in result
        assert 'vixus' in result
        assert result['margin_maintenance_ratio'] == 145.5
        assert result['retail_long_short_ratio'] == 5.13
        assert result['vixtwn'] == 36.32
        assert result['vixus'] == 27.35
        assert result['_errors'] == {}
        assert result['_sources']['vixtwn'] == 'taifex_vix_download'
        assert result['_sources']['margin_maintenance_ratio'] == 'wantgoo_margin_page'
        assert result['_sources']['retail_long_short_ratio'] == 'wantgoo_retail_page'

    @patch.object(requests, 'get')
    def test_fetch_all_indicators_uses_twse_vix_fallback(self, mock_get):
        """測試台期所失敗時會改用 TWSE API 作為備援"""
        def mock_requests_get(url, **kwargs):
            mock_response = MagicMock()
            if 'vixMinNew' in url:
                mock_response.status_code = 500
                mock_response.text = ''
            elif 'MI_VIX' in url:
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    'stat': 'OK',
                    'data': [['2024-01-15', '20.5']]
                }
                mock_response.text = ''
            elif 'astock/margin' in url:
                mock_response.status_code = 200
                mock_response.text = '<div>融資維持率</div><div>145.5%</div>'
            elif 'retail-indicator' in url:
                mock_response.status_code = 200
                mock_response.text = '<table><tbody><tr><td>2026/03/25</td><td>33985</td><td>43673</td><td>39637</td><td>5.13</td></tr></tbody></table>'
            else:
                mock_response.status_code = 200
                mock_response.text = ''
                mock_response.json.return_value = {}
            return mock_response

        mock_get.side_effect = mock_requests_get

        with patch('core.quant_scout.VIXScout.fetch', return_value={
            'status': 'success',
            'value': 27.35
        }):
            result = self.scout.fetch_all_indicators()

        assert result['vixtwn'] == 20.5
        assert result['_sources']['vixtwn'] == 'twse_mi_vix_api'
        assert result['_attempts']['vixtwn'][0]['source'] == 'taifex_vix_download'
        assert result['_attempts']['vixtwn'][0]['status'] == 'failed'
        assert result['_attempts']['vixtwn'][1]['source'] == 'twse_mi_vix_api'
        assert result['_attempts']['vixtwn'][1]['status'] == 'success'

    @patch.object(requests, 'get')
    def test_margin_failure_returns_none(self, mock_get):
        """測試融資維持率解析失敗時返回 None，而不是假值"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<html><body>no margin data</body></html>'
        mock_get.return_value = mock_response

        result = self.scout._get_wantgoo_margin()
        assert result is None
        assert self.scout.last_errors['margin_maintenance_ratio'] == '頁面可載入，但解析不到融資維持率'

    @patch.object(requests, 'get')
    def test_retail_failure_returns_none(self, mock_get):
        """測試散戶多空比解析失敗時返回 None，而不是假值"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<html><body>no retail data</body></html>'
        mock_get.return_value = mock_response

        result = self.scout._get_wantgoo_retail_ls()
        assert result is None
        assert self.scout.last_errors['retail_long_short_ratio'] == '頁面可載入，但解析不到散戶多空比'

    def test_us_vix_failure_returns_none(self):
        """測試美國 VIX 失敗時返回 None"""
        with patch('core.quant_scout.VIXScout.fetch', return_value={
            'status': 'error',
            'message': 'network'
        }):
            result = self.scout._get_us_vix()
        assert result is None
