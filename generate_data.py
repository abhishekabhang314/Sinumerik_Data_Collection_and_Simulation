import pandas as pd
import numpy as np
import datetime

# --- 1. CONFIGURATION ---
# What's new:
# - Job Profiles: Different jobs with unique parameter ranges.
# - Dynamic Behavior: Parameters are now correlated and have drifting baselines.
# - Enhanced State Logic: Simulates setup time between jobs.

# Define the simulation time frame
start_date = datetime.datetime(2025, 9, 15)  # A Monday
duration_days = 7
time_interval_minutes = 1

# Define machine operational schedule
shift_1_start, shift_1_end = 6, 14
shift_2_start, shift_2_end = 14, 22
fault_probability = 0.005
setup_time_minutes = 15

# --- Job Profiles ---
# Each job has different characteristics
JOB_PROFILES = {
    'Job_A': {  # High Speed, Low Load (e.g., Finishing Aluminum)
        'spindle_speed_rpm': [3500, 5000], 'feed_rate_mm_min': [400.0, 600.0],
        'servo_load_pct': [25.0, 45.0], 'vibration_mm_s': [0.5, 1.5],
        'base_power_kw': 8.0
    },
    'Job_B': {  # Low Speed, High Load (e.g., Roughing Steel)
        'spindle_speed_rpm': [800, 1500], 'feed_rate_mm_min': [50.0, 150.0],
        'servo_load_pct': [60.0, 90.0], 'vibration_mm_s': [1.5, 3.0],
        'base_power_kw': 12.0
    }
}
error_codes = [1001, 2034, 4500, 5012]

# --- 2. DATA GENERATION LOGIC ---

timestamps = pd.date_range(start=start_date, periods=duration_days * 24 * 60 // time_interval_minutes,
                           freq=f'{time_interval_minutes}min')
df = pd.DataFrame(index=timestamps)

# Initialize data lists and state variables
data = {key: [0.0] * len(timestamps) for key in [
    'error_code', 'cycle_time_s', 'spindle_speed_rpm', 'feed_rate_mm_min', 'axis_position_x_mm',
    'spindle_temperature_c', 'vibration_mm_s', 'servo_motor_load_pct', 'power_consumption_kw',
    'coolant_flow_l_min', 'coolant_pressure_bar', 'lubrication_level_pct', 'ambient_humidity_pct',
    'ambient_dust_ug_m3'
]}
data['machine_status'] = ['Idle'] * len(timestamps)
data['spindle_temperature_c'][0] = 25.0
data['lubrication_level_pct'][0] = 100.0

current_job = None
job_end_time = None
in_setup = False
setup_end_time = None
cycle_timer = 0
production_count = 0

# Main loop to generate data
for i, ts in enumerate(timestamps):
    if i == 0: continue

    # Copy previous state for continuity
    for key in data: data[key][i] = data[key][i - 1]

    # --- State Machine Logic ---
    is_work_hour = (
                               shift_1_start <= ts.hour < shift_1_end or shift_2_start <= ts.hour < shift_2_end) and ts.weekday() < 5

    if in_setup and ts >= setup_end_time:
        in_setup = False
        current_job = None  # Ready for next job

    status = 'Idle'
    if is_work_hour and not in_setup:
        # If no job is running, start a new one
        if current_job is None:
            current_job = np.random.choice(list(JOB_PROFILES.keys()))
            job_duration = datetime.timedelta(hours=np.random.randint(2, 5))
            job_end_time = ts + job_duration

        # If the current job is finished, start setup time
        if ts >= job_end_time:
            status = 'Idle'
            in_setup = True
            setup_end_time = ts + datetime.timedelta(minutes=setup_time_minutes)
            current_job = None
        else:
            status = 'Running'

    # Inject random faults
    if status == 'Running' and np.random.rand() < fault_probability:
        status = 'Fault'

    # Simple fault recovery logic (fault lasts 30 mins)
    if data['machine_status'][i - 1] == 'Fault' and (
            ts - timestamps[data['machine_status'].index('Fault', i - 30, i)]).total_seconds() < 1800:
        status = 'Fault'
        current_job = None  # A fault stops the job

    data['machine_status'][i] = status

    # --- Parameter Generation based on State and Job ---
    if status == 'Running' and current_job:
        profile = JOB_PROFILES[current_job]

        data['error_code'][i] = 0
        data['spindle_speed_rpm'][i] = np.random.randint(*profile['spindle_speed_rpm'])
        data['feed_rate_mm_min'][i] = np.random.uniform(*profile['feed_rate_mm_min'])
        data['servo_motor_load_pct'][i] = np.random.uniform(*profile['servo_load_pct']) + np.random.normal(0, 2)
        data['vibration_mm_s'][i] = np.random.uniform(*profile['vibration_mm_s']) + np.random.normal(0, 0.1)
        # Correlated power consumption
        data['power_consumption_kw'][i] = profile['base_power_kw'] + (data['servo_motor_load_pct'][i] / 50.0) + (
                    data['spindle_speed_rpm'][i] / 1000.0) + np.random.normal(0, 0.5)
        # Correlated temperature increase
        temp_increase = 0.1 + (data['servo_motor_load_pct'][i] / 100.0) * 0.5
        data['spindle_temperature_c'][i] = min(85.0, data['spindle_temperature_c'][i - 1] + temp_increase)
        # Other systems on
        data['coolant_flow_l_min'][i] = np.random.uniform(10.0, 20.0)
        data['coolant_pressure_bar'][i] = np.random.uniform(2.0, 4.0)
        # Simulate movement
        data['axis_position_x_mm'][i] = (data['axis_position_x_mm'][i - 1] + data['feed_rate_mm_min'][i] / 60.0) % 500

        # Cycle time and production count (every 10 mins)
        cycle_timer += time_interval_minutes
        if cycle_timer >= 10:
            data['cycle_time_s'][i] = 600.0 + np.random.normal(0, 15)
            production_count += 1
            cycle_timer = 0
        else:
            data['cycle_time_s'][i] = 0.0

    else:  # Idle, Setup, or Fault
        data['error_code'][i] = np.random.choice(error_codes) if status == 'Fault' else 0
        data['spindle_speed_rpm'][i] = 0
        data['feed_rate_mm_min'][i] = 0.0
        data['servo_motor_load_pct'][i] = np.random.uniform(0, 2)
        data['vibration_mm_s'][i] = np.random.uniform(0.1, 0.5)
        data['power_consumption_kw'][i] = np.random.uniform(1.0, 2.0)
        data['coolant_flow_l_min'][i] = 0.0
        data['coolant_pressure_bar'][i] = 0.0
        data['spindle_temperature_c'][i] = max(25.0, data['spindle_temperature_c'][i - 1] - 0.2)
        data['cycle_time_s'][i] = 0.0
        if status == 'Fault': data['vibration_mm_s'][i] = np.random.uniform(3.0, 6.0)  # Vibration spike

    # Slowly changing parameters
    data['lubrication_level_pct'][i] = max(0, data['lubrication_level_pct'][i - 1] - 0.002)
    data['ambient_humidity_pct'][i] = 60 + 15 * np.sin(2 * np.pi * ts.hour / 24) + np.random.normal(0, 2)
    data['ambient_dust_ug_m3'][i] = 20 + 5 * np.sin(2 * np.pi * ts.dayofyear / 365) + np.random.normal(0, 1)

# --- 3. CREATE AND SAVE DATAFRAME ---
final_df = pd.DataFrame(data, index=timestamps)

# Ensure correct data types and formatting
final_df['production_count'] = np.cumsum([1 if t > 0 else 0 for t in final_df['cycle_time_s']]).astype(int)
final_df['error_code'] = final_df['error_code'].astype(int)
final_df['spindle_speed_rpm'] = final_df['spindle_speed_rpm'].astype(int)

# Round floats for realism
float_cols = [
    'cycle_time_s', 'feed_rate_mm_min', 'axis_position_x_mm', 'spindle_temperature_c', 'vibration_mm_s',
    'servo_motor_load_pct', 'power_consumption_kw', 'coolant_flow_l_min', 'coolant_pressure_bar',
    'lubrication_level_pct', 'ambient_humidity_pct', 'ambient_dust_ug_m3'
]
final_df[float_cols] = final_df[float_cols].round(3)

# Save the dataframe to a CSV file
final_df.to_csv('cnc_dynamic_dummy_data.csv')

print("✅ Successfully generated dynamic CNC dummy data in 'cnc_dynamic_dummy_data.csv'")