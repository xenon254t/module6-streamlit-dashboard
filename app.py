import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import re

st.set_page_config(page_title="Kenyan University Student Performance", layout="wide")

st.markdown("""
<style>
.block-container{padding-top:1rem;}
.hero{border-radius:20px;padding:20px;background:linear-gradient(135deg,#6366f1,#10b981);color:#fff;}
.hero h1{margin:0;font-size:1.6rem;}
.hero p{margin:6px 0 0;opacity:.9;}
div[data-testid="stMetric"]{background:rgba(255,255,255,.05);padding:12px;border-radius:15px;border:1px solid rgba(255,255,255,.1);}
.panel{border-radius:18px;padding:15px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
<h1>🇰🇪 Kenyan Universities Student Performance Dashboard</h1>
<p>Modern analytics dashboard for academic performance and wellbeing insights</p>
</div>
""", unsafe_allow_html=True)

EXPECTED_NOHEADER_COLS = [
    "FirstName",
    "LastName",
    "University",
    "Campus",
    "School",
    "Program",
    "YearOfStudy",
    "Gender",
    "Age",
    "County",
    "AttendanceRate",
    "StudyHoursPerWeek",
    "GPA",
    "StressLevel",
    "SleepHours",
    "ExerciseHours"
]

def looks_like_header(cols):
    joined = " ".join([str(c) for c in cols]).lower()
    header_signals = ["gpa", "attendance", "university", "gender", "year"]
    return any(s in joined for s in header_signals)

@st.cache_data
def load_data():
    path = "student_performance_kenya.csv"
    df_try = pd.read_csv(path)

    df_try.columns = df_try.columns.astype(str).str.strip()

    if looks_like_header(df_try.columns):
        return df_try

    df = pd.read_csv(path, header=None)

    if df.shape[1] == len(EXPECTED_NOHEADER_COLS):
        df.columns = EXPECTED_NOHEADER_COLS
        return df

    if df.shape[1] > len(EXPECTED_NOHEADER_COLS):
        cols = EXPECTED_NOHEADER_COLS + [f"Extra_{i}" for i in range(df.shape[1] - len(EXPECTED_NOHEADER_COLS))]
        df.columns = cols
        return df

    df.columns = [f"Col_{i}" for i in range(df.shape[1])]
    return df

df = load_data()
df.columns = df.columns.astype(str).str.strip()

def normalize(col):
    return re.sub(r'[^a-z0-9]', '', str(col).lower())

col_lookup = {normalize(c): c for c in df.columns}

def get_column(possible_names):
    for name in possible_names:
        key = normalize(name)
        if key in col_lookup:
            return col_lookup[key]
    return None

gpa_col = get_column(["GPA", "gpa", "GradePointAverage", "CGPA"])
att_col = get_column(["AttendanceRate", "attendance", "Attendance"])
hrs_col = get_column(["StudyHoursPerWeek", "StudyHours", "StudyHoursWeekly"])
uni_col = get_column(["University", "Uni"])
yr_col  = get_column(["YearOfStudy", "Year", "YearLevel"])
gen_col = get_column(["Gender", "Sex"])
wb_col  = get_column(["MentalWellbeingScore", "Wellbeing", "WellBeingScore"])

fn_col = get_column(["FirstName", "First Name"])
ln_col = get_column(["LastName", "Last Name"])

required = [gpa_col, att_col, hrs_col, uni_col, yr_col, gen_col]

if any(col is None for col in required):
    st.error("One or more required columns are missing in your CSV.")
    st.write("Columns detected:", df.columns.tolist())
    st.write("Tip: Your CSV likely has a different column order/count than expected.")
    st.stop()

for c in [gpa_col, att_col, hrs_col]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

def performance_band(gpa):
    if pd.isna(gpa):
        return "Unknown"
    if gpa >= 3.6:
        return "Excellent"
    if gpa >= 3.2:
        return "Good"
    if gpa >= 2.7:
        return "Fair"
    return "At Risk"

df["PerformanceBand"] = df[gpa_col].apply(performance_band)

st.sidebar.header("Filters")

universities = st.sidebar.multiselect(
    "University",
    sorted(df[uni_col].dropna().unique()),
    default=sorted(df[uni_col].dropna().unique())
)

years = st.sidebar.multiselect(
    "Year Of Study",
    sorted(df[yr_col].dropna().unique()),
    default=sorted(df[yr_col].dropna().unique())
)

genders = st.sidebar.multiselect(
    "Gender",
    sorted(df[gen_col].dropna().unique()),
    default=sorted(df[gen_col].dropna().unique())
)

gpa_min, gpa_max = float(np.nanmin(df[gpa_col].values)), float(np.nanmax(df[gpa_col].values))
att_min, att_max = float(np.nanmin(df[att_col].values)), float(np.nanmax(df[att_col].values))
hrs_min, hrs_max = float(np.nanmin(df[hrs_col].values)), float(np.nanmax(df[hrs_col].values))

gpa_range = st.sidebar.slider("GPA Range", gpa_min, gpa_max, (gpa_min, gpa_max))
att_range = st.sidebar.slider("Attendance Range", att_min, att_max, (att_min, att_max))
hrs_range = st.sidebar.slider("Study Hours Per Week", hrs_min, hrs_max, (hrs_min, hrs_max))

bands = st.sidebar.multiselect(
    "Performance Band",
    sorted(df["PerformanceBand"].dropna().unique()),
    default=sorted(df["PerformanceBand"].dropna().unique())
)

filtered = df[
    df[uni_col].isin(universities) &
    df[yr_col].isin(years) &
    df[gen_col].isin(genders) &
    df["PerformanceBand"].isin(bands)
].copy()

filtered = filtered[
    (filtered[gpa_col] >= gpa_range[0]) & (filtered[gpa_col] <= gpa_range[1]) &
    (filtered[att_col] >= att_range[0]) & (filtered[att_col] <= att_range[1]) &
    (filtered[hrs_col] >= hrs_range[0]) & (filtered[hrs_col] <= hrs_range[1])
]

st.write("")
c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Students", len(filtered))
c2.metric("Average GPA", round(float(filtered[gpa_col].mean()), 2) if len(filtered) else 0)
c3.metric("Average Attendance", round(float(filtered[att_col].mean()), 1) if len(filtered) else 0)
c4.metric("Average Study Hours", round(float(filtered[hrs_col].mean()), 1) if len(filtered) else 0)
c5.metric("At Risk", int((filtered["PerformanceBand"] == "At Risk").sum()) if len(filtered) else 0)

st.divider()

left, right = st.columns(2)

with left:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    hover_cols = [c for c in [fn_col, ln_col, uni_col] if c is not None]
    fig1 = px.scatter(filtered, x=att_col, y=gpa_col, color="PerformanceBand", hover_data=hover_cols)
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    fig2 = px.histogram(filtered, x=gpa_col, nbins=12)
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

bl, br = st.columns(2)

with bl:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    uni_avg = filtered.groupby(uni_col, dropna=False)[gpa_col].mean().reset_index()
    fig3 = px.bar(uni_avg, x=uni_col, y=gpa_col)
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with br:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    if wb_col and wb_col in filtered.columns:
        fig4 = px.box(filtered, y=wb_col)
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.write("Wellbeing column not found in this dataset (optional).")
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

st.subheader("Filtered Student Records")
st.dataframe(filtered, use_container_width=True, height=420)

st.download_button(
    "Download Filtered Data",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="kenyan_students_filtered.csv",
    mime="text/csv"
)
