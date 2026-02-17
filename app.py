import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Kenyan University Student Performance", layout="wide")


st.markdown("""
<style>
.block-container{padding-top:1rem;}
.hero{
  border-radius:22px;
  padding:22px;
  background:linear-gradient(135deg,#6366f1,#10b981);
  color:#fff;
  border:1px solid rgba(255,255,255,.15);
}
.hero h1{margin:0;font-size:1.7rem;line-height:1.2;}
.hero p{margin:8px 0 0;opacity:.92;}
.panel{
  border-radius:18px;
  padding:14px;
  background:rgba(255,255,255,.03);
  border:1px solid rgba(255,255,255,.09);
}
div[data-testid="stMetric"]{
  background:rgba(255,255,255,.04);
  padding:12px;
  border-radius:16px;
  border:1px solid rgba(255,255,255,.10);
}
.small-muted{opacity:.75;font-size:.9rem;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>🇰🇪 Kenyan Universities Student Performance Dashboard</h1>
  <p>Modern analytics dashboard for academic performance and wellbeing insights</p>
</div>
""", unsafe_allow_html=True)


REQUIRED_COLS = [
    "FirstName","LastName","University","Campus","School","Program",
    "YearOfStudy","Gender","Age","County","AttendanceRate","StudyHoursPerWeek",
    "GPA","MentalWellbeingScore","FinancialStressScore","CreditsRegistered"
]

FILTER_COLS = ["University","Campus","School","Program","YearOfStudy","Gender","County"]
NUM_COLS = [
    "Age","AttendanceRate","StudyHoursPerWeek","GPA",
    "MentalWellbeingScore","FinancialStressScore","CreditsRegistered"
]

def performance_band(gpa: float) -> str:
    if pd.isna(gpa):
        return "Unknown"
    if gpa >= 3.7:
        return "Excellent (3.7+)"
    if gpa >= 3.0:
        return "Good (3.0–3.69)"
    if gpa >= 2.0:
        return "Average (2.0–2.99)"
    return "At Risk (<2.0)"

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, header=0)
    df.columns = [c.strip() for c in df.columns]

    for c in NUM_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


PATH = "student_performance_kenya.csv"
df = load_data(PATH)

missing = [c for c in REQUIRED_COLS if c not in df.columns]
if missing:
    st.error("❌ One or more required columns are missing in your CSV.")
    st.write("**Missing columns:**", missing)
    st.write("**Columns detected:**", list(df.columns))
    st.stop()

df["FullName"] = df["FirstName"].astype(str).str.strip() + " " + df["LastName"].astype(str).str.strip()
df["PerformanceBand"] = df["GPA"].apply(performance_band)


st.sidebar.header("🔎 Filters")

if st.sidebar.button("↩ Reset filters"):
    st.session_state.clear()
    st.rerun()

filtered = df.copy()

for col in FILTER_COLS:
    options = sorted(filtered[col].dropna().unique().tolist())
    default = options[:]  
    selected = st.sidebar.multiselect(col, options, default=default, key=f"f_{col}")
    if selected:
        filtered = filtered[filtered[col].isin(selected)]

def safe_min_max(series, fallback_min, fallback_max):
    s = series.dropna()
    if s.empty:
        return fallback_min, fallback_max
    return float(s.min()), float(s.max())

gpa_min, gpa_max = safe_min_max(df["GPA"], 0.0, 4.0)
att_min, att_max = safe_min_max(df["AttendanceRate"], 0.0, 100.0)
hrs_min, hrs_max = safe_min_max(df["StudyHoursPerWeek"], 0.0, 80.0)

gpa_range = st.sidebar.slider("GPA Range", 0.0, 4.0, (max(0.0, gpa_min), min(4.0, gpa_max)), 0.01, key="gpa_range")
att_range = st.sidebar.slider("Attendance Range (%)", 0.0, 100.0, (max(0.0, att_min), min(100.0, att_max)), 0.5, key="att_range")
hrs_range = st.sidebar.slider("Study Hours / Week", 0.0, max(10.0, hrs_max), (max(0.0, hrs_min), max(10.0, hrs_max)), 0.5, key="hrs_range")

filtered = filtered[
    filtered["GPA"].between(gpa_range[0], gpa_range[1], inclusive="both")
    & filtered["AttendanceRate"].between(att_range[0], att_range[1], inclusive="both")
    & filtered["StudyHoursPerWeek"].between(hrs_range[0], hrs_range[1], inclusive="both")
]

bands = sorted(df["PerformanceBand"].dropna().unique().tolist())
selected_bands = st.sidebar.multiselect("Performance Band", bands, default=bands, key="bands")
filtered = filtered[filtered["PerformanceBand"].isin(selected_bands)]


st.write("")
k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Students", f"{len(filtered):,}")
k2.metric("Avg GPA", f"{filtered['GPA'].mean():.2f}" if filtered["GPA"].notna().any() else "N/A")
k3.metric("Avg Attendance", f"{filtered['AttendanceRate'].mean():.1f}%" if filtered["AttendanceRate"].notna().any() else "N/A")
k4.metric("Avg Study Hours", f"{filtered['StudyHoursPerWeek'].mean():.1f}" if filtered["StudyHoursPerWeek"].notna().any() else "N/A")
k5.metric("At Risk", int((filtered["PerformanceBand"] == "At Risk (<2.0)").sum()))

st.markdown('<p class="small-muted">Tip: Use the sidebar to drill down by campus, program, county, and year of study.</p>', unsafe_allow_html=True)

st.divider()


tab1, tab2, tab3 = st.tabs(["📌 Overview", "📈 Charts", "🧾 Data"])

with tab1:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("Performance Band Distribution")
    band_counts = filtered["PerformanceBand"].value_counts().reset_index()
    band_counts.columns = ["PerformanceBand", "Count"]
    fig_band = px.bar(band_counts, x="PerformanceBand", y="Count")
    st.plotly_chart(fig_band, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("Top Programs by Average GPA (Top 15)")
    gpa_by_program = (
        filtered.groupby("Program", dropna=True)["GPA"]
        .mean()
        .sort_values(ascending=False)
        .head(15)
        .reset_index()
    )
    fig_prog = px.bar(gpa_by_program, x="Program", y="GPA")
    st.plotly_chart(fig_prog, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("Attendance vs GPA")
        fig1 = px.scatter(
            filtered,
            x="AttendanceRate",
            y="GPA",
            color="PerformanceBand",
            hover_data=["FullName","University","Campus","Program","YearOfStudy"]
        )
        st.plotly_chart(fig1, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("GPA Distribution")
        fig2 = px.histogram(filtered, x="GPA", nbins=14)
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    c3, c4 = st.columns(2)

    with c3:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("Wellbeing vs Financial Stress")
        fig3 = px.scatter(
            filtered,
            x="FinancialStressScore",
            y="MentalWellbeingScore",
            hover_data=["FullName","University","Program"],
        )
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c4:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("Credits Registered vs GPA")
        fig4 = px.scatter(
            filtered,
            x="CreditsRegistered",
            y="GPA",
            hover_data=["FullName","University","Program"],
        )
        st.plotly_chart(fig4, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.subheader("Filtered Student Records")
    st.dataframe(filtered, use_container_width=True, height=460)

    st.download_button(
        "⬇️ Download Filtered Data",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="kenyan_students_filtered.csv",
        mime="text/csv"
    )
