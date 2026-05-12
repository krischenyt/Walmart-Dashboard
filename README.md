# Walmart Sales Dashboard

每日自動抓取 Walmart 訂單 → 存入 Google Sheets → Streamlit Dashboard 視覺化。

## 專案結構

```
walmart-dashboard/
├── app.py                          # Streamlit Dashboard 主程式
├── walmart_api.py                  # Walmart API 串接模組
├── sheets_sync.py                  # Google Sheets 讀寫模組
├── run_daily.py                    # 每日同步腳本
├── requirements.txt
├── .gitignore
├── .github/
│   └── workflows/
│       └── daily_sync.yml          # GitHub Actions 自動排程
└── .streamlit/
    └── secrets.toml.example        # 本機開發設定範本
```

## 快速開始

### 第一步：設定 Google Cloud

1. 前往 [Google Cloud Console](https://console.cloud.google.com)
2. 建立新專案，啟用 **Google Sheets API** 和 **Google Drive API**
3. 建立 Service Account，下載 JSON 金鑰，儲存為 `service_account.json`
4. 建立 Google Sheet，命名為 **Walmart Orders 2026**
5. 把 `service_account.json` 裡的 `client_email` 加入 Google Sheet 的編輯者

### 第二步：本機測試

```bash
# 安裝套件
pip install -r requirements.txt

# 設定環境變數
export WALMART_CLIENT_ID="你的 Client ID"
export WALMART_CLIENT_SECRET="你的 Client Secret"
export GOOGLE_SHEET_ID="你的 Sheet ID"

# 第一次執行：抓最近 30 天資料
python run_daily.py --days 30

# 啟動 Dashboard
streamlit run app.py
```

### 第三步：部署到 GitHub Actions（每日自動同步）

在 GitHub Repo 的 **Settings → Secrets and variables → Actions** 新增以下 Secrets：

| Secret 名稱 | 值 |
|---|---|
| `WALMART_CLIENT_ID` | Walmart API Client ID |
| `WALMART_CLIENT_SECRET` | Walmart API Client Secret |
| `GOOGLE_CREDENTIALS` | `service_account.json` 的完整 JSON 內容 |
| `GOOGLE_SHEET_ID` | Google Sheet 的 ID |

設定完成後，每天 UTC 08:00（台灣時間 16:00）會自動執行同步。  
也可以在 GitHub Actions 頁面手動觸發。

### 第四步：部署 Dashboard 到 Streamlit Cloud（選用）

1. 前往 [streamlit.io/cloud](https://streamlit.io/cloud)，用 GitHub 帳號登入
2. 點 **New app** → 選你的 Repo → 主程式選 `app.py`
3. 在 **Advanced settings → Secrets** 貼入：

```toml
GOOGLE_SHEET_ID = "你的 Sheet ID"
GOOGLE_CREDENTIALS = """
{ 整個 service_account.json 內容貼這裡 }
"""
```

4. 點 Deploy，幾分鐘後得到公開網址

## 環境變數說明

| 變數名稱 | 說明 | 必填 |
|---|---|---|
| `WALMART_CLIENT_ID` | Walmart API Client ID | 同步用 |
| `WALMART_CLIENT_SECRET` | Walmart API Client Secret | 同步用 |
| `GOOGLE_CREDENTIALS` | Service Account JSON 字串 | 必填 |
| `GOOGLE_SHEET_ID` | Google Sheet ID | 必填 |

## 常見問題

**Q: Dashboard 顯示示範資料**  
A: 確認 `GOOGLE_SHEET_ID` 環境變數已設定，且 Google Sheet 內有資料。

**Q: GitHub Actions 失敗**  
A: 點開 Actions log 查看錯誤。最常見原因是 Secrets 名稱打錯，或 Google Sheets 授權沒設好。

**Q: 要補抓歷史資料**  
A: 執行 `python run_daily.py --days 90` 可以補抓最近 90 天。
