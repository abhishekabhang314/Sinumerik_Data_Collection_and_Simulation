import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="CNC Machine Monitoring Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --- 2. DATA LOADING & CACHING ---
@st.cache_data
def load_data(file_path):
    """
    Loads CNC data from a CSV file, parses dates, and sets the timestamp as the index.
    """
    try:
        df = pd.read_csv(file_path)
        df['timestamp'] = pd.to_datetime(df['Unnamed: 0'])
        df = df.set_index('timestamp')
        df = df.drop(columns=['Unnamed: 0'])
        return df
    except FileNotFoundError:
        st.error(
            f"Error: The file '{file_path}' was not found. Please ensure it's in the same directory as the script.")
        return None


# Load the data
df = load_data('cnc_dynamic_dummy_data.csv')

# --- 3. SIDEBAR FILTERS ---
st.sidebar.title("Filters & Controls")

if df is not None:
    # Date Range Filter
    min_date = df.index.min().date()
    max_date = df.index.max().date()

    # Check if min_date and max_date are the same
    if min_date == max_date:
        # If they are the same, create a default range of one day
        date_range_value = (min_date, min_date + datetime.timedelta(days=1))
    else:
        date_range_value = (min_date, max_date)

    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=date_range_value,
        min_value=min_date,
        max_value=max_date
    )

    # Ensure date_range has two elements before proceeding
    if len(date_range) != 2:
        st.sidebar.warning("Please select a valid date range.")
        st.stop()

    # Convert date_range to datetime for filtering
    start_date = datetime.datetime.combine(date_range[0], datetime.time.min)
    end_date = datetime.datetime.combine(date_range[1], datetime.time.max)

    # Machine Status Filter
    status_options = df['machine_status'].unique()
    selected_statuses = st.sidebar.multiselect(
        "Select Machine Status",
        options=status_options,
        default=status_options
    )

    # Error Code Filter
    error_options = df[df['error_code'] != 0]['error_code'].unique()
    selected_errors = st.sidebar.multiselect(
        "Filter by Error Code (if any)",
        options=error_options,
        default=[]
    )

    # Apply filters to the dataframe
    filtered_df = df[
        (df.index >= start_date) &
        (df.index <= end_date) &
        (df['machine_status'].isin(selected_statuses))
        ]

    if selected_errors:
        filtered_df = filtered_df[filtered_df['error_code'].isin(selected_errors)]

    # --- 4. MAIN DASHBOARD LAYOUT ---
    st.title(" CNC Machine Live Monitoring Dashboard")
    st.markdown("---")

    # === ROBUSTNESS CHECK: Only display the dashboard if there is data after filtering ===
    if not filtered_df.empty:
        # --- KPI Section ---
        st.header("Key Performance Indicators (KPIs)")

        # Calculate time range in minutes based on actual filtered data, not just the selector
        total_time_minutes = (filtered_df.index.max() - filtered_df.index.min()).total_seconds() / 60
        running_time_minutes = len(filtered_df[filtered_df['machine_status'] == 'Running'])
        uptime_percentage = (running_time_minutes / total_time_minutes) * 100 if total_time_minutes > 0 else 0

        total_production = filtered_df['production_count'].iloc[-1] - filtered_df['production_count'].iloc[0]
        total_faults = len(filtered_df[filtered_df['machine_status'] == 'Fault'])

        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric(label="Uptime", value=f"{uptime_percentage:.2f} %")
        kpi2.metric(label="Total Production", value=f"{total_production} units")
        kpi3.metric(label="Number of Faults", value=f"{total_faults}")

        st.markdown("---")

        # --- Time-Series Analysis Section ---
        st.header("Time-Series Analysis")

        time_series_options = [
            'Spindle_Speed_RPM', 'Feed_Rate_mm_min', 'Spindle_Temperature_C', 'Vibration_mm_s',
            'Servo_Motor_Load_pct', 'Power_Consumption_kW', 'Coolant_Flow_L_min', 'Coolant_Pressure_bar'
        ]

        selected_ts_params = st.multiselect(
            "Select parameters to plot over time:",
            options=time_series_options,
            default=['Spindle_Speed_RPM', 'Servo_Motor_Load_pct', 'Spindle_Temperature_C']
        )

        if selected_ts_params:
            fig_ts = px.line(
                filtered_df,
                y=selected_ts_params,
                title="Machine Parameters Over Time",
                labels={'value': 'Value', 'timestamp': 'Time'},
                template="plotly_dark"
            )
            fig_ts.update_layout(legend_title_text='Parameters')
            st.plotly_chart(fig_ts, use_container_width=True)
        else:
            st.warning("Please select at least one parameter to plot.")

        st.markdown("---")

        # --- Status Distribution & Daily Production Section ---
        st.header("Operational Overview")

        col1, col2 = st.columns(2)

        with col1:
            # Machine Status Distribution (Pie Chart)
            status_counts = filtered_df['machine_status'].value_counts()
            fig_pie = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Machine Status Distribution",
                template="plotly_dark",
                hole=0.3
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            # Daily Production and Faults (Bar Chart)
            daily_summary = filtered_df.resample('D').agg(
                daily_production=('production_count', lambda x: x.max() - x.min() if not x.empty else 0),
                fault_count=('machine_status', lambda x: (x == 'Fault').sum())
            ).reset_index()

            fig_bar = px.bar(
                daily_summary,
                x='timestamp',
                y=['daily_production', 'fault_count'],
                title="Daily Production vs. Faults",
                labels={'timestamp': 'Date'},
                barmode='group',
                template="plotly_dark"
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")

        # --- Raw Data View Section ---
        st.header("Filtered Data View")
        st.dataframe(filtered_df)

    else:
        # === Display this message if the dataframe is empty after filtering ===
        st.warning("No data available for the selected filters. Please adjust your selections in the sidebar.")

else:
    st.warning("Please make sure the 'cnc_dynamic_dummy_data.csv' file is present in the project folder.")