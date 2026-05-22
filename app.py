import streamlit as st
import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, date
import json

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="P&L Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CONSTANTS — EDIT THESE ─────────────────────────────────────────────────
SHEET_URL  = "https://docs.google.com/spreadsheets/d/1r6bWx_JlvEPn_YYszN8y6Wc8Q6Vm5FE-56aLHXhMSZk/edit?gid=837977405#gid=837977405"          # ← paste your sheet URL
SHEET_NAME = "TDSheet"                # ← e.g. "Raw" or "Data"

# ─── CUSTOM CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600;700&display=swap');

:root {
    --bg:        #0d0f14;
    --surface:   #141720;
    --border:    #1e2230;
    --accent:    #4f8ef7;
    --green:     #22c55e;
    --red:       #ef4444;
    --amber:     #f59e0b;
    --text:      #e2e8f0;
    --muted:     #64748b;
    --mono:      'DM Mono', monospace;
    --sans:      'DM Sans', sans-serif;
}

html, body, [class*="css"] {
    font-family: var(--sans);
    background-color: var(--bg) !important;
    color: var(--text);
}

.main .block-container { padding: 1.5rem 2rem; max-width: 100%; }

/* ── HEADER ── */
.dashboard-header {
    display: flex; align-items: center; gap: 12px;
    margin-bottom: 1.5rem;
}
.dashboard-header h1 {
    font-size: 1.5rem; font-weight: 700; margin: 0;
    background: linear-gradient(90deg, #4f8ef7, #a78bfa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.dashboard-header .sub {
    font-size: 0.8rem; color: var(--muted); font-family: var(--mono);
}

/* ── FILTER BAR ── */
.filter-bar {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1.5rem;
    margin-bottom: 1.5rem;
    display: flex; gap: 1rem; flex-wrap: wrap; align-items: flex-end;
}

/* ── KPI CARDS ── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
    gap: 0.75rem;
    margin-bottom: 1.5rem;
}
.kpi-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    transition: border-color .2s;
}
.kpi-card:hover { border-color: var(--accent); }
.kpi-label  { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; }
.kpi-value  { font-size: 1.35rem; font-weight: 700; font-family: var(--mono); margin: 4px 0; }
.kpi-sub    { font-size: 0.72rem; color: var(--muted); font-family: var(--mono); }
.pos { color: var(--green); }
.neg { color: var(--red); }
.neu { color: var(--text); }

/* ── SECTION HEADERS ── */
.section-title {
    font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: .1em; color: var(--muted);
    border-left: 3px solid var(--accent);
    padding-left: 10px; margin: 1.5rem 0 .75rem;
}

/* ── TABLES ── */
.stDataFrame { background: var(--surface) !important; }
.stDataFrame th {
    background: #1a1f2e !important;
    color: var(--muted) !important;
    font-family: var(--mono) !important;
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: .06em;
}
.stDataFrame td {
    font-family: var(--mono) !important;
    font-size: 0.82rem !important;
}

/* Streamlit widget overrides */
div[data-testid="stSelectbox"] > div,
div[data-testid="stMultiSelect"] > div,
div[data-testid="stDateInput"] > div input {
    background: #1a1f2e !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
    border-radius: 8px !important;
}
label { color: var(--muted) !important; font-size: 0.75rem !important; font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: .07em !important; }

div[data-testid="stAlert"] { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ─── DATA LOADING ────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ]
        creds = Credentials.from_service_account_info(dict(creds_dict), scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open_by_url(SHEET_URL)
        ws = sh.worksheet(SHEET_NAME)
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        return df, None
    except Exception as e:
        return None, str(e)

# ─── HELPER: numeric coerce ──────────────────────────────────────────────────
def to_num(series):
    return pd.to_numeric(series.astype(str).str.replace(",", "").str.replace("%", ""), errors="coerce").fillna(0)

# ─── METRIC FORMATTING ───────────────────────────────────────────────────────
def fmt_usd(v):
    if abs(v) >= 1_000_000: return f"${v/1e6:.2f}M"
    if abs(v) >= 1_000:     return f"${v/1e3:.1f}K"
    return f"${v:,.2f}"

def fmt_pct(v): return f"{v:.1f}%"
def fmt_int(v): return f"{int(v):,}"
def color_class(v): return "pos" if v > 0 else ("neg" if v < 0 else "neu")

# ─── KPI CARD HTML ────────────────────────────────────────────────────────────
def kpi(label, value, sub="", cls="neu"):
    return f"""
    <div class='kpi-card'>
        <div class='kpi-label'>{label}</div>
        <div class='kpi-value {cls}'>{value}</div>
        <div class='kpi-sub'>{sub}</div>
    </div>"""

# ─── DATE FILTER LOGIC ───────────────────────────────────────────────────────
def get_date_range(option, custom_start=None, custom_end=None):
    today = date.today()
    if option == "Today":           return today, today
    if option == "Last 7 days":     return today - timedelta(days=6), today
    if option == "Last 14 days":    return today - timedelta(days=13), today
    if option == "This month":      return today.replace(day=1), today
    if option == "Last month":
        first = today.replace(day=1)
        last_month_end = first - timedelta(days=1)
        return last_month_end.replace(day=1), last_month_end
    if option == "Custom":          return custom_start, custom_end
    return None, None

# ─── BUILD P&L SUMMARY TABLE ─────────────────────────────────────────────────
def build_pnl(df):
    rows = {}

    def s(col):
        return to_num(df[col]) if col in df.columns else pd.Series([0]*len(df))

    sales = s("SalesOrganic") + s("SalesPPC") + s("SalesSponsoredProducts") + s("SalesSponsoredDisplay")
    units = s("UnitsOrganic") + s("UnitsPPC") + s("UnitsSponsoredProducts") + s("UnitsSponsoredDisplay")
    refunds       = s("Refunds")
    promo         = s("PromoValue")
    ads           = s("SponsoredProducts") + s("SponsoredDisplay") + s("SponsoredВrands") + s("SponsoredBrandsVideo") + s("Google ads") + s("Facebook ads")
    refund_cost   = s("RefundCost")
    amazon_fees   = s("AmazonFees")
    cogs          = s("ProductCost") + s("Cost of Goods")
    gross_profit  = s("GrossProfit")
    net_profit    = s("NetProfit")
    sessions      = s("Sessions")
    est_payout    = s("EstimatedPayout")

    rows["Sales"]           = sales.sum()
    rows["Units"]           = units.sum()
    rows["Refunds (qty)"]   = refunds.sum()
    rows["Promo"]           = promo.sum()
    rows["Advertising cost"]= -abs(ads.sum())
    rows["Refund cost"]     = -abs(refund_cost.sum())
    rows["Amazon fees"]     = -abs(amazon_fees.sum())
    rows["Cost of goods"]   = -abs(cogs.sum())
    rows["Gross profit"]    = gross_profit.sum() if gross_profit.sum() != 0 else (rows["Sales"] + rows["Promo"] + rows["Advertising cost"] + rows["Refund cost"] + rows["Amazon fees"] + rows["Cost of goods"])
    rows["Net profit"]      = net_profit.sum() if net_profit.sum() != 0 else rows["Gross profit"]
    rows["Estimated payout"]= est_payout.sum()
    rows["Sessions"]        = sessions.sum()
    rows["Margin"]          = (rows["Net profit"] / rows["Sales"] * 100) if rows["Sales"] else 0
    rows["Real ACOS"]       = (abs(rows["Advertising cost"]) / rows["Sales"] * 100) if rows["Sales"] else 0

    return rows

# ─── FORMAT P&L ROWS ─────────────────────────────────────────────────────────
MONEY_ROWS   = {"Sales","Promo","Advertising cost","Refund cost","Amazon fees","Cost of goods","Gross profit","Net profit","Estimated payout"}
PCT_ROWS     = {"Margin","Real ACOS"}
INT_ROWS     = {"Units","Refunds (qty)","Sessions"}

def format_val(key, val):
    if key in MONEY_ROWS: return fmt_usd(val)
    if key in PCT_ROWS:   return fmt_pct(val)
    if key in INT_ROWS:   return fmt_int(val)
    return str(round(val, 2))

def row_color(key, val):
    profit_rows = {"Gross profit","Net profit","Margin"}
    cost_rows   = {"Advertising cost","Refund cost","Amazon fees","Cost of goods","Promo"}
    if key in profit_rows: return color_class(val)
    if key in cost_rows:   return "neg" if val < 0 else "neu"
    return "neu"

# ─── MAIN APP ────────────────────────────────────────────────────────────────
st.markdown("""
<div class='dashboard-header'>
    <div>
        <h1>📊 P&L Dashboard</h1>
        <div class='sub'>Amazon Seller Analytics · Live from Google Sheets</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Load data
df_raw, err = load_data()

if err:
    st.error(f"❌ Không kết nối được Google Sheet: {err}")
    st.info("💡 Kiểm tra lại:\n1. `SHEET_URL` và `SHEET_NAME` trong `app.py`\n2. Service account credentials trong Streamlit secrets\n3. Sheet đã được share cho service account email chưa")
    st.stop()

# Parse date
df_raw["_date"] = pd.to_datetime(df_raw["Date"], errors="coerce", dayfirst=True)
df_raw = df_raw.dropna(subset=["_date"])
df_raw["_date_only"] = df_raw["_date"].dt.date

# ── FILTER BAR ──────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns([2, 1.5, 1.2, 1.2])

with col1:
    all_asins = sorted(df_raw["ASIN"].dropna().unique().tolist()) if "ASIN" in df_raw.columns else []
    selected_asins = st.multiselect("ASIN / Product", options=all_asins, placeholder="All ASINs")

with col2:
    date_options = ["Last 7 days", "Last 14 days", "This month", "Last month", "Today", "Custom"]
    date_filter = st.selectbox("Date Range", date_options, index=0)

custom_start = custom_end = None
if date_filter == "Custom":
    with col3:
        custom_start = st.date_input("From", value=date.today() - timedelta(days=30))
    with col4:
        custom_end = st.date_input("To", value=date.today())

start_dt, end_dt = get_date_range(date_filter, custom_start, custom_end)

# ── APPLY FILTERS ────────────────────────────────────────────────────────────
df = df_raw.copy()
if selected_asins:
    df = df[df["ASIN"].isin(selected_asins)]
if start_dt and end_dt:
    df = df[(df["_date_only"] >= start_dt) & (df["_date_only"] <= end_dt)]

if df.empty:
    st.warning("⚠️ Không có dữ liệu cho bộ lọc này. Thử thay đổi date range hoặc ASIN.")
    st.stop()

# ── SUMMARY KPI CARDS ────────────────────────────────────────────────────────
pnl = build_pnl(df)
st.markdown("<div class='section-title'>Overview</div>", unsafe_allow_html=True)

kpi_html = "<div class='kpi-grid'>"
kpi_html += kpi("Total Sales",       fmt_usd(pnl["Sales"]),           f"{fmt_int(pnl['Units'])} units", "neu")
kpi_html += kpi("Gross Profit",      fmt_usd(pnl["Gross profit"]),    f"GP margin", color_class(pnl["Gross profit"]))
kpi_html += kpi("Net Profit",        fmt_usd(pnl["Net profit"]),      fmt_pct(pnl["Margin"]) + " margin", color_class(pnl["Net profit"]))
kpi_html += kpi("Est. Payout",       fmt_usd(pnl["Estimated payout"]),"",  "pos" if pnl["Estimated payout"] > 0 else "neu")
kpi_html += kpi("Advertising Cost",  fmt_usd(pnl["Advertising cost"]),fmt_pct(pnl["Real ACOS"]) + " ACOS", "neg")
kpi_html += kpi("Amazon Fees",       fmt_usd(pnl["Amazon fees"]),     "", "neg")
kpi_html += kpi("Cost of Goods",     fmt_usd(pnl["Cost of goods"]),   "", "neg")
kpi_html += kpi("Refund Cost",       fmt_usd(pnl["Refund cost"]),     f"{fmt_int(pnl['Refunds (qty)'])} refunds", "neg")
kpi_html += kpi("Sessions",          fmt_int(pnl["Sessions"]),        "", "neu")
kpi_html += "</div>"
st.markdown(kpi_html, unsafe_allow_html=True)

# ── AGGREGATE P&L TABLE ──────────────────────────────────────────────────────
st.markdown("<div class='section-title'>P&L Summary — All Selected ASINs</div>", unsafe_allow_html=True)

P_AND_L_ORDER = [
    "Sales","Units","Refunds (qty)","Promo",
    "Advertising cost","Refund cost","Amazon fees","Cost of goods",
    "Gross profit","Net profit","Estimated payout",
    "Margin","Real ACOS","Sessions"
]

summary_rows = []
for key in P_AND_L_ORDER:
    val = pnl.get(key, 0)
    summary_rows.append({
        "Metric": key,
        "Value":  format_val(key, val),
        "_val":   val,
        "_cls":   row_color(key, val),
    })

summary_df = pd.DataFrame(summary_rows)[["Metric", "Value"]]

def highlight_summary(row):
    orig = summary_rows[row.name]
    cls  = orig["_cls"]
    color_map = {"pos": "#16a34a33", "neg": "#dc262633", "neu": ""}
    bg = color_map.get(cls, "")
    return [f"background-color:{bg}" if bg else "" for _ in row]

st.dataframe(
    summary_df.style.apply(highlight_summary, axis=1),
    use_container_width=True,
    height=460,
    hide_index=True,
)

# ── PER-ASIN TABLE ───────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>P&L by ASIN</div>", unsafe_allow_html=True)

if "ASIN" not in df.columns:
    st.info("Không tìm thấy cột ASIN trong dữ liệu.")
else:
    asin_groups = df.groupby("ASIN", sort=False)
    asin_records = []

    def s(g, col):
        return to_num(g[col]) if col in g.columns else pd.Series([0]*len(g))

    for asin, grp in asin_groups:
        p = build_pnl(grp)

        name = ""
        if "Name" in grp.columns:
            name = grp["Name"].dropna().iloc[0] if len(grp["Name"].dropna()) > 0 else ""
        name_short = (str(name)[:40] + "…") if len(str(name)) > 40 else str(name)

        asin_records.append({
            "ASIN":           asin,
            "Product":        name_short,
            "Sales":          fmt_usd(p["Sales"]),
            "Units":          fmt_int(p["Units"]),
            "Gross Profit":   fmt_usd(p["Gross profit"]),
            "Net Profit":     fmt_usd(p["Net profit"]),
            "Margin":         fmt_pct(p["Margin"]),
            "Ads Cost":       fmt_usd(p["Advertising cost"]),
            "Real ACOS":      fmt_pct(p["Real ACOS"]),
            "Amazon Fees":    fmt_usd(p["Amazon fees"]),
            "COGS":           fmt_usd(p["Cost of goods"]),
            "Est. Payout":    fmt_usd(p["Estimated payout"]),
            "Refunds":        fmt_int(p["Refunds (qty)"]),
            "_net":           p["Net profit"],
            "_margin":        p["Margin"],
        })

    asin_df = pd.DataFrame(asin_records).sort_values("_net", ascending=False)

    def highlight_asin(row):
        styles = []
        for col in asin_df.columns:
            if col == "Net Profit":
                val = asin_df.loc[row.name, "_net"]
                bg = "#16a34a22" if val > 0 else "#dc262622"
                styles.append(f"background-color:{bg}")
            elif col == "Margin":
                val = asin_df.loc[row.name, "_margin"]
                bg = "#16a34a22" if val > 0 else "#dc262622"
                styles.append(f"background-color:{bg}")
            else:
                styles.append("")
        return styles

    display_cols = ["ASIN","Product","Sales","Units","Gross Profit","Net Profit","Margin","Ads Cost","Real ACOS","Amazon Fees","COGS","Est. Payout","Refunds"]
    st.dataframe(
        asin_df[display_cols].style.apply(highlight_asin, axis=1),
        use_container_width=True,
        height=min(60 + len(asin_df) * 36, 600),
        hide_index=True,
    )

# ── FOOTER ──────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style='margin-top:2rem; padding-top:1rem; border-top:1px solid #1e2230;
     font-size:0.72rem; color:#475569; font-family:DM Mono,monospace;
     display:flex; justify-content:space-between;'>
  <span>P&L Dashboard · {SHEET_NAME}</span>
  <span>Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} · Cache 5 min</span>
</div>
""", unsafe_allow_html=True)
