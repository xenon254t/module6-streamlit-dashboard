import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Module 6 Dashboard", layout="wide")
st.title("📊 Module 6 Interactive Dashboard")

st.write("Upload a dataset (CSV) and explore it interactively.")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    st.subheader("Preview")
    st.dataframe(df, use_container_width=True)

    st.sidebar.header("Controls")

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(exclude="number").columns.tolist()

    if len(cat_cols) > 0:
        filter_col = st.sidebar.selectbox("Filter column (optional)", ["(none)"] + cat_cols)
        if filter_col != "(none)":
            vals = st.sidebar.multiselect(
                f"Select {filter_col} values",
                sorted(df[filter_col].dropna().astype(str).unique().tolist())
            )
            if vals:
                df = df[df[filter_col].astype(str).isin(vals)]

    if len(numeric_cols) == 0:
        st.warning("No numeric columns found in this dataset.")
    else:
        metric = st.sidebar.selectbox("Metric column", numeric_cols)

        c1, c2, c3 = st.columns(3)
        c1.metric("Rows", f"{len(df):,}")
        c2.metric("Average", f"{df[metric].mean():,.2f}")
        c3.metric("Sum", f"{df[metric].sum():,.2f}")

        st.subheader("Chart")
        chart_type = st.radio("Choose chart type", ["Histogram", "Box Plot"], horizontal=True)

        if chart_type == "Histogram":
            fig = px.histogram(df, x=metric, nbins=30)
        else:
            fig = px.box(df, y=metric)

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Download filtered data")
        st.download_button(
            "⬇️ Download CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="filtered_data.csv",
            mime="text/csv"
        )
else:
    st.info("Upload a CSV file to start.")
