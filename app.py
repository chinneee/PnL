import streamlit as st
import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, date

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="P&L Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CONSTANTS — EDIT THESE ─────────────────────────────────────────────────
SHEET_URL  = "https://docs.google.com/spreadsheets/d/1r6bWx_JlvEPn_YYszN8y6Wc8Q6Vm5FE-56aLHXhMSZk/edit?gid=837977405#gid=837977405"
SHEET_NAME = "TDSheet"

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

.dashboard-header { display: flex; align-items: center; gap: 12px; margin-bottom: 1.5rem; }
.dashboard-header h1 {
    font-size: 1.5rem; font-weight: 700; margin: 0;
    background: linear-gradient(90deg, #4f8ef7, #a78bfa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.dashboard-header .sub { font-size: 0.8rem; color: var(--muted); font-family: var(--mono); }

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

.section-title {
    font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: .1em; color: var(--muted);
    border-left: 3px solid var(--accent);
    padding-left: 10px; margin: 1.5rem 0 .75rem;
}

.stDataFrame { background: var(--surface) !important; }
.stDataFrame th {
    background: #1a1f2e !important;
    color: var(--muted) !important;
    font-family: var(--mono) !important;
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: .06em;
}
.stDataFrame td { font-family: var(--mono) !important; font-size: 0.82rem !important; }

div[data-testid="stSelectbox"] > div,
div[data-testid="stMultiSelect"] > div,
div[data-testid="stDateInput"] > div input {
    background: #1a1f2e !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
    border-radius: 8px !important;
}
label {
    color: var(--muted) !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: .07em !important;
}
div[data-testid="stAlert"] { border-radius: 10px; }

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: var(--surface);
    border-radius: 10px;
    padding: 4px;
    border: 1px solid var(--border);
    margin-bottom: 1rem;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px;
    color: var(--muted) !important;
    font-family: var(--mono) !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    padding: 6px 16px !important;
}
.stTabs [aria-selected="true"] {
    background: var(--accent) !important;
    color: white !important;
}
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

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def to_num(series):
    return pd.to_numeric(
        series.astype(str).str.replace(",", "").str.replace("%", ""),
        errors="coerce"
    ).fillna(0)

def fmt_usd(v):
    if abs(v) >= 1_000_000: return f"${v/1e6:.2f}M"
    if abs(v) >= 1_000:     return f"${v/1e3:.1f}K"
    return f"${v:,.2f}"

def fmt_pct(v): return f"{v:.1f}%"
def fmt_int(v): return f"{int(v):,}"
def color_class(v): return "pos" if v > 0 else ("neg" if v < 0 else "neu")

def kpi(label, value, sub="", cls="neu"):
    return f"""
    <div class='kpi-card'>
        <div class='kpi-label'>{label}</div>
        <div class='kpi-value {cls}'>{value}</div>
        <div class='kpi-sub'>{sub}</div>
    </div>"""

def get_date_range(option, custom_start=None, custom_end=None):
    today = date.today()
    if option == "Today":        return today, today
    if option == "Last 7 days":  return today - timedelta(days=6), today
    if option == "Last 14 days": return today - timedelta(days=13), today
    if option == "This month":   return today.replace(day=1), today
    if option == "Last month":
        first = today.replace(day=1)
        end   = first - timedelta(days=1)
        return end.replace(day=1), end
    if option == "Custom":       return custom_start, custom_end
    return None, None

# ─── BUILD P&L DICT FROM A DATAFRAME ─────────────────────────────────────────
def build_pnl(df):
    def s(col):
        return to_num(df[col]) if col in df.columns else pd.Series([0]*len(df))

    sales        = s("SalesOrganic") + s("SalesPPC") + s("SalesSponsoredProducts") + s("SalesSponsoredDisplay")
    units        = s("UnitsOrganic")  + s("UnitsPPC")  + s("UnitsSponsoredProducts")  + s("UnitsSponsoredDisplay")
    ads          = (s("SponsoredProducts") + s("SponsoredDisplay") +
                    s("SponsoredВrands")   + s("SponsoredBrandsVideo") +
                    s("Google ads")        + s("Facebook ads"))
    gross_profit = s("GrossProfit")
    net_profit   = s("NetProfit")

    rows = {}
    rows["Sales"]            = sales.sum()
    rows["Units"]            = units.sum()
    rows["Refunds (qty)"]    = s("Refunds").sum()
    rows["Promo"]            = s("PromoValue").sum()
    rows["Advertising cost"] = -abs(ads.sum())
    rows["Refund cost"]      = -abs(s("RefundCost").sum())
    rows["Amazon fees"]      = -abs(s("AmazonFees").sum())
    rows["Cost of goods"]    = -abs((s("ProductCost") + s("Cost of Goods")).sum())
    rows["Gross profit"]     = gross_profit.sum() if gross_profit.sum() != 0 else (
        rows["Sales"] + rows["Promo"] + rows["Advertising cost"] +
        rows["Refund cost"] + rows["Amazon fees"] + rows["Cost of goods"]
    )
    rows["Net profit"]       = net_profit.sum() if net_profit.sum() != 0 else rows["Gross profit"]
    rows["Estimated payout"] = s("EstimatedPayout").sum()
    rows["Sessions"]         = s("Sessions").sum()
    rows["Margin"]           = (rows["Net profit"] / rows["Sales"] * 100) if rows["Sales"] else 0
    rows["Real ACOS"]        = (abs(rows["Advertising cost"]) / rows["Sales"] * 100) if rows["Sales"] else 0
    return rows

MONEY_ROWS = {"Sales","Promo","Advertising cost","Refund cost","Amazon fees",
              "Cost of goods","Gross profit","Net profit","Estimated payout"}
PCT_ROWS   = {"Margin","Real ACOS"}
INT_ROWS   = {"Units","Refunds (qty)","Sessions"}

def format_val(key, val):
    if key in MONEY_ROWS: return fmt_usd(val)
    if key in PCT_ROWS:   return fmt_pct(val)
    if key in INT_ROWS:   return fmt_int(val)
    return str(round(val, 2))

def row_color(key, val):
    if key in {"Gross profit","Net profit","Margin"}:
        return color_class(val)
    if key in {"Advertising cost","Refund cost","Amazon fees","Cost of goods","Promo"}:
        return "neg" if val < 0 else "neu"
    return "neu"

P_AND_L_ORDER = [
    "Sales","Units","Refunds (qty)","Promo",
    "Advertising cost","Refund cost","Amazon fees","Cost of goods",
    "Gross profit","Net profit","Estimated payout",
    "Margin","Real ACOS","Sessions"
]

# ─── BUILD DAILY P&L TABLE ───────────────────────────────────────────────────
def build_daily_table(df):
    """Returns a wide DataFrame: rows = metrics, columns = dates"""
    if "_date_only" not in df.columns:
        return pd.DataFrame()

    dates = sorted(df["_date_only"].unique())
    records = {}

    for d in dates:
        day_df = df[df["_date_only"] == d]
        p = build_pnl(day_df)
        records[d] = p

    # Build: metric × date
    rows = []
    for key in P_AND_L_ORDER:
        row = {"Metric": key}
        for d in dates:
            row[str(d)] = records[d].get(key, 0)
        rows.append(row)

    return pd.DataFrame(rows), dates

def style_daily_cell(val, key):
    """Return background color string for a daily cell value"""
    try:
        v = float(str(val).replace("$","").replace("K","e3").replace("M","e6")
                  .replace("%","").replace(",",""))
    except:
        return ""
    cls = row_color(key, v)
    if cls == "pos": return "background-color:#16a34a22; color:#4ade80"
    if cls == "neg": return "background-color:#dc262622; color:#f87171"
    return ""

# ─── HEADER ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class='dashboard-header'>
    <div>
        <h1>📊 P&L Dashboard</h1>
        <div class='sub'>Amazon Seller Analytics · Live from Google Sheets</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── LOAD DATA ───────────────────────────────────────────────────────────────
df_raw, err = load_data()

if err:
    st.error(f"❌ Không kết nối được Google Sheet: {err}")
    st.info("💡 Kiểm tra lại:\n1. `SHEET_URL` và `SHEET_NAME` trong `app.py`\n2. Credentials trong Streamlit secrets\n3. Sheet đã share cho service account chưa")
    st.stop()

df_raw["_date"] = pd.to_datetime(df_raw["Date"], errors="coerce", dayfirst=True)
df_raw = df_raw.dropna(subset=["_date"])
df_raw["_date_only"] = df_raw["_date"].dt.date

# ─── FILTER BAR ──────────────────────────────────────────────────────────────
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

# ─── APPLY FILTERS ───────────────────────────────────────────────────────────
df = df_raw.copy()
if selected_asins:
    df = df[df["ASIN"].isin(selected_asins)]
if start_dt and end_dt:
    df = df[(df["_date_only"] >= start_dt) & (df["_date_only"] <= end_dt)]

if df.empty:
    st.warning("⚠️ Không có dữ liệu. Thử thay đổi date range hoặc ASIN.")
    st.stop()

# ─── KPI CARDS ───────────────────────────────────────────────────────────────
pnl = build_pnl(df)
st.markdown("<div class='section-title'>Overview</div>", unsafe_allow_html=True)

kpi_html = "<div class='kpi-grid'>"
kpi_html += kpi("Total Sales",       fmt_usd(pnl["Sales"]),            f"{fmt_int(pnl['Units'])} units", "neu")
kpi_html += kpi("Gross Profit",      fmt_usd(pnl["Gross profit"]),     "GP",            color_class(pnl["Gross profit"]))
kpi_html += kpi("Net Profit",        fmt_usd(pnl["Net profit"]),       fmt_pct(pnl["Margin"]) + " margin", color_class(pnl["Net profit"]))
kpi_html += kpi("Est. Payout",       fmt_usd(pnl["Estimated payout"]), "",              "pos" if pnl["Estimated payout"] > 0 else "neu")
kpi_html += kpi("Advertising Cost",  fmt_usd(pnl["Advertising cost"]), fmt_pct(pnl["Real ACOS"]) + " ACOS", "neg")
kpi_html += kpi("Amazon Fees",       fmt_usd(pnl["Amazon fees"]),      "", "neg")
kpi_html += kpi("Cost of Goods",     fmt_usd(pnl["Cost of goods"]),    "", "neg")
kpi_html += kpi("Refund Cost",       fmt_usd(pnl["Refund cost"]),      f"{fmt_int(pnl['Refunds (qty)'])} refunds", "neg")
kpi_html += kpi("Sessions",          fmt_int(pnl["Sessions"]),         "", "neu")
kpi_html += "</div>"
st.markdown(kpi_html, unsafe_allow_html=True)

# ─── 3 TABS ──────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📋  P&L Summary", "📅  Daily Breakdown", "🗂️  By ASIN"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — P&L SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("<div class='section-title'>P&L Summary — All Selected ASINs</div>", unsafe_allow_html=True)

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
        height=480,
        hide_index=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — DAILY BREAKDOWN
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("<div class='section-title'>Daily P&L Breakdown</div>", unsafe_allow_html=True)

    daily_df, dates = build_daily_table(df)

    if daily_df.empty:
        st.info("Không có dữ liệu theo ngày.")
    else:
        n_days = len(dates)

        # Info bar
        date_cols = [str(d) for d in dates]
        info_col1, info_col2, info_col3 = st.columns(3)
        info_col1.metric("Số ngày", f"{n_days} ngày")
        info_col2.metric("Từ", str(dates[0]) if dates else "—")
        info_col3.metric("Đến", str(dates[-1]) if dates else "—")

        st.markdown("")

        # Format display: apply format_val per row
        display_df = daily_df.copy()
        for idx, row in display_df.iterrows():
            key = row["Metric"]
            for col in date_cols:
                raw_val = row[col]
                display_df.at[idx, col] = format_val(key, raw_val)

        # Build styler with per-cell coloring
        def style_daily(df_style):
            # We need raw values from daily_df for color logic
            styles = pd.DataFrame("", index=df_style.index, columns=df_style.columns)
            for idx, row in daily_df.iterrows():
                key = row["Metric"]
                for col in date_cols:
                    raw_val = row[col]
                    cls = row_color(key, raw_val)
                    if cls == "pos":
                        styles.at[idx, col] = "background-color:#16a34a22; color:#4ade80"
                    elif cls == "neg":
                        styles.at[idx, col] = "background-color:#dc262622; color:#f87171"
            return styles

        # Metric column: bold
        def style_metric_col(df_style):
            styles = pd.DataFrame("", index=df_style.index, columns=df_style.columns)
            styles["Metric"] = "font-weight:600; color:#94a3b8"
            return styles

        styled = (
            display_df.style
            .apply(style_daily, axis=None)
            .apply(style_metric_col, axis=None)
        )

        # Dynamic height
        row_h = 35
        tbl_height = min(60 + len(daily_df) * row_h, 560)

        st.dataframe(
            styled,
            use_container_width=True,
            height=tbl_height,
            hide_index=True,
        )

        # ── Optional: show "Total" column alongside ──────────────────────────
        with st.expander("📊 Xem thêm: So sánh tổng theo metric"):
            total_col = {}
            for key in P_AND_L_ORDER:
                total_col[key] = pnl.get(key, 0)

            compare_rows = []
            for key in P_AND_L_ORDER:
                compare_rows.append({
                    "Metric": key,
                    "Total (period)": format_val(key, total_col[key]),
                    "Daily avg":      format_val(key, total_col[key] / n_days) if key not in PCT_ROWS else "—",
                    "Best day":       format_val(key, daily_df.set_index("Metric").loc[key, date_cols].astype(float).max()) if key not in PCT_ROWS else "—",
                    "Worst day":      format_val(key, daily_df.set_index("Metric").loc[key, date_cols].astype(float).min()) if key not in PCT_ROWS else "—",
                })

            st.dataframe(pd.DataFrame(compare_rows), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — BY ASIN
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("<div class='section-title'>P&L by ASIN</div>", unsafe_allow_html=True)

    if "ASIN" not in df.columns:
        st.info("Không tìm thấy cột ASIN trong dữ liệu.")
    else:
        asin_records = []
        for asin, grp in df.groupby("ASIN", sort=False):
            p = build_pnl(grp)
            name = ""
            if "Name" in grp.columns:
                vals = grp["Name"].dropna()
                name = vals.iloc[0] if len(vals) > 0 else ""
            name_short = (str(name)[:40] + "…") if len(str(name)) > 40 else str(name)

            asin_records.append({
                "ASIN":         asin,
                "Product":      name_short,
                "Sales":        fmt_usd(p["Sales"]),
                "Units":        fmt_int(p["Units"]),
                "Gross Profit": fmt_usd(p["Gross profit"]),
                "Net Profit":   fmt_usd(p["Net profit"]),
                "Margin":       fmt_pct(p["Margin"]),
                "Ads Cost":     fmt_usd(p["Advertising cost"]),
                "Real ACOS":    fmt_pct(p["Real ACOS"]),
                "Amazon Fees":  fmt_usd(p["Amazon fees"]),
                "COGS":         fmt_usd(p["Cost of goods"]),
                "Est. Payout":  fmt_usd(p["Estimated payout"]),
                "Refunds":      fmt_int(p["Refunds (qty)"]),
                "_net":         p["Net profit"],
                "_margin":      p["Margin"],
            })

        asin_df = pd.DataFrame(asin_records).sort_values("_net", ascending=False)

        def highlight_asin(row):
            styles = []
            for col in asin_df.columns:
                if col == "Net Profit":
                    v = asin_df.loc[row.name, "_net"]
                    styles.append("background-color:#16a34a22; color:#4ade80" if v > 0 else "background-color:#dc262622; color:#f87171")
                elif col == "Margin":
                    v = asin_df.loc[row.name, "_margin"]
                    styles.append("background-color:#16a34a22; color:#4ade80" if v > 0 else "background-color:#dc262622; color:#f87171")
                else:
                    styles.append("")
            return styles

        display_cols = ["ASIN","Product","Sales","Units","Gross Profit","Net Profit",
                        "Margin","Ads Cost","Real ACOS","Amazon Fees","COGS","Est. Payout","Refunds"]
        st.dataframe(
            asin_df[display_cols].style.apply(highlight_asin, axis=1),
            use_container_width=True,
            height=min(60 + len(asin_df) * 36, 600),
            hide_index=True,
        )

# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style='margin-top:2rem; padding-top:1rem; border-top:1px solid #1e2230;
     font-size:0.72rem; color:#475569; font-family:DM Mono,monospace;
     display:flex; justify-content:space-between;'>
  <span>P&L Dashboard · {SHEET_NAME}</span>
  <span>Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} · Cache 5 min</span>
</div>
""", unsafe_allow_html=True)
