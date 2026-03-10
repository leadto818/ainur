"""
Market π Terms Demo
===================

A Streamlit demonstration of "Market π Terms" — dimensionless ratios used to identify market regimes.
Based on the "Quantity / Dimensionless / Generative State" framework.

Features:
- Main Chart: Price (Candlestick/Line)
- Sub Chart: Dimensionless π Terms (Vol-adjusted returns, Trend ratios, etc.)
- Regime Classification: Based on stable intervals of π terms.
- Theoretical Context: Explanations of the Physics/Market/Cultivation mapping.
"""

import time
import os
from dataclasses import dataclass
from typing import Optional, List

import pandas as pd
import requests
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- Constants & Configuration ---
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"
DEFAULT_ALPHA_VANTAGE_API_KEY = "L9B4KOXCHPSAURRL"  # Provided in prompt

@dataclass
class AVConfig:
    apikey: str
    symbol: str
    outputsize: str = "compact"
    function: str = "TIME_SERIES_DAILY"

# --- Data Fetching ---
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_alpha_vantage_daily(cfg: AVConfig, max_retries: int = 3, backoff_sec: float = 2.0) -> pd.DataFrame:
    """Fetch daily OHLCV data from Alpha Vantage."""
    params = {
        "function": cfg.function,
        "symbol": cfg.symbol,
        "outputsize": cfg.outputsize,
        "datatype": "json",
        "apikey": cfg.apikey,
    }

    last_note = None
    for attempt in range(max_retries):
        try:
            r = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()

            if "Note" in data:
                last_note = data["Note"]
                time.sleep(backoff_sec)
                continue
            if "Error Message" in data:
                raise RuntimeError(data["Error Message"])
            
            ts_key = "Time Series (Daily)"
            ts = data.get(ts_key)
            if not ts:
                # Sometimes API returns generic info or limit reached without error text
                time.sleep(backoff_sec)
                continue
            
            df = pd.DataFrame.from_dict(ts, orient="index").sort_index()
            df = df.astype(float)
            df.rename(columns={
                "1. open": "open", "2. high": "high", "3. low": "low",
                "4. close": "close", "5. volume": "volume"
            }, inplace=True)
            df.index = pd.to_datetime(df.index)
            df.index.name = "date"
            return df
        
        except Exception as e:
            time.sleep(backoff_sec)
    
    raise RuntimeError(f"Failed to fetch data. Last note: {last_note}")

# --- Logic: Market π Terms Construction ---
def build_market_pi_terms(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Construct dimensionless π terms.
    
    Core Terms:
    - pi_ret_z: Return / Volatility (Force relative to Noise)
    - pi_trend: Fast EMA / Slow EMA - 1 (Trend Intensity)
    - pi_range: (High - Low) / Close (Intraday volatility structure)
    - vol_z:    (DollarVol - Mean) / Std (Liquidity Anomaly Score)
    """
    out = df.copy()
    
    # 1. Standard Returns & Volatility
    out["ret"] = out["close"].pct_change()
    out["vol"] = out["ret"].rolling(window).std()
    
    # 2. π Term: Return Z-Score (Signal-to-Noise)
    # Reflects "Intensity" relative to "State"
    out["pi_ret_z"] = out["ret"] / out["vol"].replace(0, pd.NA)

    # 3. Liquidity / Activity Structure
    out["dollar_vol"] = out["close"] * out["volume"]
    dv_mean = out["dollar_vol"].rolling(window).mean()
    dv_std = out["dollar_vol"].rolling(window).std()
    # Dimensionless Volume Z-Score
    out["vol_z"] = (out["dollar_vol"] - dv_mean) / dv_std.replace(0, pd.NA)

    # 4. Intraday Range Structure 
    out["pi_range"] = (out["high"] - out["low"]) / out["close"].replace(0, pd.NA)

    # 5. Trend Structure (Dimensionless Moving Average Ratio)
    ema_fast = out["close"].ewm(span=max(3, window // 2), adjust=False).mean()
    ema_slow = out["close"].ewm(span=max(6, window), adjust=False).mean()
    out["pi_trend"] = (ema_fast / ema_slow) - 1.0

    return out

# --- Logic: Regime Classification ---
def classify_regime(df: pd.DataFrame) -> pd.Series:
    """
    Classify Market Regimes based on 'Dimensionless Ratio' Stability Intervals.
    
    Theory Mapping:
    - Range (Oscillation): Low Trend Strength, Normal Vol Z
    - Trend (Up/Down): High Trend Strength + Directional Return Intensity
    - Transition/Chaos: High Vol Z, Conflicting Signals
    """
    if len(df) < 50:
        return pd.Series(["insufficient_data"] * len(df), index=df.index)

    # Calculate dynamic thresholds (Learning the 'Stable Interval')
    # In a real agent, this would be an online learning process. Here we use quantiles.
    pi_trend = df["pi_trend"].dropna()
    pi_ret = df["pi_ret_z"].dropna()
    
    trend_upper = pi_trend.quantile(0.75)
    trend_lower = pi_trend.quantile(0.25)
    ret_quiet = pi_ret.abs().quantile(0.4)
    
    def get_status(row):
        t = row["pi_trend"]
        r = row["pi_ret_z"]
        
        if pd.isna(t) or pd.isna(r): return "Unknown"
        
        # 1. Trend States
        if t > trend_upper:
            return "Trend UP (Strong Flow)"
        if t < trend_lower:
            return "Trend DOWN (Liquidation)"
            
        # 2. Range/Oscillation States
        if abs(r) < ret_quiet:
            return "Stable Range (Laminar)"
            
        # 3. Everything else is Transition/Noise
        return "Transition / Noise"

    return df.apply(get_status, axis=1)

# --- UI: Plotting ---
def plot_dashboard(df: pd.DataFrame, pi_cols: List[str]):
    """Create a combined chart with Price and selected π Terms."""
    
    # Create subplots: Row 1 = Price, Row 2 = π Terms
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.05,
        row_heights=[0.6, 0.4],
        subplot_titles=("Price Action", "Market π Terms (Dimensionless)")
    )

    # Price Chart (Candlestick)
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["open"], high=df["high"],
        low=df["low"], close=df["close"],
        name="Price"
    ), row=1, col=1)

    # π Terms Chart
    for col in pi_cols:
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[col],
                mode='lines', name=col
            ), row=2, col=1)

    # Add Zero Line for π terms
    fig.add_shape(type="line",
        x0=df.index[0], y0=0, x1=df.index[-1], y1=0,
        line=dict(color="gray", width=1, dash="dash"),
        row=2, col=1
    )

    fig.update_layout(
        height=700,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

# --- Main App ---
def main():
    st.set_page_config(page_title="Market π Terms", layout="wide", page_icon="🌊")

    # -- Sidebar --
    with st.sidebar:
        st.title("⚙️ Control Panel")
        
        st.subheader("Data Source")
        symbol = st.text_input("Symbol", value="TSLA")
        api_key = st.text_input("API Key", value=DEFAULT_ALPHA_VANTAGE_API_KEY, type="password")
        
        st.subheader("π Matrix Config")
        window = st.slider("Window (Time Scale)", 5, 100, 20, help="The 'L' (Characteristic Length) in Re = ρvL/μ")
        
        st.subheader("Visualization")
        pi_options = ["pi_ret_z", "pi_trend", "pi_range", "vol_z"]
        selected_pi = st.multiselect("Select π Terms", pi_options, default=["pi_ret_z", "pi_trend"])
        
        history_len = st.select_slider("Display History", options=["1 Month", "3 Months", "6 Months", "1 Year", "All"], value="6 Months")
        
        st.markdown("---")
        st.markdown("**Theoretical Basis**")
        st.info(
            """
            **Dimensionless Analysis**
            
            Just as Reynolds Number (Re) predicts turbulence without caring about specific velocity units, **Market π Terms** predict market regimes (Trend vs Range) without relying on absolute price levels.
            """
        )

    # -- Main Content --
    st.title("Market π Terms Analysis")
    st.markdown(
        """
        > *"The behavior of the world is not determined by 'Quantity', but by the 'Generative Relationship between Quantities'."*
        """
    )
    
    # Fetch & Process
    try:
        cfg = AVConfig(apikey=api_key, symbol=symbol)
        with st.spinner(f"Sampling Market Quantities for {symbol}..."):
            raw_df = fetch_alpha_vantage_daily(cfg)
            
        # Filter by History
        if history_len == "1 Month": raw_df = raw_df.tail(22)
        elif history_len == "3 Months": raw_df = raw_df.tail(66)
        elif history_len == "6 Months": raw_df = raw_df.tail(132)
        elif history_len == "1 Year": raw_df = raw_df.tail(252)
        
        # Calculate π Terms
        df_pi = build_market_pi_terms(raw_df, window=window)
        
        # Classify Regime
        df_pi["regime"] = classify_regime(df_pi)
        
    except Exception as e:
        st.error(f"Error initializing system: {e}")
        st.stop()

    # -- Dashboard Layout --
    col_main, col_metrics = st.columns([3, 1])

    with col_main:
        # Chart
        st.plotly_chart(plot_dashboard(df_pi, selected_pi), use_container_width=True)
        
        # Theoretical Context Expander
        with st.expander("📚 Concept: The Tripartite Roadmap (Physical / Market / Cultivation)"):
            st.markdown("""
            ### 1. Physics (The Flow)
            - **Formula**: $Re = \\frac{\\rho v L}{\\mu}$
            - **Meaning**: Flow state (Laminar vs Turbulent) depends on the *ratio* of inertial forces to viscous forces, not absolute speed.
            
            ### 2. Market (The Vibe)
            - **Formula**: $\\pi_{market} = \\frac{\\text{Emotion/Flow}}{\\text{Capacity/Vol}}$
            - **Meaning**: Market regimes (Trend vs Mean Reversion) depend on the *ratio* of purchasing pressure to liquidity capability.
            
            ### 3. Cultivation (The Way)
            - **Ref**: *Huainanzi* - "Indeterminate (Wu-Liang), hence getting the 'Righteousness' (Yi)."
            - **Meaning**: Correct action doesn't come from fixed rules, but from assessing the *relative* situation (Time, Place, Event, Momentum).
            """)

    with col_metrics:
        st.subheader("Regime Radar")
        
        # Latest State
        last_row = df_pi.iloc[-1]
        st.metric("Current Regime", last_row["regime"])
        
        st.markdown("### π Statistics")
        st.metric("Trend Intensity (π_trend)", f"{last_row['pi_trend']:.4f}", delta_color="normal")
        st.metric("Return Force (π_ret_z)", f"{last_row['pi_ret_z']:.2f}")
        st.metric("Liq. Anomaly (vol_z)", f"{last_row['vol_z']:.2f}")
        
        st.markdown("---")
        st.markdown("### Regime Distribution")
        regime_counts = df_pi["regime"].value_counts()
        st.bar_chart(regime_counts)
        
        st.download_button(
            "Download CSV",
            df_pi.to_csv().encode('utf-8'),
            f"{symbol}_pi_terms.csv",
            "text/csv"
        )

    # -- Data Preview --
    st.markdown("### Data Preview (Dimensionless View)")
    st.dataframe(df_pi.tail(10).style.format("{:.4f}", subset=["pi_ret_z", "pi_trend", "pi_range", "vol_z"]), use_container_width=True)

if __name__ == "__main__":
    main()
