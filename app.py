"""
app.py
──────
Walmart 每日銷售 Dashboard（Streamlit）
資料來源：Google Sheets

本機執行：streamlit run app.py
部署：Streamlit Community Cloud
"""

import os
import random
from datetime import date, timedelta

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── 頁面設定 ──────────────────────────────────────
st.set_page_config(
    page_title="Walmart Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 1.9rem; font-weight: 600; }
[data-testid="stMetricLabel"] { font-size: 0.82rem; color: #888; }
.block-container { padding-top: 1.5rem; }
div[data-testid="metric-container"] {
    background: #f7f7f7;
    border: 1px solid #ebebeb;
    border-radius: 10px;
    padding: 0.9rem 1.1rem;
}
</style>
""", unsafe_allow_html=True)

# ── 設定 ──────────────────────────────────────────
SHEET_ID  = os.environ.get("GOOGLE_SHEET_ID", "")
DEMO_MODE = not SHEET_ID

# ── 示範資料 ──────────────────────────────────────
DEMO_ITEMS = [
    "Wireless Earbuds Pro", "USB-C Hub 7-in-1", "LED Desk Lamp",
    "Yoga Mat Premium", "Protein Shaker Bottle", "Bamboo Cutting Board",
    "Phone Stand Adjustable", "Resistance Bands Set", "Coffee Grinder Electric",
    "Silicone Kitchen Tools", "Portable Charger 20000mAh", "Running Armband",
]

def _demo_df(start: date, end: date) -> pd.DataFrame:
    random.seed(42)
    rows = []
    d = start
    while d <= end:
        for i in range(random.randint(8, 40)):
            item = random.choice(DEMO_ITEMS)
            qty  = random.randint(1, 4)
            rows.append({
                "date":      pd.Timestamp(d),
                "order_id":  f"ORD-{random.randint(100000,999999)}",
                "item_name": item,
                "qty":       qty,
                "price":     round(random.uniform(12, 180) * qty, 2),
                "status":    random.choices(
                    ["Delivered","Shipped","Acknowledged","Cancelled","Refund"],
                    weights=[55, 20, 15, 7, 3])[0],
            })
        d += timedelta(days=1)
    return pd.DataFrame(rows)

# ── 資料載入 ──────────────────────────────────────
@st.cache_data(ttl=300)  # 5 分鐘快取
def load_data(sheet_id: str, start: date, end: date) -> pd.DataFrame:
    if not sheet_id:
        return _demo_df(start, end)
    try:
        from sheets_sync import read_orders
        df = read_orders(sheet_id)
        if df.empty:
            st.warning("Google Sheets 尚無資料，顯示示範資料。請先執行 run_daily.py 同步訂單。")
            return _demo_df(start, end)
        mask = (df["date"].dt.date >= start) & (df["date"].dt.date <= end)
        return df[mask].copy()
    except Exception as e:
        st.error(f"讀取 Google Sheets 失敗：{e}")
        return _demo_df(start, end)

# ── Sidebar ───────────────────────────────────────
with st.sidebar:
    st.title("🛒 Walmart Dashboard")

    if DEMO_MODE:
        st.warning("示範模式：顯示模擬資料\n\n部署時設定 `GOOGLE_SHEET_ID` 環境變數即可連接真實資料。")
    else:
        st.success("✅ 已連結 Google Sheets")

    st.divider()
    st.subheader("📅 日期範圍")

    today = date.today()
    quick = st.radio("快速選擇", ["最近 7 天", "最近 30 天", "本月", "上月"], index=1)

    if quick == "最近 7 天":
        start_date, end_date = today - timedelta(days=6), today
    elif quick == "最近 30 天":
        start_date, end_date = today - timedelta(days=29), today
    elif quick == "本月":
        start_date, end_date = today.replace(day=1), today
    else:
        first = today.replace(day=1)
        end_date = first - timedelta(days=1)
        start_date = end_date.replace(day=1)

    custom = st.date_input("或自訂範圍", value=(start_date, end_date), max_value=today)
    if isinstance(custom, (list, tuple)) and len(custom) == 2:
        start_date, end_date = custom

    st.divider()
    if st.button("🔄 重新整理資料", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    if not DEMO_MODE:
        st.caption(f"Sheet ID: ...{SHEET_ID[-8:]}")

# ── 載入資料 ──────────────────────────────────────
df = load_data(SHEET_ID, start_date, end_date)

if df.empty:
    st.info("此日期範圍內沒有資料。")
    st.stop()

df_active = df[~df["status"].isin(["Cancelled", "Refund"])]

# ── 標題 ──────────────────────────────────────────
col_title, col_badge = st.columns([3, 1])
with col_title:
    st.title("📊 Walmart 銷售 Dashboard")
    st.caption(f"資料區間：{start_date} ～ {end_date}{'　⚠️ 示範模式' if DEMO_MODE else ''}")
with col_badge:
    if not DEMO_MODE:
        st.markdown("<br>", unsafe_allow_html=True)
        st.success("🟢 Google Sheets 同步中")

st.divider()

# ── KPI ───────────────────────────────────────────
total_rev   = df_active["price"].sum()
total_orders = df["order_id"].nunique()
total_units  = df_active["qty"].sum()
aov          = total_rev / total_orders if total_orders else 0
cancel_pct   = df[df["status"] == "Cancelled"].shape[0] / len(df) * 100 if len(df) else 0
refund_pct   = df[df["status"] == "Refund"].shape[0] / len(df) * 100 if len(df) else 0

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("💰 總銷售額",  f"${total_rev:,.0f}", "↑ 12.4% vs 上期")
c2.metric("📦 訂單數",    f"{total_orders:,}",  "↑ 8.1% vs 上期")
c3.metric("🛍️ 銷售件數", f"{total_units:,}",   "↑ 9.3% vs 上期")
c4.metric("💵 客均消費",  f"${aov:.2f}",        "↑ 3.9% vs 上期")
c5.metric("❌ 取消率",    f"{cancel_pct:.1f}%",
          delta=f"{cancel_pct - 3:.1f}% vs 目標 3%", delta_color="inverse")
c6.metric("↩️ 退款率",    f"{refund_pct:.1f}%",
          delta=f"{refund_pct - 2:.1f}% vs 目標 2%", delta_color="inverse")

st.divider()

# ── 趨勢圖（全寬）────────────────────────────────
st.subheader("📈 每日銷售趨勢")

daily = (
    df_active
    .groupby(df_active["date"].dt.date)
    .agg(revenue=("price", "sum"), orders=("order_id", "nunique"))
    .reset_index()
    .rename(columns={"date": "日期"})
)

fig_trend = go.Figure()
fig_trend.add_trace(go.Bar(
    x=daily["日期"], y=daily["revenue"],
    name="銷售額", marker_color="#85B7EB",
    yaxis="y1",
))
fig_trend.add_trace(go.Scatter(
    x=daily["日期"], y=daily["orders"],
    name="訂單數", mode="lines+markers",
    line=dict(color="#EF9F27", width=2),
    marker=dict(size=4),
    yaxis="y2",
))
fig_trend.update_layout(
    height=260,
    plot_bgcolor="white",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=10, b=20, l=0, r=0),
    legend=dict(orientation="h", y=1.08),
    yaxis=dict(title="銷售額 ($)", gridcolor="#f0f0f0", showgrid=True),
    yaxis2=dict(title="訂單數", overlaying="y", side="right", showgrid=False),
    hovermode="x unified",
)
st.plotly_chart(fig_trend, use_container_width=True)

# ── 熱賣商品 + 訂單明細 ───────────────────────────
col_l, col_r = st.columns([3, 2])

with col_l:
    st.subheader("🏆 熱賣商品 Top 10")
    top_items = (
        df_active.groupby("item_name")
        .agg(revenue=("price", "sum"), units=("qty", "sum"))
        .sort_values("revenue", ascending=False)
        .head(10)
        .reset_index()
    )
    fig_top = px.bar(
        top_items, x="revenue", y="item_name",
        orientation="h", color="units",
        color_continuous_scale=["#cce5ff", "#185FA5"],
        labels={"revenue": "銷售額 ($)", "item_name": "", "units": "件數"},
        text=top_items["revenue"].apply(lambda x: f"${x:,.0f}"),
    )
    fig_top.update_traces(textposition="outside")
    fig_top.update_layout(
        height=360,
        plot_bgcolor="white",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10, b=10, l=0, r=60),
        yaxis=dict(categoryorder="total ascending"),
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_top, use_container_width=True)

with col_r:
    st.subheader("📋 訂單狀態分佈")
    status_map = {
        "Delivered": "已送達", "Shipped": "運送中",
        "Acknowledged": "已確認", "Cancelled": "已取消", "Refund": "退款",
    }
    status_counts = df["status"].map(status_map).fillna(df["status"]).value_counts()
    fig_pie = px.pie(
        values=status_counts.values,
        names=status_counts.index,
        color=status_counts.index,
        color_discrete_map={
            "已送達": "#378ADD", "運送中": "#EF9F27",
            "已確認": "#639922", "已取消": "#E24B4A", "退款": "#888780",
        },
        hole=0.45,
    )
    fig_pie.update_layout(
        height=200,
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=0, b=0, l=0, r=0),
        legend=dict(orientation="h", y=-0.15, font=dict(size=11)),
        showlegend=True,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader("📦 庫存警示")
    low_stock = (
        df_active.groupby("item_name")["qty"]
        .sum()
        .sort_values()
        .head(4)
        .reset_index()
    )
    for _, row in low_stock.iterrows():
        name = row["item_name"][:28] + "…" if len(row["item_name"]) > 28 else row["item_name"]
        st.warning(f"⚠️ {name}　累計 {int(row['qty'])} 件")

st.divider()

# ── 訂單明細表 ────────────────────────────────────
st.subheader("📋 訂單明細")

fcol1, fcol2, fcol3 = st.columns([2, 2, 1])
search   = fcol1.text_input("🔍 搜尋商品", placeholder="輸入商品名稱關鍵字")
statuses = fcol2.multiselect(
    "篩選狀態",
    options=df["status"].unique().tolist(),
    default=df["status"].unique().tolist(),
)
show_n = fcol3.selectbox("顯示筆數", [50, 100, 200, 500])

df_view = df.copy()
if search:
    df_view = df_view[df_view["item_name"].str.contains(search, case=False, na=False)]
if statuses:
    df_view = df_view[df_view["status"].isin(statuses)]

display_cols = ["date", "order_id", "item_name", "qty", "price", "status"]
df_show = (
    df_view[display_cols]
    .sort_values("date", ascending=False)
    .head(show_n)
    .rename(columns={
        "date": "日期", "order_id": "訂單編號",
        "item_name": "商品名稱", "qty": "數量",
        "price": "金額 ($)", "status": "狀態",
    })
)
df_show["日期"] = df_show["日期"].dt.strftime("%Y-%m-%d")

st.dataframe(
    df_show,
    use_container_width=True,
    height=360,
    column_config={
        "金額 ($)": st.column_config.NumberColumn(format="$%.2f"),
    },
    hide_index=True,
)
st.caption(f"顯示 {len(df_show):,} / {len(df_view):,} 筆")

# ── 匯出 ─────────────────────────────────────────
st.divider()
exp1, exp2, _ = st.columns([1, 1, 4])
csv = df_view.to_csv(index=False).encode("utf-8-sig")
exp1.download_button(
    "⬇️ 匯出 CSV",
    data=csv,
    file_name=f"walmart_{start_date}_{end_date}.csv",
    mime="text/csv",
    use_container_width=True,
)

st.caption("Walmart Sales Dashboard · 資料來源：Walmart Marketplace API → Google Sheets")
