import streamlit as st
import pandas as pd
from snowflake.snowpark import Session
from snowflake.connector.errors import DatabaseError
import traceback

st.set_page_config(page_title="Building Heating System Dashboard", layout="wide")
st.error("🔥 THIS FILE IS RUNNING")
# st.stop()
st.write("Secrets keys:", list(st.secrets.keys()))
# ---------------------------
# Snowflake connection
# ---------------------------
@st.cache_resource
def create_session():
    st.write("STEP 3: entered create_session")
    return None

st.write("STEP 2: before calling create_session")

session = create_session()

st.write("STEP 4: after calling create_session")
# def create_session():
#     st.write("🔍 Loading secrets...")
#     st.write(st.secrets)  # SAFE: keys only, values hidden
#
#     cfg = st.secrets["snowflake"]
#
#     st.write("🔍 Building Snowflake config...")
#     st.write({
#         "account": cfg.get("account"),
#         "user": cfg.get("user"),
#         "warehouse": cfg.get("warehouse"),
#         "database": cfg.get("database"),
#         "schema": cfg.get("schema"),
#         "role": cfg.get("role"),
#         "has_password": "password" in cfg,
#     })
#
#     return Session.builder.configs({
#         "account": cfg["account"],
#         "user": cfg["user"],
#         "password": cfg["password"],
#         "warehouse": cfg["warehouse"],
#         "database": cfg["database"],
#         "schema": cfg["schema"],
#         "role": cfg["role"],
#     }).create()
#
# try:
#     session = create_session()
#     st.success("✅ Snowflake session created successfully")
#     st.write(session.sql("SELECT CURRENT_USER(), CURRENT_ROLE()").collect())
#
# except Exception:
#     st.error("❌ Snowflake session creation failed")
#     st.code(traceback.format_exc())
#     st.stop()
#
#
# session = create_session()

st.title("Building Heating System Dashboard")
st.caption("Real-time temperature visualization powered by Snowflake + Streamlit Cloud")


# ---------------------------
# Load data
# ---------------------------
TABLE_NAME = "BUILDING_A"   # ← change if needed

df = session.table(TABLE_NAME).to_pandas()

# ---------------------------
# Optional: remove outliers
# ---------------------------
def remove_outliers_iqr(df, column):
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    return df[(df[column] >= lower) & (df[column] <= upper)]


if st.sidebar.checkbox("Remove outliers", value=False):
    for col in ["EXT_TEMP", "TARGET_TEMP", "INDOOR_TEMP"]:
        if col in df.columns:
            df = remove_outliers_iqr(df, col)


# ---------------------------
# Sidebar filter
# ---------------------------
if "ZONEID" not in df.columns:
    st.error("Column 'ZONEID' not found in table. Please check your Snowflake table.")
    st.stop()

zone_list = sorted(df["ZONEID"].dropna().unique())
selected_zone = st.sidebar.selectbox("Select Zone ID", zone_list)

# Ensure time column is in datetime format if possible
try:
    df['SAMPLE_TIME'] = pd.to_datetime(df['SAMPLE_TIME'])
except Exception:
    pass  # If it fails, we still use it as-is

# ---------------------------
# Filter for selected zone
# ---------------------------
filtered = df[df["ZONEID"] == selected_zone].copy()


# ---------------------------
# Display table
# ---------------------------
st.subheader(f"Data for Zone {selected_zone}")
st.dataframe(filtered, use_container_width=True)

# ---------------------------
# Line chart
# ---------------------------
plot_cols = ["EXT_TEMP", "TARGET_TEMP", "INDOOR_TEMP"]
available_cols = [c for c in plot_cols if c in filtered.columns]
timestamp_col = 'SAMPLE_TIME'
if len(available_cols) > 0:
    st.subheader("Temperature Over Time")
    st.line_chart(filtered.set_index(timestamp_col)[available_cols])
else:
    st.warning("No temperature columns available to plot.")


st.success("Dashboard loaded successfully!")
