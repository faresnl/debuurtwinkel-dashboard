"""Interactive De Buurtwinkel dashboard, recreated from DeBuurtwinkel.pbit metadata.

Streamlit cannot execute .pbit files. This program implements the identified
pages, measures, and relationships with Python, using the original three CSVs.
"""
from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
REQUIRED = ("sales_data.csv", "product_details.csv", "store_locations.csv")
BLUE = "#118DFF"
NAVY = "#12239E"
ORANGE = "#E66C37"

st.set_page_config(page_title="De Buurtwinkel | Sales Dashboard", page_icon="🛒", layout="wide")
st.markdown("""<style>
.block-container {padding-top:1.3rem; max-width:1450px;}
[data-testid="stMetric"] {background: #f3f7fc; padding: 1rem; border-radius: .8rem;
  border: 1px solid #dfe8f4;}
</style>""", unsafe_allow_html=True)


def read_csv(payload: bytes) -> pd.DataFrame:
    last_error = None
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return pd.read_csv(io.BytesIO(payload), encoding=enc)
        except (UnicodeDecodeError, ValueError) as exc:
            last_error = exc
    raise ValueError(f"Could not decode CSV: {last_error}")


def load_tables(files: dict[str, bytes]) -> pd.DataFrame:
    sales = read_csv(files["sales_data.csv"])
    products = read_csv(files["product_details.csv"])
    stores = read_csv(files["store_locations.csv"])

    needed = {
        "sales_data.csv": (sales, {"TransactionID", "Date", "ProductID", "StoreID", "UnitsSold"}),
        "product_details.csv": (products, {"ProductID", "ProductName", "ProductCategory", "UnitPrice", "UnitCost"}),
        "store_locations.csv": (stores, {"StoreID", "City", "Province"}),
    }
    for fname, (table, columns) in needed.items():
        missing = columns - set(table.columns)
        if missing:
            raise ValueError(f"{fname} is missing columns: {', '.join(sorted(missing))}")

    sales["Date"] = pd.to_datetime(sales["Date"], errors="coerce", dayfirst=False)
    sales["UnitsSold"] = pd.to_numeric(sales["UnitsSold"], errors="coerce")
    for col in ("UnitPrice", "UnitCost"):
        products[col] = pd.to_numeric(products[col], errors="coerce")
    sales = sales.dropna(subset=["Date", "UnitsSold", "ProductID", "StoreID"])

    # Same relationships and calculated columns as the PBIT's Power Query steps.
    # Avoid duplicate Product/Store keys creating duplicate sales rows.
    if products["ProductID"].duplicated().any():
        raise ValueError("product_details.csv has duplicate ProductID values")
    if stores["StoreID"].duplicated().any():
        raise ValueError("store_locations.csv has duplicate StoreID values")
    sales = sales.merge(products, on="ProductID", how="left", validate="many_to_one")
    sales = sales.merge(stores, on="StoreID", how="left", validate="many_to_one")
    sales["Revenue"] = sales["UnitsSold"] * sales["UnitPrice"]
    sales["TotalCost"] = sales["UnitsSold"] * sales["UnitCost"]
    sales["Profit"] = sales["Revenue"] - sales["TotalCost"]
    return sales


def money(value: float) -> str:
    return f"€{value:,.2f}"


def layout_chart(fig: go.Figure, height: int = 310) -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=12, r=12, t=40, b=14),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(size=12), legend=dict(orientation="h", y=-0.22))
    return fig


# A province-centre bubble map is used because the source data has no coordinates.
# Positions are indicative province centers, not store addresses.
PROVINCES = {
    "groningen": (53.21, 6.57),
    "friesland": (53.15, 5.80), "fryslân": (53.15, 5.80),
    "drenthe": (52.90, 6.62), "overijssel": (52.50, 6.25),
    "flevoland": (52.52, 5.50), "gelderland": (52.05, 5.90),
    "utrecht": (52.09, 5.12),
    "noord-holland": (52.64, 4.82), "north holland": (52.64, 4.82),
    "zuid-holland": (52.04, 4.49), "south holland": (52.04, 4.49),
    "zeeland": (51.50, 3.85),
    "noord-brabant": (51.60, 5.12), "north brabant": (51.60, 5.12),
    "limburg": (51.20, 5.96),
}


def province_map(df: pd.DataFrame) -> None:
    summed = df.groupby("Province", dropna=False, as_index=False)["Revenue"].sum()
    summed["_coords"] = summed["Province"].fillna("").astype(str).str.casefold().str.strip().map(PROVINCES)
    mapped = summed.dropna(subset=["_coords"]).copy()
    if mapped.empty:
        st.info("No province coordinates in the offline lookup. Showing revenue by province instead.")
        fig = px.bar(summed, x="Province", y="Revenue", color_discrete_sequence=[BLUE])
        st.plotly_chart(layout_chart(fig), width="stretch")
        return
    mapped["lat"] = mapped["_coords"].apply(lambda x: x[0])
    mapped["lon"] = mapped["_coords"].apply(lambda x: x[1])
    fig = px.scatter_map(mapped, lat="lat", lon="lon", size="Revenue", color="Revenue",
                         hover_name="Province", hover_data={"Revenue": ":,.2f", "lat": False, "lon": False},
                         zoom=5.9, center={"lat": 52.25, "lon": 5.45},
                         map_style="carto-positron", color_continuous_scale="Blues", size_max=35)
    st.plotly_chart(layout_chart(fig), width="stretch")
    st.caption("Bubbles show approximate province centres (not precise store locations).")
    missing = summed[summed["_coords"].isna()]["Province"].astype(str).tolist()
    if missing:
        st.caption("Not mapped: " + ", ".join(missing))


st.title("🛒 De Buurtwinkel")
st.image(str(ROOT / "assets" / "supermarket_banner.jpg"), width="stretch")
st.caption("Interactive Streamlit recreation based on your Power BI template • Data loads automatically")

# Load datasets automatically from the deployed project. Visitors never upload files.
DATA_DIR = ROOT / "data"
files: dict[str, bytes] = {}
for filename in REQUIRED:
    source = DATA_DIR / filename
    if source.is_file():
        files[filename] = source.read_bytes()

missing_files = [name for name in REQUIRED if name not in files]
if missing_files:
    st.error("This deployment is missing its original CSV data files.")
    st.write("**Required files in the app's `data/` folder:**")
    for filename in missing_files:
        st.code(f"data/{filename}", language="text")
    st.info("The app owner must add the three original CSV files to the project and redeploy. "
            "Visitors cannot upload data here, and this report template contains no sales records.")
    st.stop()

try:
    whole = load_tables(files)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

if whole.empty:
    st.warning("The CSV files loaded, but contain no usable sales rows.")
    st.stop()

categories = sorted(whole["ProductCategory"].dropna().astype(str).unique().tolist())
min_date = whole["Date"].min().date()
max_date = whole["Date"].max().date()
with st.sidebar:
    st.header("Dashboard slicers")
    chosen_categories = st.multiselect("Product category", categories, default=categories)
    date_selection = st.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

filtered = whole[whole["ProductCategory"].isin(chosen_categories)].copy()
if isinstance(date_selection, tuple) and len(date_selection) == 2:
    start, end = date_selection
    filtered = filtered[(filtered["Date"].dt.date >= start) & (filtered["Date"].dt.date <= end)]
else:
    start, end = min_date, max_date

revenue = float(filtered["Revenue"].sum())
profit = float(filtered["Profit"].sum())
margin = profit / revenue if revenue else 0.0

# DAX SAMEPERIODLASTYEAR equivalent for a selected date range and category.
last_year_start = (pd.Timestamp(start) - pd.DateOffset(years=1)).date()
last_year_end = (pd.Timestamp(end) - pd.DateOffset(years=1)).date()
previous = whole[
    (whole["ProductCategory"].isin(chosen_categories))
    & (whole["Date"].dt.date >= last_year_start)
    & (whole["Date"].dt.date <= last_year_end)
]
prev_revenue = float(previous["Revenue"].sum())
yoy = (revenue - prev_revenue) / prev_revenue if prev_revenue else 0.0

page_sales, page_one, page_data = st.tabs(["Sales Dashboard", "Page 1", "About the metrics"])

with page_sales:
    st.subheader("Retail Sales Analysis")
    k1, k2, k3 = st.columns(3)
    k1.metric("Total Revenue", money(revenue))
    k2.metric("Total Profit", money(profit))
    k3.metric("Profit Margin %", f"{margin:.1%}")

    c1, c2 = st.columns([1.15, 1], gap="large")
    with c1:
        st.markdown("**Revenue by month**")
        months = filtered.copy()
        months["Month"] = months["Date"].dt.to_period("M").dt.to_timestamp()
        monthly = months.groupby("Month", as_index=False)["Revenue"].sum()
        fig = px.line(monthly, x="Month", y="Revenue", markers=True,
                      color_discrete_sequence=[BLUE], labels={"Month": "Months", "Revenue": "Revenue (€)"})
        st.plotly_chart(layout_chart(fig), width="stretch")
    with c2:
        st.markdown("**Profit by product category**")
        grouped = filtered.groupby("ProductCategory", as_index=False)["Profit"].sum().sort_values("Profit")
        fig = px.bar(grouped, x="Profit", y="ProductCategory", orientation="h",
                     color_discrete_sequence=[NAVY], labels={"ProductCategory": "Product category", "Profit": "Profit (€)"})
        st.plotly_chart(layout_chart(fig), width="stretch")
    st.markdown("**Revenue by province**")
    province_map(filtered)

with page_one:
    st.subheader("Page 1")
    a, b, c = st.columns(3, gap="medium")
    with a:
        st.markdown("**Units sold by product**")
        products = filtered.groupby("ProductName", as_index=False)["UnitsSold"].sum().sort_values("UnitsSold", ascending=False)
        st.dataframe(products, height=320, hide_index=True, width="stretch")
    with b:
        st.markdown("**Revenue over time**")
        daily = filtered.groupby("Date", as_index=False)["Revenue"].sum()
        fig = px.line(daily, x="Date", y="Revenue", color_discrete_sequence=[BLUE])
        st.plotly_chart(layout_chart(fig, 320), width="stretch")
    with c:
        st.markdown("**Total Revenue**")
        fig = px.bar(pd.DataFrame({"Measure": ["Revenue"], "Value": [revenue]}), x="Measure", y="Value",
                     color_discrete_sequence=[NAVY])
        st.plotly_chart(layout_chart(fig, 320), width="stretch")

    d, e, f = st.columns(3, gap="medium")
    with d:
        st.markdown("**Year-over-year revenue growth**")
        st.metric("YoY Revenue Growth %", f"{yoy:.1%}")
        if not prev_revenue:
            st.caption("No revenue for the previous-year comparison period. DAX DIVIDE(..., 0) returns 0.")
    with e:
        st.markdown("**Total Profit**")
        fig = go.Figure(go.Indicator(mode="gauge+number", value=profit, number={"prefix": "€", "valueformat": ",.0f"},
                                      gauge={"axis": {"range": [min(0, profit), max(revenue, profit, 1)]},
                                             "bar": {"color": BLUE}}))
        st.plotly_chart(layout_chart(fig, 310), width="stretch")
    with f:
        st.markdown("**Profit Margin %**")
        share = min(100, max(0, margin * 100))
        fig = go.Figure(go.Pie(values=[share, 100 - share], labels=["Profit", "Remaining"], hole=0.65,
                               marker={"colors": [BLUE, "#D9E4F2"]}, sort=False))
        st.plotly_chart(layout_chart(fig, 310), width="stretch")
        if margin < 0 or margin > 1:
            st.caption("The donut is clamped to 0–100%; the actual profit margin is in the KPI.")

with page_data:
    st.write("**Measures reproduced from the Power BI template**")
    st.code("Total Revenue = SUM(sales_data[Revenue])\nTotal Profit = [Total Revenue] - SUM(sales_data[TotalCost])\nProfit Margin % = DIVIDE([Total Profit], [Total Revenue], 0)\nYoY Revenue Growth % = compared with same period last year", language="text")
    st.caption("The date-range comparison approximates SAMEPERIODLASTYEAR; exact DAX filter semantics may differ.")
    st.caption("Raw transaction records are not downloadable from this public-facing dashboard.")

st.caption("Reconstructed using the actual DeBuurtwinkel.pbit page and model definitions. Does not execute Power BI or the original .pbit file.")
