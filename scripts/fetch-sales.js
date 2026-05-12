/**
 * fetch-sales.js
 * 每天由 GitHub Actions 呼叫，抓取 Walmart Marketplace 銷售資料
 * 並將結果附加到 data/sales.json
 */

import fetch from 'node-fetch';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DATA_FILE = path.join(__dirname, '..', 'data', 'sales.json');

// ─── 1. 取得 Walmart OAuth token ───────────────────────────────────────────
async function getAccessToken() {
  const clientId = process.env.WALMART_CLIENT_ID;
  const clientSecret = process.env.WALMART_CLIENT_SECRET;

  if (!clientId || !clientSecret) {
    throw new Error('缺少 WALMART_CLIENT_ID 或 WALMART_CLIENT_SECRET 環境變數');
  }

  const credentials = Buffer.from(`${clientId}:${clientSecret}`).toString('base64');

  const res = await fetch('https://marketplace.walmartapis.com/v3/token', {
    method: 'POST',
    headers: {
      'Authorization': `Basic ${credentials}`,
      'Content-Type': 'application/x-www-form-urlencoded',
      'Accept': 'application/json',
      'WM_SVC.NAME': 'Walmart Marketplace',
      'WM_QOS.CORRELATION_ID': `fetch-${Date.now()}`,
    },
    body: 'grant_type=client_credentials',
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Token 取得失敗 (${res.status}): ${err}`);
  }

  const data = await res.json();
  return data.access_token;
}

// ─── 2. 抓取昨天的訂單 ────────────────────────────────────────────────────
async function fetchOrders(token) {
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const dateStr = yesterday.toISOString().split('T')[0]; // YYYY-MM-DD

  const startTime = `${dateStr}T00:00:00.000Z`;
  const endTime   = `${dateStr}T23:59:59.999Z`;

  const url = new URL('https://marketplace.walmartapis.com/v3/orders');
  url.searchParams.set('createdStartDate', startTime);
  url.searchParams.set('createdEndDate',   endTime);
  url.searchParams.set('limit', '200');

  const res = await fetch(url.toString(), {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/json',
      'WM_SVC.NAME': 'Walmart Marketplace',
      'WM_QOS.CORRELATION_ID': `orders-${Date.now()}`,
      'WM_SEC.ACCESS_TOKEN': token,
    },
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`訂單抓取失敗 (${res.status}): ${err}`);
  }

  const data = await res.json();
  return { date: dateStr, orders: data.list?.elements?.order ?? [] };
}

// ─── 3. 計算當日統計 ──────────────────────────────────────────────────────
function calcDailySummary(date, orders) {
  let totalRevenue = 0;
  let totalUnits   = 0;
  const productMap = {};

  for (const order of orders) {
    for (const line of order.orderLines?.orderLine ?? []) {
      const qty   = Number(line.orderLineQuantity?.amount ?? 0);
      const price = Number(line.charges?.charge?.[0]?.chargeAmount?.amount ?? 0);
      const name  = line.item?.productName ?? 'Unknown';
      const sku   = line.item?.sku ?? 'N/A';

      totalRevenue += price * qty;
      totalUnits   += qty;

      if (!productMap[sku]) {
        productMap[sku] = { sku, name, units: 0, revenue: 0 };
      }
      productMap[sku].units   += qty;
      productMap[sku].revenue += price * qty;
    }
  }

  const topProducts = Object.values(productMap)
    .sort((a, b) => b.revenue - a.revenue)
    .slice(0, 10)
    .map(p => ({ ...p, revenue: +p.revenue.toFixed(2) }));

  return {
    date,
    orderCount:   orders.length,
    totalRevenue: +totalRevenue.toFixed(2),
    totalUnits,
    topProducts,
    fetchedAt: new Date().toISOString(),
  };
}

// ─── 4. 讀寫 JSON 資料檔 ──────────────────────────────────────────────────
function loadData() {
  if (!fs.existsSync(DATA_FILE)) return { lastUpdated: null, daily: [] };
  return JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
}

function saveData(db, summary) {
  const existingIdx = db.daily.findIndex(d => d.date === summary.date);
  if (existingIdx >= 0) {
    db.daily[existingIdx] = summary; // 覆蓋同一天資料
  } else {
    db.daily.push(summary);
  }
  db.daily.sort((a, b) => a.date.localeCompare(b.date));
  db.lastUpdated = new Date().toISOString();
  fs.writeFileSync(DATA_FILE, JSON.stringify(db, null, 2));
  console.log(`✅ 已儲存 ${summary.date} 資料 — 訂單 ${summary.orderCount} 筆，營收 $${summary.totalRevenue}`);
}

// ─── 5. 主流程 ────────────────────────────────────────────────────────────
(async () => {
  try {
    console.log('🔑 取得 Walmart access token...');
    const token = await getAccessToken();

    console.log('📦 抓取昨日訂單...');
    const { date, orders } = await fetchOrders(token);
    console.log(`  找到 ${orders.length} 筆訂單（${date}）`);

    const summary = calcDailySummary(date, orders);
    const db = loadData();
    saveData(db, summary);
  } catch (err) {
    console.error('❌ 錯誤:', err.message);
    process.exit(1);
  }
})();
