import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Student Dashboard", layout="wide")
st.title("📊 Student Performance Dashboard")

REQUIRED_COLS = [
    "FirstName","LastName","University","Campus","School","Program",
    "YearOfStudy","Gender","Age","County","AttendanceRate","StudyHoursPerWeek",
    "GPA","MentalWellbeingScore","FinancialStressScore","CreditsRegistered"
]

FILTER_COLS = [
    "University","Campus","School","Program","YearOfStudy","Gender","County"
]

NUM_COLS = [
    "Age","AttendanceRate","StudyHoursPerWeek","GPA",
    "MentalWellbeingScore","FinancialStressScore","CreditsRegistered"
]

def performance_band(gpa: float) -> str:
    if pd.isna(gpa):
        return "Unknown"
    if gpa >= 3.7:
        return "Excellent (3.7+)"
    elif gpa >= 3.0:
        return "Good (3.0–3.69)"
    elif gpa >= 2.0:
        return "Average (2.0–2.99)"
    else:
        return "At Risk (<2.0)"

@st.cache_data
def load_csv(file) -> pd.DataFrame:
    # header=0 means: first row is column names (your case)
    df = pd.read_csv(file, header=0)

    # Clean column names just in case of extra spaces
    df.columns = [c.strip() for c in df.columns]

    # Convert numeric columns safely
    for c in NUM_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    return df

uploaded = st.file_uploader("Upload your CSV", type=["csv"])
if not uploaded:
    st.info("Upload a CSV file to begin.")
    st.stop()

df = load_csv(uploaded)

# Validate columns
missing = [c for c in REQUIRED_COLS if c not in df.columns]
if missing:
    st.error("❌ One or more required columns are missing in your CSV.")
    st.write("**Missing columns:**", missing)
    st.write("**Columns detected:**", list(df.columns))
    st.stop()

# Add derived columns
df["FullName"] = df["FirstName"].astype(str).str.strip() + " " + df["LastName"].astype(str).str.strip()
df["PerformanceBand"] = df["GPA"].apply(performance_band)

# ----------------------------
# Sidebar filters (based on your headers)
# ----------------------------
st.sidebar.header("🔎 Filters")

filtered = df.copy()

# Categorical filters
for col in FILTER_COLS:
    options = sorted([x for x in filtered[col].dropna().unique().tolist()])
    selected = st.sidebar.multiselect(col, options, default=options)
    if selected:
        filtered = filtered[filtered[col].isin(selected)]

# GPA range filter
min_gpa = float(np.nanmin(df["GPA"])) if df["GPA"].notna().any() else 0.0
max_gpa = float(np.nanmax(df["GPA"])) if df["GPA"].notna().any() else 4.0
gpa_range = st.sidebar.slider("GPA Range", 0.0, 4.0, (max(0.0, min_gpa), min(4.0, max_gpa)), 0.01)
filtered = filtered[filtered["GPA"].between(gpa_range[0], gpa_range[1], inclusive="both")]

# Age range filter (optional)
if df["Age"].notna().any():
    min_age = int(np.nanmin(df["Age"]))
    max_age = int(np.nanmax(df["Age"]))
    age_range = st.sidebar.slider("Age Range", min_age, max_age, (min_age, max_age), 1)
    filtered = filtered[filtered["Age"].between(age_range[0], age_range[1], inclusive="both")]

# ----------------------------
# KPIs
# ----------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("Students", f"{len(filtered):,}")
col2.metric("Avg GPA", f"{filtered['GPA'].mean():.2f}" if filtered["GPA"].notna().any() else "N/A")
col3.metric("Avg Attendance", f"{filtered['AttendanceRate'].mean():.1f}%" if filtered["AttendanceRate"].notna().any() else "N/A")
col4.metric("Avg Study Hours", f"{filtered['StudyHoursPerWeek'].mean():.1f}" if filtered["StudyHoursPerWeek"].notna().any() else "N/A")

st.divider()

# ----------------------------
# Charts
# ----------------------------
left, right = st.columns(2)

with left:
    st.subheader("Performance Bands")
    band_counts = filtered["PerformanceBand"].value_counts().reset_index()
    band_counts.columns = ["PerformanceBand", "Count"]
    st.bar_chart(band_counts.set_index("PerformanceBand"))

with right:
    st.subheader("Average GPA by Program (Top 15)")
    gpa_by_program = (
        filtered.groupby("Program", dropna=True)["GPA"]
        .mean()
        .sort_values(ascending=False)
        .head(15)
        .reset_index()
    )
    st.bar_chart(gpa_by_program.set_index("Program"))

st.divider()

# ----------------------------
# Data table
# ----------------------------
st.subheader("Filtered Dataset")
show_cols = [
    "FullName","University","Campus","School","Program","YearOfStudy","Gender",
    "Age","County","AttendanceRate","StudyHoursPerWeek","GPA",
    "MentalWellbeingScore","FinancialStressScore","CreditsRegistered","PerformanceBand"
]
st.dataframe(filtered[show_cols], use_container_width=True)

# Download filtered data
csv_out = filtered.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download filtered CSV", data=csv_out, file_name="filtered_students.csv", mime="text/csv")
