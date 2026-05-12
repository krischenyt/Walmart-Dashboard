"""
walmart_api.py
──────────────
Walmart Marketplace API 串接模組
負責：取得 Token、抓訂單、解析資料
"""

import os
import base64
import time
import hashlib
import requests
from datetime import date, timedelta


WALMART_BASE = "https://marketplace.walmartapis.com/v3"


def get_token() -> str:
    """
    取得 OAuth 2.0 Access Token
    每次呼叫都會重新取得（Token 有效期 15 分鐘）
    """
    client_id = os.environ["WALMART_CLIENT_ID"]
    client_secret = os.environ["WALMART_CLIENT_SECRET"]

    creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    correlation_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:16]

    resp = requests.post(
        f"{WALMART_BASE}/token",
        headers={
            "Authorization": f"Basic {creds}",
            "Content-Type": "application/x-www-form-urlencoded",
            "WM_QOS.CORRELATION_ID": correlation_id,
            "WM_SVC.NAME": "walmart-dashboard",
        },
        data={"grant_type": "client_credentials"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def fetch_orders(token: str, start_date: date, end_date: date) -> list[dict]:
    """
    分頁抓取指定日期範圍的所有訂單
    自動處理分頁（nextCursor）和 Rate Limit
    """
    headers = {
        "WM_SEC.ACCESS_TOKEN": token,
        "WM_QOS.CORRELATION_ID": hashlib.md5(str(time.time()).encode()).hexdigest()[:16],
        "WM_SVC.NAME": "walmart-dashboard",
        "Accept": "application/json",
    }

    all_orders = []
    cursor = None
    page = 1

    while True:
        params = {
            "createdStartDate": f"{start_date}T00:00:00",
            "createdEndDate": f"{end_date}T23:59:59",
            "limit": 200,
        }
        if cursor:
            params["nextCursor"] = cursor

        print(f"  抓取第 {page} 頁訂單...")
        resp = requests.get(
            f"{WALMART_BASE}/orders",
            headers=headers,
            params=params,
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()

        orders = (
            data.get("list", {})
                .get("elements", {})
                .get("order", [])
        )
        all_orders.extend(orders)

        meta = data.get("list", {}).get("meta", {})
        cursor = meta.get("nextCursor")

        if not cursor:
            break

        page += 1
        time.sleep(0.3)  # Rate limit 保護

    print(f"  共抓取 {len(all_orders)} 筆訂單原始資料")
    return all_orders


def parse_orders(raw_orders: list[dict]) -> list[dict]:
    """
    將 Walmart 訂單 JSON 扁平化
    每個 order line 變成一列資料
    """
    rows = []

    for order in raw_orders:
        order_id = order.get("purchaseOrderId", "")
        order_date = (order.get("orderDate") or "")[:10]
        customer_name = (
            order.get("shippingInfo", {})
                 .get("postalAddress", {})
                 .get("name", "")
        )

        order_lines = (
            order.get("orderLines", {})
                 .get("orderLine", []) or []
        )

        for line in order_lines:
            item = line.get("item", {})
            item_name = item.get("productName", "未知商品")
            item_id = item.get("itemId", "")
            sku = item.get("sku", "")

            qty_info = line.get("orderLineQuantity", {})
            qty = int(float(qty_info.get("amount", 1)))

            # 取得金額（找 PRODUCT 類型的 charge）
            charges = line.get("charges", {}).get("charge", []) or []
            price = 0.0
            for charge in charges:
                if charge.get("chargeType") == "PRODUCT":
                    price = float(
                        charge.get("chargeAmount", {}).get("amount", 0)
                    )
                    break

            # 取得訂單狀態
            statuses = (
                line.get("orderLineStatuses", {})
                    .get("orderLineStatus", []) or []
            )
            status = statuses[0].get("status", "Unknown") if statuses else "Unknown"

            rows.append({
                "date":          order_date,
                "order_id":      order_id,
                "item_id":       item_id,
                "sku":           sku,
                "item_name":     item_name,
                "qty":           qty,
                "price":         round(price, 2),
                "status":        status,
                "customer_name": customer_name,
            })

    return rows
