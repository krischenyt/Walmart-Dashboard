# 📊 Walmart Sales Dashboard

每天自動從 Walmart Marketplace API 抓取銷售資料，並透過 GitHub Pages 提供可分享的 Dashboard。

## 🔗 Dashboard 連結
部署後連結：`https://<your-username>.github.io/<repo-name>/`

---

## 🚀 快速設定（5 步驟）

### 1. Fork / Clone 此 Repo
```bash
git clone https://github.com/YOUR_USERNAME/walmart-dashboard.git
cd walmart-dashboard
```

### 2. 申請 Walmart Marketplace API 金鑰
1. 前往 [Walmart Developer Portal](https://developer.walmart.com/)
2. 登入賣家帳號 → **My Account → API Keys**
3. 複製 **Client ID** 和 **Client Secret**

### 3. 設定 GitHub Secrets
在 GitHub Repo 頁面：**Settings → Secrets and variables → Actions → New repository secret**

| Secret 名稱 | 說明 |
|---|---|
| `WALMART_CLIENT_ID` | Walmart API Client ID |
| `WALMART_CLIENT_SECRET` | Walmart API Client Secret |

### 4. 啟用 GitHub Pages
1. **Settings → Pages**
2. Source：`Deploy from a branch`
3. Branch：`main` / `docs`
4. 存檔後 1-2 分鐘即可訪問

### 5. 第一次執行（產生資料）
手動觸發 GitHub Action：**Actions → Fetch Walmart Sales Data → Run workflow**

> 💡 **測試用**：先跑 `node scripts/seed-demo.js` 產生 90 天假資料

---

## 📅 排程說明
GitHub Actions 每天 UTC 02:00（台灣時間 10:00）自動執行，抓取昨天的訂單並更新資料。

## 📁 專案結構
```
walmart-dashboard/
├── .github/
│   └── workflows/
│       └── fetch-sales.yml     # 自動排程
├── scripts/
│   ├── fetch-sales.js          # Walmart API 抓資料
│   ├── seed-demo.js            # 產生示範資料
│   └── package.json
├── data/
│   └── sales.json              # 歷史銷售資料（自動更新）
└── docs/                       # GitHub Pages
    ├── index.html              # Dashboard 前端
    └── data/
        └── sales.json
```

## 🔧 本地開發
```bash
# 產生測試資料
cd scripts && npm install
node seed-demo.js

# 啟動本地伺服器（需在根目錄）
npx serve docs
# 或
python3 -m http.server 8000 --directory docs
```

## ❓ FAQ

**Q: 為什麼 Dashboard 沒有資料？**
先執行 `node scripts/seed-demo.js` 產生示範資料，或手動觸發 GitHub Action。

**Q: 資料多久更新一次？**
每天自動執行一次（台灣時間 10:00）。也可在 Actions 頁面手動觸發。

**Q: 可以修改抓取頻率嗎？**
編輯 `.github/workflows/fetch-sales.yml` 中的 `cron` 表達式。
