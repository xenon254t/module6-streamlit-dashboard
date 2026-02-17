import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Advanced Interactive Dashboard", layout="wide")

st.title("📊 Advanced Interactive Dashboard (Module 6)")
st.caption("Upload data → filter in sidebar → view KPIs → explore multiple interactive charts → download results")


@st.cache_data
def load_data(file) -> pd.DataFrame:
    name = file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(file)
    if name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(file)
    raise ValueError("Unsupported file type. Upload CSV or Excel.")

def to_datetime_safe(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce", utc=False)

def is_datetime_col(s: pd.Series) -> bool:
    if pd.api.types.is_datetime64_any_dtype(s):
        return True
    if s.dtype == "object":
        sample = s.dropna().astype(str).head(50)
        if len(sample) == 0:
            return False
        parsed = pd.to_datetime(sample, errors="coerce")
        return parsed.notna().mean() >= 0.6
    return False


uploaded = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx", "xls"])

if uploaded is None:
    st.info("No file uploaded. Using demo dataset (Gapminder).")
    df = px.data.gapminder()
else:
    df = load_data(uploaded)
df.columns = [str(c).strip() for c in df.columns]

num_cols = df.select_dtypes(include="number").columns.tolist()
cat_cols = df.select_dtypes(exclude="number").columns.tolist()

datetime_cols = []
for c in df.columns:
    if is_datetime_col(df[c]):
        datetime_cols.append(c)

for c in datetime_cols:
    if not pd.api.types.is_datetime64_any_dtype(df[c]):
        df[c] = to_datetime_safe(df[c])

cat_cols = [c for c in df.columns if c not in num_cols and c not in datetime_cols]


st.sidebar.header("🧰 Filters & Controls")

search = st.sidebar.text_input("Global search (matches any column)", "").strip()

cat_filter_cols = []
if len(cat_cols) > 0:
    st.sidebar.subheader("Categorical filters")
    cat_filter_cols = st.sidebar.multiselect(
        "Pick categorical columns to filter (up to 3)",
        options=cat_cols,
        default=cat_cols[:1] if len(cat_cols) else []
    )[:3]

st.sidebar.subheader("Numeric filters")
num_filter_cols = []
if len(num_cols) > 0:
    num_filter_cols = st.sidebar.multiselect(
        "Pick numeric columns for range filters (up to 2)",
        options=num_cols,
        default=num_cols[:1] if len(num_cols) else []
    )[:2]

date_col = None
if len(datetime_cols) > 0:
    st.sidebar.subheader("Date filter")
    date_col = st.sidebar.selectbox("Date column (optional)", ["(none)"] + datetime_cols, index=0)
    if date_col == "(none)":
        date_col = None

filtered = df.copy()

cat_selections = {}
for c in cat_filter_cols:
    values = sorted(filtered[c].dropna().astype(str).unique().tolist())
    selected = st.sidebar.multiselect(f"{c}", options=values, default=values[: min(10, len(values))])
    cat_selections[c] = selected
    if selected:
        filtered = filtered[filtered[c].astype(str).isin(selected)]

# Numeric range filters
num_ranges = {}
for c in num_filter_cols:
    col = filtered[c].dropna()
    if len(col) == 0:
        continue
    mn, mx = float(col.min()), float(col.max())
    if mn == mx:
        num_ranges[c] = (mn, mx)
        continue
    r = st.sidebar.slider(f"{c} range", min_value=mn, max_value=mx, value=(mn, mx))
    num_ranges[c] = r
    filtered = filtered[(filtered[c] >= r[0]) & (filtered[c] <= r[1])]

date_range = None
if date_col:
    d = filtered[date_col].dropna()
    if len(d) > 0:
        dmin, dmax = d.min(), d.max()
        picked = st.sidebar.date_input(
            f"{date_col} range",
            value=(dmin.date(), dmax.date()),
            min_value=dmin.date(),
            max_value=dmax.date()
        )
        if isinstance(picked, tuple) and len(picked) == 2:
            start, end = picked
            date_range = (pd.to_datetime(start), pd.to_datetime(end) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1))
            filtered = filtered[(filtered[date_col] >= date_range[0]) & (filtered[date_col] <= date_range[1])]

if search:
    mask = filtered.astype(str).apply(
        lambda row: row.str.contains(search, case=False, na=False)
    ).any(axis=1)
    filtered = filtered[mask]
st.subheader("📌 Key Metrics (KPIs)")

missing_total = int(filtered.isna().sum().sum())
rows = len(filtered)
cols = filtered.shape[1]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Rows", f"{rows:,}")
k2.metric("Columns", f"{cols:,}")
k3.metric("Missing values", f"{missing_total:,}")
k4.metric("Numeric columns", f"{len(num_cols):,}")

if len(num_cols) > 0:
    metric_col = st.selectbox("Select a numeric column for KPI stats", options=num_cols, index=0)
    s = filtered[metric_col].dropna()

    a1, a2, a3, a4, a5, a6 = st.columns(6)
    if len(s) == 0:
        a1.metric("Sum", "—")
        a2.metric("Avg", "—")
        a3.metric("Median", "—")
        a4.metric("Min", "—")
        a5.metric("Max", "—")
        a6.metric("Std Dev", "—")
    else:
        a1.metric("Sum", f"{s.sum():,.2f}")
        a2.metric("Avg", f"{s.mean():,.2f}")
        a3.metric("Median", f"{s.median():,.2f}")
        a4.metric("Min", f"{s.min():,.2f}")
        a5.metric("Max", f"{s.max():,.2f}")
        a6.metric("Std Dev", f"{s.std():,.2f}")

st.divider()


st.subheader("📈 Interactive Visualizations")

if rows == 0:
    st.warning("No data after filters. Adjust your filters in the sidebar.")
    st.stop()

chart_tab1, chart_tab2, chart_tab3 = st.tabs(["Distribution & Comparison", "Trends & Relationships", "Correlation"])

with chart_tab1:
    left, right = st.columns([1.1, 1])

    with left:
        st.markdown("### Distribution")
        fig_hist = px.histogram(filtered, x=metric_col, nbins=35, title=f"Histogram: {metric_col}")
        st.plotly_chart(fig_hist, use_container_width=True)

    with right:
        st.markdown("### Box Plot")
        fig_box = px.box(filtered, y=metric_col, title=f"Box Plot: {metric_col}")
        st.plotly_chart(fig_box, use_container_width=True)

    st.markdown("### Grouped Bar (optional)")
    if len(cat_cols) > 0:
        group_col = st.selectbox("Group by", options=cat_cols, index=0)
        agg = st.selectbox("Aggregation", options=["sum", "mean", "count"], index=0)

        if agg == "count":
            summary = filtered.groupby(group_col, dropna=False).size().reset_index(name="count")
            fig_bar = px.bar(summary, x=group_col, y="count", title=f"Count by {group_col}")
        else:
            summary = filtered.groupby(group_col, dropna=False)[metric_col].agg(agg).reset_index()
            fig_bar = px.bar(summary, x=group_col, y=metric_col, title=f"{agg.title()} of {metric_col} by {group_col}")

        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No categorical columns detected for grouped charts.")

with chart_tab2:
    st.markdown("### Scatter Plot")
    if len(num_cols) >= 2:
        x_col = st.selectbox("X-axis", options=num_cols, index=0)
        y_col = st.selectbox("Y-axis", options=[c for c in num_cols if c != x_col], index=0)

        color_col = None
        if len(cat_cols) > 0:
            color_col = st.selectbox("Color (optional)", options=["(none)"] + cat_cols, index=0)
            if color_col == "(none)":
                color_col = None

        fig_scatter = px.scatter(filtered, x=x_col, y=y_col, color=color_col, title=f"{y_col} vs {x_col}")
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("Need at least 2 numeric columns for a scatter plot.")

    st.markdown("### Line Chart (time series)")
    if date_col and len(num_cols) > 0:
        time_metric = st.selectbox("Time metric", options=num_cols, index=0)
        # sort by time
        ts = filtered.dropna(subset=[date_col]).sort_values(date_col)
        if len(ts) == 0:
            st.info("No valid date rows after filtering.")
        else:
            fig_line = px.line(ts, x=date_col, y=time_metric, title=f"{time_metric} over time ({date_col})")
            st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Choose a date column in the sidebar to enable time-series chart.")

with chart_tab3:
    st.markdown("### Correlation Heatmap (numeric only)")
    if len(num_cols) >= 2:
        corr_cols = st.multiselect("Pick numeric columns", options=num_cols, default=num_cols[: min(8, len(num_cols))])
        if len(corr_cols) >= 2:
            corr = filtered[corr_cols].corr(numeric_only=True)
            fig_heat = px.imshow(corr, text_auto=True, title="Correlation Matrix")
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.info("Pick at least 2 numeric columns.")
    else:
        st.info("Need at least 2 numeric columns for correlation heatmap.")

st.divider()

st.subheader("🗂️ Filtered Dataset")

st.dataframe(filtered, use_container_width=True, height=380)

csv_bytes = filtered.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download filtered CSV", data=csv_bytes, file_name="filtered_data.csv", mime="text/csv")

if len(cat_cols) > 0 and len(num_cols) > 0:
    st.subheader("📌 Download a grouped summary (optional)")
    sum_group = st.selectbox("Summary group column", options=cat_cols, index=0, key="sum_group")
    sum_metric = st.selectbox("Summary metric column", options=num_cols, index=0, key="sum_metric")
    sum_agg = st.selectbox("Summary aggregation", options=["sum", "mean", "count", "median"], index=0, key="sum_agg")

    if sum_agg == "count":
        summary_df = filtered.groupby(sum_group, dropna=False).size().reset_index(name="count")
    else:
        summary_df = filtered.groupby(sum_group, dropna=False)[sum_metric].agg(sum_agg).reset_index()

    st.dataframe(summary_df, use_container_width=True, height=250)

    summary_bytes = summary_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download summary CSV", data=summary_bytes, file_name="summary_data.csv", mime="text/csv")

st.caption("Tip: For best results, upload datasets with at least one numeric column and (optional) a date column.")
