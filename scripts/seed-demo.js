/**
 * seed-demo.js
 * 產生 90 天假資料，方便在設定真實 API 前測試 Dashboard
 * 執行：node seed-demo.js
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DATA_FILE = path.join(__dirname, '..', 'data', 'sales.json');

const PRODUCTS = [
  { sku: 'WMT-001', name: 'Wireless Earbuds Pro' },
  { sku: 'WMT-002', name: 'USB-C Hub 7-in-1' },
  { sku: 'WMT-003', name: 'Portable Phone Stand' },
  { sku: 'WMT-004', name: 'LED Desk Lamp' },
  { sku: 'WMT-005', name: 'Mechanical Keyboard' },
  { sku: 'WMT-006', name: 'Webcam 1080p' },
  { sku: 'WMT-007', name: 'Mouse Pad XL' },
  { sku: 'WMT-008', name: 'Cable Management Kit' },
];

function rand(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function generateDay(dateStr, dayIndex) {
  // 週末銷售較高
  const d = new Date(dateStr);
  const isWeekend = d.getDay() === 0 || d.getDay() === 6;
  const multiplier = isWeekend ? 1.4 : 1.0;

  // 模擬成長趨勢
  const growthFactor = 1 + (dayIndex / 90) * 0.3;

  const orderCount = Math.round(rand(40, 80) * multiplier * growthFactor);
  const topProducts = PRODUCTS.map(p => {
    const units = Math.round(rand(2, 20) * multiplier);
    const price = rand(15, 120);
    return { sku: p.sku, name: p.name, units, revenue: +(units * price).toFixed(2) };
  }).sort((a, b) => b.revenue - a.revenue);

  const totalRevenue = topProducts.reduce((s, p) => s + p.revenue, 0);
  const totalUnits   = topProducts.reduce((s, p) => s + p.units,   0);

  return {
    date: dateStr,
    orderCount,
    totalRevenue: +totalRevenue.toFixed(2),
    totalUnits,
    topProducts,
    fetchedAt: new Date().toISOString(),
  };
}

const daily = [];
for (let i = 89; i >= 0; i--) {
  const d = new Date();
  d.setDate(d.getDate() - i);
  const dateStr = d.toISOString().split('T')[0];
  daily.push(generateDay(dateStr, 89 - i));
}

const db = { lastUpdated: new Date().toISOString(), daily };
fs.mkdirSync(path.dirname(DATA_FILE), { recursive: true });
fs.writeFileSync(DATA_FILE, JSON.stringify(db, null, 2));
console.log(`✅ 產生 ${daily.length} 天示範資料 → ${DATA_FILE}`);
