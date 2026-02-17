import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Kenyan University Student Performance", layout="wide")

st.markdown("""
<style>
.block-container { padding-top: 1rem; }
.hero {
    border-radius: 20px;
    padding: 20px;
    background: linear-gradient(135deg, #6366f1, #10b981);
    color: white;
}
.hero h1 { margin: 0; font-size: 1.6rem; }
.hero p { margin: 5px 0 0; opacity: 0.9; }
div[data-testid="stMetric"] {
    background: rgba(255,255,255,.05);
    padding: 12px;
    border-radius: 15px;
    border: 1px solid rgba(255,255,255,.1);
}
.panel {
    border-radius: 18px;
    padding: 15px;
    background: rgba(255,255,255,.03);
    border: 1px solid rgba(255,255,255,.08);
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
<h1>🇰🇪 Kenyan Universities Student Performance Dashboard</h1>
<p>Modern analytics dashboard for academic performance and wellbeing insights</p>
</div>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    return pd.read_csv("student_performance_kenya.csv")

df = load_data()

def performance_band(gpa):
    if gpa >= 3.6:
        return "Excellent"
    elif gpa >= 3.2:
        return "Good"
    elif gpa >= 2.7:
        return "Fair"
    else:
        return "At Risk"

df["PerformanceBand"] = df["GPA"].apply(performance_band)

st.sidebar.header("Filters")

universities = st.sidebar.multiselect("University", df["University"].unique(), default=df["University"].unique())
year = st.sidebar.multiselect("Year Of Study", df["YearOfStudy"].unique(), default=df["YearOfStudy"].unique())
gender = st.sidebar.multiselect("Gender", df["Gender"].unique(), default=df["Gender"].unique())
gpa_range = st.sidebar.slider("GPA Range", float(df["GPA"].min()), float(df["GPA"].max()), (float(df["GPA"].min()), float(df["GPA"].max())))
attendance_range = st.sidebar.slider("Attendance Range", float(df["AttendanceRate"].min()), float(df["AttendanceRate"].max()), (float(df["AttendanceRate"].min()), float(df["AttendanceRate"].max())))

filtered = df[
    df["University"].isin(universities) &
    df["YearOfStudy"].isin(year) &
    df["Gender"].isin(gender) &
    (df["GPA"] >= gpa_range[0]) &
    (df["GPA"] <= gpa_range[1]) &
    (df["AttendanceRate"] >= attendance_range[0]) &
    (df["AttendanceRate"] <= attendance_range[1])
]

st.write("")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Students", len(filtered))
col2.metric("Average GPA", round(filtered["GPA"].mean(), 2))
col3.metric("Average Attendance", round(filtered["AttendanceRate"].mean(), 1))
col4.metric("Avg Study Hours", round(filtered["StudyHoursPerWeek"].mean(), 1))

st.divider()

left, right = st.columns(2)

with left:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    fig1 = px.scatter(filtered, x="AttendanceRate", y="GPA", color="PerformanceBand",
                      hover_data=["FirstName", "LastName", "University"])
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    fig2 = px.histogram(filtered, x="GPA", nbins=12)
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

bottom_left, bottom_right = st.columns(2)

with bottom_left:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    uni_avg = filtered.groupby("University")["GPA"].mean().reset_index()
    fig3 = px.bar(uni_avg, x="University", y="GPA")
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with bottom_right:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    fig4 = px.box(filtered, y="MentalWellbeingScore")
    st.plotly_chart(fig4, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

st.dataframe(filtered, use_container_width=True)

st.download_button("Download Filtered Data",
                   data=filtered.to_csv(index=False).encode("utf-8"),
                   file_name="kenyan_students_filtered.csv",
                   mime="text/csv")
