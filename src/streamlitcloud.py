import streamlit as st
import pandas as pd
from snowflake.snowpark import Session
from snowflake.connector.errors import DatabaseError

st.set_page_config(page_title="Building Heating System Dashboard", layout="wide")
st.write("Secrets keys:", list(st.secrets.keys()))
# ---------------------------
# Snowflake connection
# ---------------------------
@st.cache_resource
def create_session():
    try:
        cfg = st.secrets["snowflake"]
        print(cfg)
        return Session.builder.configs({
            "account": cfg["account"],
            "user": cfg["user"],
            "password": cfg["password"],   # still password for now
            "warehouse": cfg["warehouse"],
            "database": cfg["database"],
            "schema": cfg["schema"],
            "role": cfg["role"],
        }).create()

    except DatabaseError as e:
        st.error("❌ Snowflake connection failed.")
        st.error("Check credentials in Streamlit Secrets.")
        st.stop()   # 🔥 THIS LINE PREVENTS LOCKS


session = create_session()

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
