"""
run_daily.py
────────────
每日同步腳本
執行流程：取得 Token → 抓昨天+今天訂單 → 寫入 Google Sheets

使用方式：
  python run_daily.py              # 抓昨天到今天
  python run_daily.py --days 7     # 抓最近 7 天（補抓用）
  python run_daily.py --days 30    # 抓最近 30 天（初次設定用）
"""

import os
import sys
import argparse
from datetime import date, timedelta

from walmart_api import get_token, fetch_orders, parse_orders
from sheets_sync import write_orders


def main():
    parser = argparse.ArgumentParser(description="Walmart 訂單每日同步")
    parser.add_argument("--days", type=int, default=2,
                        help="抓取最近幾天的資料（預設 2，即昨天+今天）")
    args = parser.parse_args()

    # 讀取必要的環境變數
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    if not sheet_id:
        print("❌ 錯誤：請設定環境變數 GOOGLE_SHEET_ID")
        sys.exit(1)

    end_date = date.today()
    start_date = end_date - timedelta(days=args.days - 1)

    print(f"{'='*50}")
    print(f"Walmart 訂單同步")
    print(f"日期範圍：{start_date} ～ {end_date}")
    print(f"{'='*50}")

    # Step 1: 取得 Token
    print("\n[1/3] 取得 Walmart API Token...")
    try:
        token = get_token()
        print("  ✅ Token 取得成功")
    except Exception as e:
        print(f"  ❌ Token 取得失敗：{e}")
        sys.exit(1)

    # Step 2: 抓取訂單
    print(f"\n[2/3] 抓取訂單資料...")
    try:
        raw = fetch_orders(token, start_date, end_date)
        rows = parse_orders(raw)
        print(f"  ✅ 解析完成，共 {len(rows)} 筆訂單明細")
    except Exception as e:
        print(f"  ❌ 抓取失敗：{e}")
        sys.exit(1)

    # Step 3: 寫入 Google Sheets
    print(f"\n[3/3] 寫入 Google Sheets...")
    try:
        written = write_orders(rows, sheet_id)
        print(f"  ✅ 同步完成")
    except Exception as e:
        print(f"  ❌ 寫入失敗：{e}")
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f"同步完成！新增 {written} 筆訂單")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
