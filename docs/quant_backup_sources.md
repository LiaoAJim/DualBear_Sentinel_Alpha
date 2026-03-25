# Step 3 量化備援來源研究筆記

最後更新: 2026-03-25

這份筆記整理目前對 `Step 3 哨兵決策判斷` 量化來源的研究狀態，避免日後重複逆向。

## 目前正式採用

- 台灣 VIX
  - 主來源: 台期所 `vixMinNew`
  - 清單頁: `https://www.taifex.com.tw/cht/7/vixMinNew`
  - 實際下載檔: `https://www.taifex.com.tw/cht/7/getVixData?filesname=YYYYMMDD`
  - 目前解析規則: 優先取最後一行 `Last 1 min AVG`
- 台灣 VIX 備援
  - TWSE `MI_VIX`
  - `https://www.twse.com.tw/rwd/zh/indices/MI_VIX?response=json`

## 統一證券研究結果

頁面:

- `https://www.pscnet.com.tw/pscnetStock/menuContent.do?main_id=386032846c000000ccd145898ac293b6&sub_id=38d642081a00000099f12672f4cf7d6e`

已確認的端點線索:

- `/pscnetStock/ajaxInformation.do`
- `/pscnetStock/ajaxEGeneral.do`
- `/pscnetStock/getSearchByKeyword.do`

目前判讀:

- 以上端點偏向客服、站內搜尋、一般內容區塊
- 尚未找到直接對應 `融資維持率` 的公開 API
- `main.js` 主要是站台互動，不像市場數據程式

結論:

- 現階段不建議把統一證券頁面接成正式備援來源

## 凱基證券研究結果

主頁:

- `https://www.kgi.com.tw/zh-tw/product-market/stock-market-overview/tw-stock-market/tw-stock-market-detail?a=B658010E71E243C4A1D6B5F7BE914BDC&b=5D48401A7CE148CD8ABAC965F9B5AFBF`

已確認的公開 API:

- Dropdown API
  - `https://www.kgi.com.tw/api/client/KGISDropdownList/GetDropdownList?sc_lang=zh-TW&sc_site=kgis-zh-tw`

實測可回傳的關鍵分類:

- `b7931c45-ac79-48ac-b7e5-89261ffc5edc` -> 信用交易
- `b658010e-71e2-43c4-a1d6-b5f7be914bdc` -> 盤後分析

信用交易分類目前可拿到的 MoneyDJ iframe URL:

- 融資: `https://kgiweb.moneydj.com/b2brwd/page/rank/chip/0037`
- 融券: `https://kgiweb.moneydj.com/b2brwd/page/rank/chip/0039`
- 資券比: `https://kgiweb.moneydj.com/b2brwd/page/rank/chip/0045`
- 融資使用率: `https://kgiweb.moneydj.com/b2brwd/page/rank/chip/0046`

盤後分析分類目前可拿到的 MoneyDJ iframe URL:

- 信用交易: `https://kgiweb.moneydj.com/b2brwd/page/afterhours/market/0002`

## MoneyDJ SPA 逆向結果

iframe 頁面本身不含數值，資料由 SPA bundle 動態載入:

- bundle
  - `https://kgiweb.moneydj.com/b2brwd/page/js/bundle.8b42ef6e.js?a=1`
- revision
  - `https://kgiweb.moneydj.com/b2brwdCommon/jsondata/revision.rdjjs`

bundle 已確認的關鍵常數:

- API path: `/b2brwdCommon/jsondata/`
- Proxy path: `/b2brwdCommon/proxy/`
- 歷史 XML path: `/b2brwdCommon/{hash}/gethistdata2.xdjxml`

已確認的 hash 規則片段:

- `hash = md5(domain + param.x + "/" + url + ".xdjjson?" + query)`
- 實際抓取時會變成:
  - `/b2brwdCommon/jsondata/{hash前2}/{hash第3-4}/{hash第5-6}/{url}.xdjjson?...&revision=...`

已確認的 sitemap 對照:

- `rank/chip/0037` -> 融資增加排行
- `rank/chip/0045` -> 資券比排行
- `rank/chip/0046` -> 融資使用率排行
- `afterhours/market/0002` -> 信用交易

## 目前卡點

- 雖然已找到 MoneyDJ 的 hash 規則主體
- 但 `rank/chip/0037`、`rank/chip/0046`、`afterhours/market/0002` 對應的完整 request profile 尚未還原
- 目前無法確認:
  - `url` 是否真的是頁面 path 本身
  - `param.x` 是否固定為 sitemap 第二欄 `1`
  - 是否還有隱含參數，例如 `dt`、`type`、`id`、市場代碼

## 建議下一步

若未來要繼續追凱基 / MoneyDJ 備援來源，建議依序做:

1. 直接逆向 bundle 內 `rank` 頁面的 `apis` 或 `requestProfile`
2. 找出 `0037` / `0046` / `0002` 對應的完整 `url + param`
3. 用正確 request profile 重建 hash 後，再驗證 `.xdjjson` 是否可直接讀取
4. 驗證回傳格式是否有市場總覽數值，而不是僅排行列表

## 目前程式上的結論

- 凱基頁面目前可當「研究線索來源」
- 但尚不適合直接列入 `QuantSentimentScout` 正式備援
- `core/quant_scout.py` 目前只保留:
  - 台期所 / TWSE
  - WantGoo
  - 統一 / 凱基靜態探測
  - MacroMicro 探測
