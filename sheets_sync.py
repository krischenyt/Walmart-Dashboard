"""
sheets_sync.py
──────────────
Google Sheets 讀寫模組
負責：建立連線、寫入訂單（去重）、讀取資料給 Dashboard
"""

import os
import json
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]
SHEET_NAME = "Orders"
HEADERS = ["date", "order_id", "item_id", "sku", "item_name", "qty", "price", "status", "customer_name"]


def _get_client() -> gspread.Client:
    """
    建立 Google Sheets 連線
    支援兩種方式：
      1. 環境變數 GOOGLE_CREDENTIALS（JSON 字串，適合 GitHub Actions / Streamlit Cloud）
      2. service_account.json 檔案（適合本機開發）
    """
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")

    if creds_json:
        # 從環境變數讀取（部署環境）
        info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    elif os.path.exists("service_account.json"):
        # 從檔案讀取（本機開發）
        creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
    else:
        raise EnvironmentError(
            "找不到 Google 憑證。\n"
            "請設定環境變數 GOOGLE_CREDENTIALS，\n"
            "或在專案根目錄放置 service_account.json"
        )

    return gspread.authorize(creds)


def _get_worksheet(sheet_id: str) -> gspread.Worksheet:
    """取得或建立 Orders 工作表"""
    gc = _get_client()
    spreadsheet = gc.open_by_key(sheet_id)

    try:
        ws = spreadsheet.worksheet(SHEET_NAME)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=SHEET_NAME, rows=10000, cols=len(HEADERS))
        ws.append_row(HEADERS)
        print(f"  已建立工作表：{SHEET_NAME}")

    return ws


def write_orders(rows: list[dict], sheet_id: str) -> int:
    """
    寫入訂單資料到 Google Sheets
    - 自動去重（根據 order_id）
    - 回傳實際寫入的筆數
    """
    if not rows:
        print("  無新資料需要寫入")
        return 0

    ws = _get_worksheet(sheet_id)

    # 讀取現有資料，取得已存在的 order_id
    existing = ws.get_all_values()

    if not existing or existing[0] != HEADERS:
        # 工作表是空的或標題不對，重設標題
        ws.clear()
        ws.append_row(HEADERS)
        existing_ids = set()
    else:
        # 找到 order_id 欄位的 index
        id_col = HEADERS.index("order_id")
        existing_ids = {row[id_col] for row in existing[1:] if len(row) > id_col}

    # 篩選出新訂單
    new_rows = [r for r in rows if r["order_id"] not in existing_ids]

    if not new_rows:
        print("  所有訂單已存在，無需更新")
        return 0

    # 批次寫入
    data_to_write = [
        [r.get(h, "") for h in HEADERS]
        for r in new_rows
    ]
    ws.append_rows(data_to_write, value_input_option="USER_ENTERED")

    print(f"  已寫入 {len(new_rows)} 筆新訂單（略過 {len(rows) - len(new_rows)} 筆重複）")
    return len(new_rows)


def read_orders(sheet_id: str) -> pd.DataFrame:
    """
    從 Google Sheets 讀取所有訂單資料
    回傳 DataFrame，供 Dashboard 使用
    """
    ws = _get_worksheet(sheet_id)
    data = ws.get_all_records(expected_headers=HEADERS)

    if not data:
        return pd.DataFrame(columns=HEADERS)

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0).astype(int)

    return df
