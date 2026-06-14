import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import time
import json
import random
from datetime import datetime

# Page configuration for enterprise layout
st.set_page_config(page_title="Enterprise Energy Analytics", layout="wide", page_icon="⚡")

# Resolve paths dynamically
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(script_dir, ".."))
data_dir = os.path.join(root_dir, "data")
DATA_LOG_CSV = os.path.join(data_dir, "historical_energy_log.csv")

# Custom CSS for dark professional styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: bold; color: #00f2fe; }
    div[data-testid="stMetricLabel"] { font-size: 14px; color: #a3b8cc; }
    .status-normal { padding: 10px; background-color: #1e4620; color: #4af2a1; border-radius: 5px; font-weight: bold; text-align: center; }
    .status-critical { padding: 10px; background-color: #611c1c; color: #ff6b6b; border-radius: 5px; font-weight: bold; text-align: center; animation: blinker 1s linear infinite; }
    @keyframes blinker { 50% { opacity: 0.5; } }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Enterprise Smart Home Energy Monitoring Dashboard")
st.markdown("Real-time localized edge grid computation and power quality anomaly detection pipeline.")
st.write("---")

# Simulation logic encapsulated inside the UI for seamless demonstration
class LiveAppliance:
    def __init__(self, name, watts):
        self.name = name; self.watts = watts; self.active = False
    def read(self):
        return self.watts * (1.0 + random.uniform(-0.05, 0.05)) if self.active else 0.0

if 'appliances' not in st.session_state:
    st.session_state.appliances = [
        LiveAppliance("HVAC Core System", 2200.0),
        LiveAppliance("Smart Refrigerator", 280.0),
        LiveAppliance("Industrial Water Boiler", 3000.0),
        LiveAppliance("Enterprise IT Stack", 150.0)
    ]
    st.session_state.appliances[1].active = True
    st.session_state.appliances[3].active = True
    st.session_state.wh = 0.0
    st.session_state.ticks = 0
    # Clean init file
    os.makedirs(data_dir, exist_ok=True)
    pd.DataFrame(columns=["timestamp","Voltage","Current","Power","Cumulative_kWh","Status"]).to_csv(DATA_LOG_CSV, index=False)

# Layout Columns for Controls and System Status
col_ctrl, col_status = st.columns([2, 1])

with col_ctrl:
    st.subheader("⚙️ Localized Load Control Center")
    c1, c2, c3, c4 = st.columns(4)
    st.session_state.appliances[0].active = c1.checkbox("HVAC System", value=st.session_state.appliances[0].active)
    st.session_state.appliances[1].active = c2.checkbox("Refrigerator", value=st.session_state.appliances[1].active)
    st.session_state.appliances[2].active = c3.checkbox("Water Boiler", value=st.session_state.appliances[2].active)
    st.session_state.appliances[3].active = c4.checkbox("IT Infrastructure", value=st.session_state.appliances[3].active)

# System computation loop handler
if st.button("🔄 Compute Next Telemetry Window", type="primary"):
    st.session_state.ticks += 1
    w = sum(app.read() for app in st.session_state.appliances)
    v = random.uniform(229.0, 231.8)
    i = w / v
    st.session_state.wh += (w * (1.0 / 3600.0))
    kwh = st.session_state.wh / 1000.0
    cost = kwh * 7.50
    status = "NORMAL" if i <= 22.0 else "CRITICAL_OVERLOAD_TRIP"
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Append to logs safely
    new_row = pd.DataFrame([[ts, round(v,2), round(i,3), round(w,2), round(kwh,5), status]], 
                           columns=["timestamp","Voltage","Current","Power","Cumulative_kWh","Status"])
    new_row.to_csv(DATA_LOG_CSV, mode='a', header=False, index=False)

# Load layout data
try:
    df = pd.read_csv(DATA_LOG_CSV)
except:
    df = pd.DataFrame(columns=["timestamp","Voltage","Current","Power","Cumulative_kWh","Status"])

# UI Render Logic Block
if not df.empty:
    latest = df.iloc[-1]
    
    with col_status:
        st.subheader("🚨 Circuit Breaker Vector")
        if latest["Status"] == "NORMAL":
            st.markdown('<div class="status-normal">⚡ GRID STATUS: OPERATIONAL (SAFE)</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-critical">⚠️ CRITICAL OVERLOAD: RELAY TRIPPED</div>', unsafe_allow_html=True)

    # Metric Dashboard Layout Grid
    st.write("### 📊 Live Grid Infrastructure Performance Matrix")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Line Voltage", f"{latest['Voltage']} V", delta=f"{round(latest['Voltage']-230, 2)}V Base")
    m2.metric("Total Load Current", f"{latest['Current']} A", delta="Overload > 22A", delta_color="inverse")
    m3.metric("Active Power", f"{latest['Power']} W")
    m4.metric("Accumulated Energy", f"{latest['Cumulative_kWh']} kWh")
    m5.metric("Projected Cost Impact", f"Rs. {round(latest['Cumulative_kWh']*7.50, 2)}")

    # Interactive Real-time Analytical Plots
    st.write("### 📈 Time-Series Analytics Framework")
    g1, g2 = st.columns(2)
    
    with g1:
        fig_p = px.line(df, x="timestamp", y="Power", title="Active Real-time Power Consumed Vector (Watts)", markers=True)
        fig_p.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_p, use_container_width=True)
        
    with g2:
        fig_i = px.line(df, x="timestamp", y="Current", title="Dynamic Current Waveform Analytics (Amperes)", markers=True)
        fig_i.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_i, use_container_width=True)

    # Raw Structured Data Inspector Log
    st.write("### 🗄️ Historical Industrial Data Log Analytics")
    st.dataframe(df.sort_values(by="timestamp", ascending=False), use_container_width=True)
else:
    st.info("💡 Click on 'Compute Next Telemetry Window' button above to populate the interactive enterprise dashboard nodes.")