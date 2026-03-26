import json
from datetime import datetime

# 導入 13 個獨立的偵察特工 (One Site, One PY)
from core.ptt_scout import PttStockScout
from core.anue_scout import AnueScout
from core.yahoo_scout import YahooScout
from core.udn_scout import UdnScout
from core.wantgoo_scout import WantGooScout
from core.moneydj_scout import MoneyDjScout
from core.ctee_scout import CteeScout
from core.tianxia_scout import TianxiaScout
from core.caixin_scout import CaixinScout
from core.cmoney_scout import CmoneyScout
from core.ettoday_scout import EttodayScout
from core.tvbs_scout import TvbsScout
from core.cna_scout import CnaScout

def run_news_recon():
    """
    Step 1 新聞廣域偵察任務 (Orchestrator V2)。
    全面模組化架構：13 個偵察對象對應 13 個獨立爬蟲 PY。
    """
    intelligence = []
    source_status = {}
    
    # 定義要執行的特工清單
    scouts = [
        ('ptt', PttStockScout(), 'scrape_latest_posts', {'pages': 1, 'min_pushes': 10}),
        ('anue', AnueScout(), 'scrape_latest_news', {'limit': 8}),
        ('yahoo', YahooScout(), 'scrape_latest_news', {'limit': 6}),
        ('udn', UdnScout(), 'scrape_latest_news', {'limit': 6}),
        ('wantgoo', WantGooScout(), 'scrape_latest_news', {'limit': 6}),
        ('moneydj', MoneyDjScout(), 'scrape_latest_news', {'limit': 6}),
        ('ctee', CteeScout(), 'scrape_latest_news', {'limit': 6}),
        ('tianxia', TianxiaScout(), 'scrape_latest_news', {'limit': 6}),
        ('caixin', CaixinScout(), 'scrape_latest_news', {'limit': 6}),
        ('cmoney', CmoneyScout(), 'scrape_latest_news', {'limit': 6}),
        ('ettoday', EttodayScout(), 'scrape_latest_news', {'limit': 6}),
        ('tvbs', TvbsScout(), 'scrape_latest_news', {'limit': 6}),
        ('cna', CnaScout(), 'scrape_latest_news', {'limit': 6}),
    ]

    for source_id, scout_obj, method_name, kwargs in scouts:
        try:
            print(f"🕵️ 正在啟動 {source_id} 偵察特工...")
            method = getattr(scout_obj, method_name)
            results = method(**kwargs)
            
            # 標準化處理 (確保欄位名稱一致性)
            for item in results:
                if 'link' in item and 'url' not in item:
                    item['url'] = item.pop('link')
            
            intelligence.extend(results)
            source_status[source_id] = {'success': True, 'count': len(results)}
        except Exception as e:
            print(f"❌ {source_id} 偵察失敗: {str(e)}")
            source_status[source_id] = {'success': False, 'error': str(e), 'count': 0}

    source_failures = [
        f"情報來源:{src}"
        for src, status in source_status.items()
        if not status.get('success')
    ]

    print(f"[OK] 13 據點廣域偵察完畢：共獲取 {len(intelligence)} 則情報。")
    
    return {
        "intelligence": intelligence,
        "source_status": source_status,
        "source_failures": source_failures
    }

if __name__ == "__main__":
    res = run_news_recon()
    print(json.dumps(res, ensure_ascii=False, indent=2))
