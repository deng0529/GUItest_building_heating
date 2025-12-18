# app.py
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Building Zone Temperature Dashboard", layout="wide")

st.title("Zone Temperature Dashboard")

st.write(
    "Upload a CSV file with columns including `zoneid`, `ext`, `target_temp`, "
    "`temp.0` and a time column (e.g. `sample_time`). The app will rename and visualize them."
)

# 1. File upload
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is None:
    st.info("Please upload a CSV file to get started.")
    st.stop()

# 2. Read data
df = pd.read_csv(uploaded_file)

# 3. Rename columns
rename_map = {
    "zoneid": "zone_id",
    "ext": "ext_temp",
    "temp.0": "real_temp",
}
df = df.rename(columns=rename_map)

# 4. Detect / set time column (change this if your column name is different)
time_column_candidates = ["sample_time", "time", "timestamp", "datetime"]
time_col = None
for c in time_column_candidates:
    if c in df.columns:
        time_col = c
        break

if time_col is None:
    st.error(
        "No time column found. Please ensure your CSV has a time column like "
        "'sample_time', 'time', 'timestamp', or 'datetime'."
    )
    st.stop()

# Ensure time column is in datetime format if possible
try:
    df[time_col] = pd.to_datetime(df[time_col])
except Exception:
    pass  # If it fails, we still use it as-is

# 5. Show full table
st.subheader("Raw Data (Renamed Columns)")
st.dataframe(df)

# 6. Sidebar controls
st.sidebar.header("Filters")

# zone_id selection
if "zone_id" not in df.columns:
    st.error("Column `zone_id` not found after renaming. Check your input file.")
    st.stop()

zone_options = sorted(df["zone_id"].dropna().unique())
selected_zone = st.sidebar.selectbox("Select zone_id", options=zone_options)

# metric selection
available_metrics = [c for c in ["ext_temp", "target_temp", "real_temp"] if c in df.columns]

if not available_metrics:
    st.error(
        "None of `ext_temp`, `target_temp`, or `real_temp` columns found after renaming. "
        "Check your input file."
    )
    st.stop()

selected_metrics = st.sidebar.multiselect(
    "Select variables to plot",
    options=available_metrics,
    default=available_metrics,
)

if not selected_metrics:
    st.warning("Please select at least one variable to plot.")
    st.stop()

# 7. Filter data by selected zone
zone_df = df[df["zone_id"] == selected_zone].sort_values(by=time_col)

st.subheader(f"Time Series for zone_id = {selected_zone}")
st.line_chart(
    zone_df.set_index(time_col)[selected_metrics],
    height=400,
)

st.caption(
    "Chart shows selected variables over time for the chosen zone_id. "
    "You can change the zone and variables from the sidebar."
)
