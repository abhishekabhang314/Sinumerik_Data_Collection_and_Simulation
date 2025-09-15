import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import numpy as np

st.set_page_config(page_title="CNC Machine Monitoring Dashboard", page_icon="✨", layout="wide")

# Define the expected parameter list (exact names provided by user)
PARAMETERS = [
    "error_code", "cycle_time_s", "spindle_speed_rpm", "feed_rate_mm_min", "axis_position_x_mm",
    "spindle_temperature_c", "vibration_mm_s", "servo_motor_load_pct", "power_consumption_kw",
    "coolant_flow_l_min", "coolant_pressure_bar", "lubrication_level_pct", "ambient_humidity_pct",
    "ambient_dust_ug_m3", "machine_status", "production_count"
]

# Choose a professional color palette for categorical charts
COLOR_SEQ = [
    "#A8D5BA", "#F7C6C7", "#FFD8A9", "#C6D8FF", "#E3C9FF", "#FFEFAF",
    "#B8E6E6", "#F6D6E0", "#D9EAD3", "#F3E6CB", "#CFCFEA", "#F2D6C9"
]

# Pastel continuous scale for heatmaps / continuous charts
PASTEL_SCALE = ["#FFF5E6", "#FFE6CC", "#FFD9B3", "#FFC299", "#FFB380", "#FF9F80", "#FF8C66"]

# Unified layout settings applied to every figure to avoid white flash
DARK_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="#0b1020",
    plot_bgcolor="#0b1020",
    font=dict(color="#FFFFFF"),
    margin=dict(l=40, r=20, t=60, b=40),
    title_x=0.02
)

# --- DATA LOADING & CACHING ---
@st.cache_data
def load_data(file_path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(file_path)
        if 'Unnamed: 0' in df.columns:
            df['timestamp'] = pd.to_datetime(df['Unnamed: 0'])
            df = df.set_index('timestamp')
            df = df.drop(columns=['Unnamed: 0'])
        elif 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
        else:
            raise ValueError("CSV must contain a timestamp column named 'Unnamed: 0' or 'timestamp'.")

        # Ensure numeric columns are numeric when possible
        for c in df.columns:
            if c in PARAMETERS and c not in ['machine_status']:
                df[c] = pd.to_numeric(df[c], errors='coerce')

        return df
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        return None
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Load data
DATA_PATH = 'cnc_dynamic_dummy_data.csv'
df = load_data(DATA_PATH)

# Sidebar controls
st.sidebar.title("Filters & Controls")

if df is not None:
    # Date & time selection
    min_dt = df.index.min()
    max_dt = df.index.max()

    date_range = st.sidebar.date_input("Select Date Range", value=(min_dt.date(), min_dt.date()), min_value=min_dt.date(), max_value=max_dt.date())
    if len(date_range) != 2:
        st.sidebar.warning("Please select a valid date range")
        st.stop()

    # specific times
    start_time = st.sidebar.time_input("Start time", value=datetime.time(0, 0))
    end_time = st.sidebar.time_input("End time", value=datetime.time(23, 59))

    start_dt = pd.to_datetime(datetime.datetime.combine(date_range[0], start_time))
    end_dt = pd.to_datetime(datetime.datetime.combine(date_range[1], end_time))

    # machine_status filter (if present)
    status_options = df['machine_status'].unique().tolist() if 'machine_status' in df.columns else []
    selected_statuses = st.sidebar.multiselect("Machine status", options=status_options, default=status_options)

    # error code
    error_options = df[df['error_code'] != 0]['error_code'].unique().tolist() if 'error_code' in df.columns else []
    selected_errors = st.sidebar.multiselect("Error codes", options=error_options, default=[])

    # filter application
    filtered = df[(df.index >= start_dt) & (df.index <= end_dt)].copy()
    if selected_statuses:
        filtered = filtered[filtered['machine_status'].isin(selected_statuses)]
    if selected_errors:
        filtered = filtered[filtered['error_code'].isin(selected_errors)]

    if filtered.empty:
        st.warning("No data for the selected filters.")
        st.stop()

    # compute durations between rows and _duration column
    times = filtered.index.to_series()
    durations = (times.shift(-1) - times).fillna(pd.Timedelta(seconds=0))
    filtered['_duration'] = durations

    # SUMMARY METRICS shown in left sidebar
    total_production = 0
    if 'production_count' in filtered.columns and len(filtered['production_count'].dropna()) >= 2:
        total_production = int(filtered['production_count'].iloc[-1] - filtered['production_count'].iloc[0])

    running_duration = filtered.loc[filtered['machine_status'] == 'Running', '_duration'].sum() if 'machine_status' in filtered.columns else pd.Timedelta(0)
    total_duration = filtered['_duration'].sum()
    down_duration = total_duration - running_duration

    # average cycle time calculation (time between production increments)
    avg_cycle_s = None
    if 'production_count' in filtered.columns:
        prod_events = filtered[filtered['production_count'].diff() > 0]
        if len(prod_events) >= 2:
            diffs = prod_events.index.to_series().diff().dropna()
            avg_cycle_s = diffs.mean().total_seconds()

    time_util_pct = (running_duration.total_seconds() / total_duration.total_seconds() * 100) if total_duration.total_seconds() > 0 else 0

    # Sidebar metrics (nicely formatted)
    st.sidebar.header("Summary Metrics")
    st.sidebar.metric("Total production", f"{total_production} units")
    st.sidebar.metric("Avg cycle time", f"{avg_cycle_s:.1f} s" if avg_cycle_s is not None else "N/A")
    st.sidebar.metric("Total down time", str(down_duration))
    st.sidebar.metric("Time utilization", f"{time_util_pct:.2f} %")
    st.sidebar.markdown("---")

    # ---- MAIN LAYOUT ----
    st.title("CNC Machine Monitoring Dashboard")

    # 1) Multi-parameter time series (keep as-is)
    st.header("Time-series: Multiple Parameters")

    time_series_options = [p for p in PARAMETERS if p not in ['error_code', 'machine_status', 'production_count']]
    default_selection = ['servo_motor_load_pct', 'spindle_temperature_c']
    selected_ts = st.multiselect("Select parameters to plot over time:", options=time_series_options, default=[d for d in default_selection if d in time_series_options])

    if selected_ts:
        ts_long = filtered[selected_ts].reset_index().melt(id_vars='timestamp', value_vars=selected_ts, var_name='parameter', value_name='value')
        fig_ts = px.line(ts_long, x='timestamp', y='value', color='parameter', title='Machine Parameters Over Time', color_discrete_sequence=COLOR_SEQ)
        fig_ts.update_layout(**DARK_LAYOUT)
        fig_ts.update_traces(mode='lines', line=dict(width=2))
        st.plotly_chart(fig_ts, use_container_width=True, config={'displayModeBar': True})
    else:
        st.info("Select at least one parameter to view the time-series chart")

    st.markdown("---")

    # 2) Detailed per-parameter charts for a selected date/time window
    st.header("Detailed Day/Time View (per-parameter)")
    available_dates = pd.Series(filtered.index.date).unique().tolist()
    selected_date = st.selectbox("Select date for deep-dive:", options=available_dates, index=0)

    d_start = st.time_input("Detail start time", value=datetime.time(0, 0), key='dstart')
    d_end = st.time_input("Detail end time", value=datetime.time(23, 59), key='dend')

    dstart_dt = pd.to_datetime(datetime.datetime.combine(selected_date, d_start))
    dend_dt = pd.to_datetime(datetime.datetime.combine(selected_date, d_end))

    df_day = filtered[(filtered.index >= dstart_dt) & (filtered.index <= dend_dt)]

    if df_day.empty:
        st.warning("No data in the chosen detail window.")
    else:
        # show selected parameter list to choose which to display
        detail_params = st.multiselect("Choose parameters for detailed charts:", options=time_series_options, default=time_series_options[:6])
        cols = st.columns(2)
        for i, param in enumerate(detail_params):
            col = cols[i % 2]
            with col:
                if param not in df_day.columns:
                    st.info(f"{param} not present in data")
                    continue

                # Choose chart type heuristically
                if param in ['spindle_speed_rpm', 'feed_rate_mm_min', 'spindle_temperature_c', 'vibration_mm_s', 'power_consumption_kw']:
                    fig = px.line(df_day.reset_index(), x='timestamp', y=param, title=f"{param} (trend)", color_discrete_sequence=COLOR_SEQ)
                else:
                    # line with moving average overlay
                    temp = df_day[[param]].reset_index()
                    temp[f'{param}_ma'] = temp[param].rolling(window=max(3, int(len(temp)/20)), min_periods=1).mean()
                    fig = px.line(temp, x='timestamp', y=[param, f'{param}_ma'], title=f"{param} (value & MA)", color_discrete_sequence=COLOR_SEQ)

                fig.update_layout(**DARK_LAYOUT)
                fig.update_traces(line=dict(width=2))
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    st.markdown("---")

    # 3) Operational overview (pie + daily bar)
    st.header("Operational Overview")
    c1, c2 = st.columns(2)

    with c1:
        if 'machine_status' in filtered.columns:
            status_counts = filtered['machine_status'].value_counts()
            fig_pie = px.pie(values=status_counts.values, names=status_counts.index, title='Machine Status Distribution', hole=0.35, color_discrete_sequence=COLOR_SEQ)
            fig_pie.update_layout(**DARK_LAYOUT)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info('machine_status not in data')

    with c2:
        if 'production_count' in filtered.columns:
            daily = filtered.resample('D').agg(daily_production=('production_count', lambda x: x.max() - x.min() if not x.empty else 0), faults=('machine_status', lambda x: (x == 'Fault').sum() if 'machine_status' in filtered.columns else 0)).reset_index()
            if not daily.empty:
                daily_long = daily.melt(id_vars='timestamp', value_vars=['daily_production', 'faults'], var_name='metric', value_name='count')
                fig_bar = px.bar(daily_long, x='timestamp', y='count', color='metric', barmode='group', title='Daily production vs faults', color_discrete_sequence=COLOR_SEQ)
                fig_bar.update_layout(**DARK_LAYOUT)
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info('Not enough data for daily summary')
        else:
            st.info('production_count not in data')

    st.markdown("---")

    # 4) Correlation heatmap (colorful, annotated)
    st.header("Parameter Correlation")
    numeric_cols = [c for c in time_series_options if c in filtered.columns]
    if len(numeric_cols) >= 2:
        corr = filtered[numeric_cols].corr()
        fig_corr = px.imshow(corr, text_auto=True, aspect='auto', color_continuous_scale=PASTEL_SCALE, title='Correlation matrix')
        fig_corr.update_layout(**DARK_LAYOUT)
        st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.info('Not enough numeric columns for correlation')

    st.markdown("---")

    # 5) Production trend + moving average
    st.header("Production Trend & Moving Average")
    if 'production_count' in filtered.columns:
        tmp = filtered[['production_count']].reset_index()
        tmp['production_ma'] = tmp['production_count'].rolling(window=20, min_periods=1).mean()
        fig_prod = px.line(tmp, x='timestamp', y=['production_count', 'production_ma'], labels={'value': 'production_count'}, title='Production count with MA', color_discrete_sequence=COLOR_SEQ)
        fig_prod.update_layout(**DARK_LAYOUT)
        st.plotly_chart(fig_prod, use_container_width=True)

    st.markdown("---")

    # Filtered data view
    st.header('Filtered Data (preview)')
    st.dataframe(filtered.head(500))

else:
    st.warning(f"Make sure '{DATA_PATH}' exists and contains a timestamp column named 'Unnamed: 0' or 'timestamp'.")
