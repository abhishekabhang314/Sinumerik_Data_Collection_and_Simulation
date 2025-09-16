
# CNC Machine Monitoring Dashboard

This project provides an interactive web dashboard for visualizing and analyzing the operational data of a CNC machine. Built with Python using **Streamlit**, **Pandas**, and **Plotly**, it transforms raw time-series data from a CSV file into actionable insights, helping to track productivity, diagnose faults, and understand machine health.

## 🌐 Live Demo
**You can access the live, interactive dashboard here:**
[**View Live Dashboard**](https://abhishekabhang314-sinumerik-data-collection-an-dashboard-gb4bru.streamlit.app/)

---

## ✨ Features

* **Dynamic Filtering:** Filter the entire dataset by date range, time of day, machine status, and specific error codes.
* **KPI Summary:** View high-level metrics like Total Production, Average Cycle Time, and Time Utilization directly in the sidebar.
* **Interactive Time-Series Charts:** Plot multiple parameters over time to compare trends and identify anomalies.
* **Detailed Drill-Down View:** Select a specific day and time window to generate detailed trend charts for individual parameters.
* **Operational Overview:** See a breakdown of machine status (Running, Idle, Fault) and a daily summary of production vs. faults.
* **Parameter Correlation Heatmap:** Discover statistical relationships between different machine parameters (e.g., how spindle load affects temperature).

---

## 🚀 Getting Started

Follow these instructions to get the dashboard running on your local machine.

### Prerequisites

You need to have Python 3.8+ installed. First, install the required libraries using pip:

```bash
pip install streamlit pandas plotly-express
````

### File Structure

Ensure your project folder is set up correctly:

```
your_project_folder/
├── 🖥️ dashboard.py           # The Python script for your Streamlit app
└── 📄 cnc_dynamic_dummy_data.csv  # The data file
```

### Installation

1.  Clone this repository or download the files into your project folder.
2.  Open your terminal or command prompt.
3.  Navigate to the root of your project folder using the `cd` command.
4.  Run the following command to launch the dashboard:

<!-- end list -->

```bash
streamlit run dashboard.py
```

Your web browser will automatically open with the application running.

---

## 📊 Dashboard Guide

The dashboard is designed for interactive data exploration. Here’s a guide to its main components.

### Filters & Controls (Sidebar)

All controls are located in the sidebar on the left. Any changes you make here will instantly update the entire dashboard.

  * **Select Date Range:** Choose the start and end dates for your analysis.
  * **Start/End Time:** Refine the analysis to specific hours within the selected dates.
  * **Machine Status:** Filter the data to include only specific statuses (e.g., show only `Running` and `Fault` periods).
  * **Error Codes:** If you are investigating faults, you can select one or more specific error codes to isolate those events.

### Visualizations (Main Panel)

The main panel contains several interactive charts to help you understand the data.

1.  **Multi-Parameter Time Series:** The main chart where you can select multiple parameters (like temperature, load, and speed) to plot on the same timeline. Hover over the lines to see specific values.
2.  **Detailed Day/Time View:** After selecting a date and time window, this section generates individual trend charts for your chosen parameters, allowing for a closer look. Some charts include a moving average (MA) to help smooth out noise.
3.  **Operational Overview:**
      * **Machine Status Distribution:** A pie chart showing the percentage of time the machine spent in `Running`, `Idle`, and `Fault` states.
      * **Daily Production vs. Faults:** A bar chart that compares the total number of units produced each day against the number of faults that occurred.
4.  **Parameter Correlation:** A heatmap that shows the statistical relationship between different numeric parameters. A high value (close to 1.0) indicates a strong positive correlation (e.g., as power consumption goes up, temperature also goes up).
5.  **Production Trend:** A line chart showing the cumulative production count over time, with a moving average to visualize the overall production rate.

---

### 🛠️ Technologies Used

  * **Streamlit:** For building and serving the web application.
  * **Pandas:** For data loading, cleaning, and manipulation.
  * **Plotly Express:** For generating interactive, high-quality visualizations.

<!-- end list -->
