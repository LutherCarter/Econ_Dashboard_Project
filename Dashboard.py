import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# --- Configuration & Setup ---
st.set_page_config(page_title="Macroeconomic & Volatility Dashboard", layout="wide")

# Dictionary of available FRED series
FRED_SERIES = {
    "Interest Rates": {
        "FEDFUNDS": "Federal Funds Effective Rate",
        "GS10": "10-Year Treasury Constant Maturity Rate",
        "MORTGAGE30US": "30-Year Fixed Rate Mortgage Average"
    },
    "Industrial/Economic Metrics": {
        "INDPRO": "Industrial Production: Total Index",
        "PAYEMS": "All Employees, Total Nonfarm",
        "CPIAUCSL": "Consumer Price Index (CPI)"
    },
    "Volatility Markers": {
        "VIXCLS": "CBOE Volatility Index (VIX)",
        "BAMLH0A0HYM2": "ICE BofA US High Yield Index Option-Adjusted Spread"
    }
}

# --- ETL Pipeline Functions ---

@st.cache_data(ttl=3600) # Cache data for 1 hour to simulate automated periodic ETL updates
def fetch_fred_data(series_id, api_key, start_date, end_date):
    """Fetches time-series data from the FRED API."""
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start_date.strftime("%Y-%m-%d"),
        "observation_end": end_date.strftime("%Y-%m-%d"),
        "frequency": "m", # Monthly frequency for consistent merging
        "aggregation_method": "avg"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'observations' not in data:
            return pd.DataFrame()
            
        df = pd.DataFrame(data['observations'])
        df['date'] = pd.to_datetime(df['date'])
        # Handle '.' which FRED uses for missing values
        df['value'] = pd.to_numeric(df['value'].replace('.', np.nan), errors='coerce')
        return df[['date', 'value']].rename(columns={'value': series_id})
    except Exception as e:
        st.error(f"Error fetching {series_id}: {e}")
        return pd.DataFrame()

def generate_mock_data(start_date, end_date):
    """Generates realistic mock data if no API key is provided."""
    dates = pd.date_range(start=start_date, end=end_date, freq='M')
    np.random.seed(42)
    df = pd.DataFrame({'date': dates})
    
    # Simulate Rates
    df['FEDFUNDS'] = np.cumsum(np.random.normal(0.05, 0.2, len(dates))) + 1.5
    df['FEDFUNDS'] = df['FEDFUNDS'].clip(lower=0)
    df['GS10'] = df['FEDFUNDS'] + np.random.normal(1.5, 0.5, len(dates))
    
    # Simulate Industrial Metrics (Inversely correlated to rapid rate hikes)
    df['INDPRO'] = 100 + np.cumsum(np.random.normal(0.2, 0.8, len(dates))) - (df['FEDFUNDS'] * 0.5)
    
    # Simulate Volatility (Spikes when rates jump or industrial drops)
    rate_diff = df['FEDFUNDS'].diff().fillna(0)
    df['VIXCLS'] = 15 + np.random.normal(0, 3, len(dates)) + (rate_diff * 10).clip(lower=0)
    
    return df

# --- UI & Sidebar ---

st.title("📊 Real-Time Macroeconomic & Volatility Dashboard")
st.markdown("""
This dashboard correlates Federal Reserve interest rate policies with industrial production metrics and market volatility. 
*Configure the ETL pipeline settings in the sidebar.*
""")

# Attempt to load the API key securely from a separate secrets module
try:
    secure_api_key = st.secrets["FRED_API_KEY"]
except (KeyError, FileNotFoundError):
    secure_api_key = ""

with st.sidebar:
    st.header("ETL Settings & API")
    api_key = st.text_input("FRED API Key", value=secure_api_key, type="password", 
                            help="Automatically loaded from secrets if configured. Otherwise, enter your key.")
    
    st.subheader("Date Range")
    end_date = datetime.today()
    start_date = st.date_input("Start Date", end_date - timedelta(days=5*365))
    end_date = st.date_input("End Date", end_date)
    
    st.markdown("---")
    st.subheader("Select Metrics")
    selected_rate = st.selectbox("Interest Rate Metric", list(FRED_SERIES["Interest Rates"].keys()), 
                                 format_func=lambda x: FRED_SERIES["Interest Rates"][x])
    selected_ind = st.selectbox("Industrial Metric", list(FRED_SERIES["Industrial/Economic Metrics"].keys()), 
                                format_func=lambda x: FRED_SERIES["Industrial/Economic Metrics"][x])
    selected_vol = st.selectbox("Volatility Marker", list(FRED_SERIES["Volatility Markers"].keys()), 
                                format_func=lambda x: FRED_SERIES["Volatility Markers"][x])

# --- Data Execution (ETL) ---
with st.spinner('Running ETL Pipeline & Aggregating Data...'):
    if api_key:
        # Fetch actual data
        df_rate = fetch_fred_data(selected_rate, api_key, start_date, end_date)
        df_ind = fetch_fred_data(selected_ind, api_key, start_date, end_date)
        df_vol = fetch_fred_data(selected_vol, api_key, start_date, end_date)
        
        # Merge dataframes
        if not df_rate.empty and not df_ind.empty and not df_vol.empty:
            df_merged = pd.merge(df_rate, df_ind, on='date', how='outer')
            df_merged = pd.merge(df_merged, df_vol, on='date', how='outer')
            df_merged = df_merged.sort_values('date').ffill().dropna()
        else:
            df_merged = pd.DataFrame()
            st.warning("Could not merge data. Check API key and series availability.")
    else:
        # Use mock data
        st.info("No API Key provided. Utilizing simulated macroeconomic data for demonstration.")
        df_merged = generate_mock_data(start_date, end_date)
        # Map mock data to selected variables to prevent errors
        df_merged = df_merged.rename(columns={
            'FEDFUNDS': selected_rate,
            'INDPRO': selected_ind,
            'VIXCLS': selected_vol
        })

if not df_merged.empty:
    
    # --- KPIs ---
    st.markdown("### Current Economic Snapshot")
    kpi_cols = st.columns(3)
    
    latest_data = df_merged.iloc[-1]
    prev_data = df_merged.iloc[-2] if len(df_merged) > 1 else latest_data
    
    def render_kpi(col, title, current, previous, is_rate=False):
        delta = current - previous
        delta_str = f"{delta:.2f}" + (" bps" if is_rate else "")
        col.metric(label=title, value=f"{current:.2f}", delta=delta_str, 
                   delta_color="inverse" if is_rate or "Volatility" in title else "normal")

    render_kpi(kpi_cols[0], FRED_SERIES["Interest Rates"].get(selected_rate, selected_rate), 
               latest_data[selected_rate], prev_data[selected_rate], is_rate=True)
    render_kpi(kpi_cols[1], FRED_SERIES["Industrial/Economic Metrics"].get(selected_ind, selected_ind), 
               latest_data[selected_ind], prev_data[selected_ind])
    render_kpi(kpi_cols[2], FRED_SERIES["Volatility Markers"].get(selected_vol, selected_vol), 
               latest_data[selected_vol], prev_data[selected_vol], is_rate=True)
    
    st.markdown("---")

    # --- Layout: Charts ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Interest Rates vs. Industrial Metrics")
        # Dual axis plot using Plotly Graph Objects
        fig1 = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig1.add_trace(
            go.Scatter(x=df_merged['date'], y=df_merged[selected_ind], name=selected_ind, 
                       line=dict(color='#1f77b4', width=2), fill='tozeroy', fillcolor='rgba(31, 119, 180, 0.1)'),
            secondary_y=False,
        )
        
        fig1.add_trace(
            go.Scatter(x=df_merged['date'], y=df_merged[selected_rate], name=selected_rate, 
                       line=dict(color='#ff7f0e', width=3, dash='dot')),
            secondary_y=True,
        )
        
        fig1.update_layout(
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=0, r=0, t=40, b=0)
        )
        fig1.update_yaxes(title_text=FRED_SERIES["Industrial/Economic Metrics"].get(selected_ind, selected_ind), secondary_y=False)
        fig1.update_yaxes(title_text=f"{selected_rate} (%)", secondary_y=True)
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("Pearson Correlation Matrix")
        # Calculate correlation
        corr_matrix = df_merged[[selected_rate, selected_ind, selected_vol]].corr()
        
        fig2 = px.imshow(corr_matrix, text_auto=True, aspect="auto", 
                         color_continuous_scale='RdBu_r', range_color=[-1, 1])
        fig2.update_layout(margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # --- Volatility Tracking Pipeline ---
    st.subheader("Automated Volatility Tracking")
    
    # Calculate rolling 6-month volatility for the industrial metric
    window = 6
    df_merged['Ind_Rolling_Vol'] = df_merged[selected_ind].pct_change().rolling(window=window).std() * np.sqrt(12) * 100
    
    col3, col4 = st.columns([1, 1])
    
    with col3:
        st.markdown(f"**{selected_vol} (Market Volatility Marker)**")
        fig3 = px.area(df_merged, x='date', y=selected_vol, color_discrete_sequence=['#d62728'])
        fig3.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig3, use_container_width=True)
        
    with col4:
        st.markdown(f"**{selected_ind} - 6-Month Rolling Volatility (Annualized %)**")
        # Dropna for the rolling calculation specifically for plotting
        df_plot = df_merged.dropna(subset=['Ind_Rolling_Vol'])
        fig4 = px.line(df_plot, x='date', y='Ind_Rolling_Vol', color_discrete_sequence=['#9467bd'])
        fig4.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig4, use_container_width=True)

else:
    st.warning("Insufficient data available for the selected timeframe and parameters.")