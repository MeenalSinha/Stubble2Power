import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from sklearn.cluster import KMeans
import folium
from streamlit_folium import folium_static
import random

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="Stubble2Power - Green Energy Revolution",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# GLASSMORPHISM + MODERN UI THEME
# ============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Gradient background */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Glassmorphism sidebar */
    [data-testid="stSidebar"] {
        background: rgba(163, 201, 168, 0.3);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.3);
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #2d5f3f !important;
        font-weight: 700;
    }
    
    h1 {
        background: linear-gradient(135deg, #2d5f3f 0%, #5a9367 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Glass cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.4);
        transition: all 0.3s ease;
        animation: fadeIn 0.6s ease-out;
    }
    
    .glass-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 35px rgba(0, 0, 0, 0.12);
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Hero section */
    .hero-section {
        background: linear-gradient(135deg, rgba(163, 201, 168, 0.6), rgba(138, 180, 145, 0.6));
        backdrop-filter: blur(20px);
        border-radius: 25px;
        padding: 3rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.3);
        margin-bottom: 2rem;
        animation: heroFadeIn 1s ease-out;
    }
    
    @keyframes heroFadeIn {
        from { opacity: 0; transform: scale(0.95); }
        to { opacity: 1; transform: scale(1); }
    }
    
    .hero-logo {
        font-size: 4rem;
        animation: bounce 4s ease-in-out infinite;
    }
    
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-8px); }
    }
    
    .hero-title {
        color: white !important;
        font-size: 3.5rem;
        font-weight: 900;
        margin: 1rem 0;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    .hero-subtitle {
        color: white;
        font-size: 1.5rem;
        font-weight: 400;
        opacity: 0.95;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #5a9367 0%, #7db88a 100%);
        color: white;
        border-radius: 15px;
        height: 3.5em;
        width: 100%;
        font-size: 1.1em;
        font-weight: 700;
        border: none;
        box-shadow: 0 4px 15px rgba(90, 147, 103, 0.4);
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #4a7d57 0%, #6da77a 100%);
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(90, 147, 103, 0.5);
    }
    
    /* Metric cards */
    .metric-glass-card {
        background: linear-gradient(135deg, rgba(163, 201, 168, 0.7), rgba(138, 180, 145, 0.7));
        backdrop-filter: blur(15px);
        padding: 1.8rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.3);
        transition: all 0.3s ease;
        animation: fadeInUp 0.6s ease-out;
    }
    
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .metric-glass-card:hover {
        transform: translateY(-5px) scale(1.02);
        box-shadow: 0 10px 35px rgba(163, 201, 168, 0.35);
    }
    
    .metric-value {
        font-size: 3rem;
        font-weight: 900;
        margin: 0.5rem 0;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .metric-label {
        font-size: 1rem;
        opacity: 0.95;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Alert boxes */
    .glass-alert-success {
        background: rgba(212, 241, 221, 0.7);
        backdrop-filter: blur(10px);
        border-left: 5px solid #5a9367;
        padding: 1.2rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(90, 147, 103, 0.2);
    }
    
    .glass-alert-warning {
        background: rgba(255, 243, 205, 0.7);
        backdrop-filter: blur(10px);
        border-left: 5px solid #f9c74f;
        padding: 1.2rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(249, 199, 79, 0.2);
    }
    
    .glass-alert-danger {
        background: rgba(255, 229, 229, 0.7);
        backdrop-filter: blur(10px);
        border-left: 5px solid #f44336;
        padding: 1.2rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(244, 67, 54, 0.2);
        animation: pulse 3s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.01); }
    }
    
    .glass-alert-info {
        background: rgba(227, 242, 253, 0.7);
        backdrop-filter: blur(10px);
        border-left: 5px solid #2196f3;
        padding: 1.2rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(33, 150, 243, 0.2);
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #5a9367 0%, #7db88a 100%);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(245, 223, 208, 0.5);
        backdrop-filter: blur(10px);
        border-radius: 15px 15px 0 0;
        color: #2d5f3f;
        padding: 12px 24px;
        font-weight: 700;
        border: 1px solid rgba(255, 255, 255, 0.3);
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(245, 223, 208, 0.8);
        transform: translateY(-2px);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(163, 201, 168, 0.8), rgba(138, 180, 145, 0.8));
        color: white;
        box-shadow: 0 4px 15px rgba(163, 201, 168, 0.3);
    }
    
    /* Tech badges */
    .tech-badge {
        display: inline-block;
        background: linear-gradient(135deg, #5a9367, #7db88a);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        margin: 0.3rem;
        font-size: 0.9rem;
        font-weight: 600;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
    }
    
    /* Footer */
    .footer {
        background: rgba(234, 231, 220, 0.6);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        margin-top: 3rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CENTRALIZED ASSUMPTIONS
# ============================================================================
SCENARIOS = {
    "Conservative": {
        "briquette_yield": 0.6,
        "biochar_yield": 0.15,
        "processing_cost_per_ton": 1000,
        "briquette_price": 5,
        "biochar_price": 12,
        "carbon_credit_per_ton": 400,
        "farmer_payment_per_ton": 1200,
        "mobile_unit_cost_per_km": 180,
        "co2_per_ton_stubble": 1.2,
        "coal_replaced_ratio": 0.6,
        "processing_time_per_ton": 2.5
    },
    "Base Case": {
        "briquette_yield": 0.7,
        "biochar_yield": 0.2,
        "processing_cost_per_ton": 800,
        "briquette_price": 6,
        "biochar_price": 15,
        "carbon_credit_per_ton": 500,
        "farmer_payment_per_ton": 1500,
        "mobile_unit_cost_per_km": 150,
        "co2_per_ton_stubble": 1.5,
        "coal_replaced_ratio": 0.8,
        "processing_time_per_ton": 2
    },
    "Optimistic": {
        "briquette_yield": 0.75,
        "biochar_yield": 0.22,
        "processing_cost_per_ton": 700,
        "briquette_price": 7,
        "biochar_price": 18,
        "carbon_credit_per_ton": 600,
        "farmer_payment_per_ton": 1800,
        "mobile_unit_cost_per_km": 120,
        "co2_per_ton_stubble": 1.8,
        "coal_replaced_ratio": 0.9,
        "processing_time_per_ton": 1.8
    }
}

# Sample villages
SAMPLE_VILLAGES = {
    'Khanna': (30.7056, 76.2222), 'Ludhiana': (30.9010, 75.8573),
    'Moga': (30.8158, 75.1711), 'Ferozepur': (30.9180, 74.6130),
    'Bathinda': (30.2110, 74.9455), 'Patiala': (30.3398, 76.3869),
    'Sangrur': (30.2459, 75.8421), 'Barnala': (30.3779, 75.5483),
    'Mansa': (29.9880, 75.3930), 'Muktsar': (30.4754, 74.5146),
    'Faridkot': (30.6726, 74.7556), 'Kapurthala': (31.3800, 75.3800),
    'Jalandhar': (31.3260, 75.5762), 'Hoshiarpur': (31.5340, 75.9110),
    'Amritsar': (31.6340, 74.8723)
}

# Initialize session state
if 'farmer_data' not in st.session_state:
    st.session_state.farmer_data = pd.DataFrame(columns=[
        'Farmer Name', 'Village', 'District', 'Acres', 'Stubble (tons)', 
        'Harvest Date', 'Latitude', 'Longitude'
    ])
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'scenario' not in st.session_state:
    st.session_state.scenario = "Base Case"
if 'operational_months' not in st.session_state:
    st.session_state.operational_months = 6

# ============================================================================
# BUSINESS LOGIC FUNCTIONS
# ============================================================================
def calculate_unit_economics(stubble_tons, assumptions, transport_cost):
    """Calculate complete unit economics"""
    stubble_kg = stubble_tons * 1000
    briquette_prod = stubble_kg * assumptions["briquette_yield"]
    biochar_prod = stubble_kg * assumptions["biochar_yield"]
    briquette_revenue = briquette_prod * assumptions["briquette_price"]
    biochar_revenue = biochar_prod * assumptions["biochar_price"]
    carbon_revenue = stubble_tons * assumptions["carbon_credit_per_ton"]
    total_revenue = briquette_revenue + biochar_revenue + carbon_revenue
    processing_cost = stubble_tons * assumptions["processing_cost_per_ton"]
    farmer_payment = stubble_tons * assumptions["farmer_payment_per_ton"]
    total_cost = processing_cost + farmer_payment + transport_cost
    profit = total_revenue - total_cost
    margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
    cost_per_ton = total_cost / stubble_tons if stubble_tons > 0 else 0
    revenue_per_ton = total_revenue / stubble_tons if stubble_tons > 0 else 0
    
    return {
        'production': {'briquette_kg': briquette_prod, 'biochar_kg': biochar_prod},
        'revenue': {'briquette': briquette_revenue, 'biochar': biochar_revenue, 'carbon': carbon_revenue, 'total': total_revenue},
        'cost': {'processing': processing_cost, 'farmer_payment': farmer_payment, 'transport': transport_cost, 'total': total_cost},
        'metrics': {'profit': profit, 'margin': margin, 'cost_per_ton': cost_per_ton, 'revenue_per_ton': revenue_per_ton,
                   'breakeven_tons': total_cost / revenue_per_ton if revenue_per_ton > 0 else 0}
    }

def calculate_environmental_impact(stubble_tons, assumptions):
    """Calculate environmental impact"""
    co2_avoided = stubble_tons * assumptions["co2_per_ton_stubble"]
    coal_replaced = stubble_tons * assumptions["coal_replaced_ratio"]
    return {
        'co2_avoided': co2_avoided, 'coal_replaced': coal_replaced,
        'trees_equivalent': int(co2_avoided * 33), 'cars_equivalent': int(co2_avoided * 0.22),
        'homes_powered': int(coal_replaced * 2)
    }

def calculate_logistics_savings(mobile_cost, stubble_tons):
    """Calculate logistics savings"""
    central_cost = stubble_tons * 100 * 150 / 10
    savings = central_cost - mobile_cost
    reduction_pct = (savings / central_cost * 100) if central_cost > 0 else 0
    return {'mobile_cost': mobile_cost, 'central_cost': central_cost, 'savings': savings, 'reduction_pct': reduction_pct}

# ============================================================================
# MAIN APP
# ============================================================================
def main():
    # Hero Section
    st.markdown("""
    <div class="hero-section">
        <div class="hero-logo">🌾</div>
        <h1 class="hero-title">Stubble2Power</h1>
        <p class="hero-subtitle">
            Mobile Bio-Refineries Transforming Agricultural Waste into Clean Energy
        </p>
        <div style="margin-top: 1.5rem;">
            <span class="tech-badge">🚛 Mobile Units</span>
            <span class="tech-badge">♻️ Zero Emission</span>
            <span class="tech-badge">💰 70% Cost Savings</span>
            <span class="tech-badge">🌍 Carbon Negative</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Impact banner
    st.markdown("""
    <div class="glass-alert-info">
        <strong>📊 Impact:</strong> India burns 23M tons of stubble annually causing ₹20B in losses. 
        Stubble2Power eliminates burning while creating value for farmers.
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar Configuration
    with st.sidebar:
        st.title("🌾 Stubble2Power")
        
        st.warning("""
        ⚠️ **Prototype Disclaimer**
        
        This is a simulation for pilot planning. All costs, outputs, and impact figures are estimates based on industry assumptions.
        """)
        
        st.markdown("---")
        st.markdown("### ⚙️ Configuration")
        
        scenario = st.selectbox(
            "Select Scenario",
            ["Conservative", "Base Case", "Optimistic"],
            index=1,
            help="Different scenarios with varying assumptions"
        )
        st.session_state.scenario = scenario
        
        operational_months = st.slider(
            "Operational Months/Year",
            min_value=3, max_value=12, value=6,
            help="Number of months the system operates annually"
        )
        st.session_state.operational_months = operational_months
        
        st.markdown("---")
        st.markdown("### 📊 Quick Stats")
        if not st.session_state.farmer_data.empty:
            st.metric("Farmers", len(st.session_state.farmer_data))
            st.metric("Stubble", f"{st.session_state.farmer_data['Stubble (tons)'].sum():.0f}t")
            if st.session_state.processed_data:
                st.metric("Clusters", len(st.session_state.processed_data['cluster_metrics']))
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.info(
            "**Stubble2Power** transforms agricultural waste into clean energy using mobile bio-refineries.\n\n"
            "**Track:** Energy & Sustainability"
        )
    
    # Navigation Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Home", "📥 Data Input", "🗺️ Clustering", "💰 Economics", "📊 Dashboard"
    ])
    
    # TAB 1: HOME
    with tab1:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="glass-card">
                <h2 style="text-align: center; color: #f44336 !important;">🔥</h2>
                <h4 style="text-align: center;">The Problem</h4>
                <p style="text-align: center; color: #666;">
                    23M tons of stubble burned annually causing ₹20B damage and severe air pollution (AQI 400+)
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="glass-card">
                <h2 style="text-align: center; color: #5a9367 !important;">🚛</h2>
                <h4 style="text-align: center;">Our Solution</h4>
                <p style="text-align: center; color: #666;">
                    Mobile bio-refineries visit farmers, process stubble on-site, and pay directly
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="glass-card">
                <h2 style="text-align: center; color: #2196f3 !important;">🎯</h2>
                <h4 style="text-align: center;">Impact</h4>
                <p style="text-align: center; color: #666;">
                    70% cost reduction, 3x faster processing, ₹150L annual farmer income
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("### 📈 System Benefits")
        col1, col2, col3, col4 = st.columns(4)
        
        metrics = [
            ("Logistics", "70%", "Cost Saved"),
            ("Processing", "2hrs", "Per Ton"),
            ("Farmer Pay", "₹1500", "Per Ton"),
            ("Margin", "30%", "Profit")
        ]
        
        for col, (label, value, sublabel) in zip([col1, col2, col3, col4], metrics):
            with col:
                st.markdown(f"""
                <div class="metric-glass-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-label" style="font-size: 0.8rem;">{sublabel}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🚀 Quick Start")
        
        col_demo1, col_demo2 = st.columns([2, 1])
        
        with col_demo1:
            if st.button("🎬 Run Quick Demo", key="demo_home"):
                st.balloons()
                st.success("✅ Demo ready! Go to Data Input → Add Sample Farmers → Generate Clusters")
        
        with col_demo2:
            st.markdown("""
            <div class="glass-alert-success">
                <strong>💡 Demo Flow:</strong><br>
                1. Add farmers<br>
                2. Generate clusters<br>
                3. View dashboard
            </div>
            """, unsafe_allow_html=True)
    
    # TAB 2: DATA INPUT
    with tab2:
        st.markdown("### 📥 Farmer Data Collection")
        
        st.markdown("""
        <div class="glass-alert-info">
            <strong>📋 Data Collection:</strong> Register farmers with their location and stubble availability for optimal mobile unit deployment
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### 👨‍🌾 Register New Farmer")
            with st.form("farmer_form"):
                fname = st.text_input("Farmer Name", placeholder="Enter farmer name")
                village = st.selectbox("Village", list(SAMPLE_VILLAGES.keys()))
                district = st.text_input("District", "Punjab")
                acres = st.number_input("Acres Cultivated", min_value=1, max_value=100, value=10)
                stubble = st.number_input("Estimated Stubble (tons)", min_value=1, max_value=50, value=5)
                harvest_date = st.date_input("Harvest Date", datetime.now())
                
                submit = st.form_submit_button("✅ Register Farmer", use_container_width=True)
                
                if submit and fname and village:
                    lat, lon = SAMPLE_VILLAGES[village]
                    lat += random.uniform(-0.05, 0.05)
                    lon += random.uniform(-0.05, 0.05)
                    
                    new_data = pd.DataFrame({
                        'Farmer Name': [fname], 'Village': [village], 'District': [district],
                        'Acres': [acres], 'Stubble (tons)': [stubble], 'Harvest Date': [harvest_date],
                        'Latitude': [lat], 'Longitude': [lon]
                    })
                    
                    st.session_state.farmer_data = pd.concat([st.session_state.farmer_data, new_data], ignore_index=True)
                    st.success(f"✅ Farmer {fname} registered successfully!")
                    st.balloons()
        
        with col2:
            st.markdown("#### 🚀 Quick Actions")
            
            st.markdown("""
            <div class="glass-card">
                <h5 style="text-align: center; color: #5a9367 !important;">Sample Data</h5>
                <p style="text-align: center; color: #666; margin: 1rem 0;">
                    Instantly populate the system with 20 sample farmers for testing
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📦 Add 20 Sample Farmers", use_container_width=True):
                sample_data = []
                for i in range(20):
                    village = random.choice(list(SAMPLE_VILLAGES.keys()))
                    lat, lon = SAMPLE_VILLAGES[village]
                    lat += random.uniform(-0.05, 0.05)
                    lon += random.uniform(-0.05, 0.05)
                    
                    sample_data.append({
                        'Farmer Name': f"Farmer_{i+1}", 'Village': village, 'District': 'Punjab',
                        'Acres': random.randint(5, 50), 'Stubble (tons)': random.randint(3, 30),
                        'Harvest Date': datetime.now() + timedelta(days=random.randint(0, 30)),
                        'Latitude': lat, 'Longitude': lon
                    })
                
                st.session_state.farmer_data = pd.concat([st.session_state.farmer_data, pd.DataFrame(sample_data)], ignore_index=True)
                st.success("✅ Added 20 sample farmers!")
                st.balloons()
        
        if not st.session_state.farmer_data.empty:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 📊 Registered Farmers Database")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="metric-glass-card">
                    <div class="metric-label">Total Farmers</div>
                    <div class="metric-value">{len(st.session_state.farmer_data)}</div>
                    <div class="metric-label" style="font-size: 0.8rem;">Enrolled</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-glass-card">
                    <div class="metric-label">Total Acres</div>
                    <div class="metric-value">{st.session_state.farmer_data['Acres'].sum():.0f}</div>
                    <div class="metric-label" style="font-size: 0.8rem;">Cultivated</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-glass-card">
                    <div class="metric-label">Total Stubble</div>
                    <div class="metric-value">{st.session_state.farmer_data['Stubble (tons)'].sum():.0f}t</div>
                    <div class="metric-label" style="font-size: 0.8rem;">Available</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="metric-glass-card">
                    <div class="metric-label">Villages</div>
                    <div class="metric-value">{st.session_state.farmer_data['Village'].nunique()}</div>
                    <div class="metric-label" style="font-size: 0.8rem;">Covered</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Data table with download
            col_table, col_download = st.columns([3, 1])
            
            with col_table:
                st.dataframe(st.session_state.farmer_data, use_container_width=True, height=400)
            
            with col_download:
                st.markdown("##### 📥 Export Data")
                farmer_csv = st.session_state.farmer_data.to_csv(index=False)
                st.download_button(
                    "📄 Download CSV",
                    farmer_csv,
                    "farmer_data.csv",
                    "text/csv",
                    use_container_width=True
                )
                
                st.markdown("""
                <div class="glass-alert-success" style="margin-top: 1rem;">
                    <strong>✅ Ready for Clustering</strong><br>
                    Proceed to the Clustering tab to generate optimal mobile unit routes
                </div>
                """, unsafe_allow_html=True)
    
    # TAB 3: CLUSTERING
    with tab3:
        st.markdown("### 🗺️ Clustering & Route Optimization")
        
        if st.session_state.farmer_data.empty:
            st.markdown("""
            <div class="glass-alert-warning">
                <strong>⚠️ No Farmer Data Available</strong><br>
                Please add farmer data in the Data Input tab first before generating clusters.
            </div>
            """, unsafe_allow_html=True)
            return
        
        df = st.session_state.farmer_data.copy()
        assumptions = SCENARIOS[st.session_state.scenario]
        
        st.markdown("""
        <div class="glass-alert-info">
            <strong>🤖 AI-Powered Clustering:</strong> Using K-Means algorithm to group farmers into optimal clusters for mobile bio-refinery deployment
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### ⚙️ Clustering Configuration")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            n_clusters = st.slider("Number of Mobile Units (Clusters)", 2, 8, 4,
                                  help="More units = shorter routes but higher deployment cost")
        
        with col2:
            st.markdown(f"""
            <div class="glass-card" style="padding: 1rem;">
                <strong>Current Settings:</strong><br>
                • Scenario: {st.session_state.scenario}<br>
                • Transport Cost: ₹{assumptions['mobile_unit_cost_per_km']}/km<br>
                • Total Farmers: {len(df)}
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            process_btn = st.button("🚀 Generate Clusters", type="primary", use_container_width=True)
        
        if process_btn:
            with st.spinner("🔄 Processing clusters..."):
                coords = df[['Latitude', 'Longitude']].values
                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                df['Cluster'] = kmeans.fit_predict(coords)
                
                cluster_metrics = df.groupby('Cluster').agg({
                    'Stubble (tons)': 'sum', 'Farmer Name': 'count', 'Village': 'nunique'
                }).reset_index()
                cluster_metrics.columns = ['Cluster', 'Total Stubble (tons)', 'Farmers', 'Villages']
                
                cluster_metrics['Avg Distance (km)'] = 0.0
                cluster_metrics['Transport Cost (INR)'] = 0.0
                
                for cluster_id in range(n_clusters):
                    cluster_data = df[df['Cluster'] == cluster_id]
                    if len(cluster_data) > 1:
                        coords_cluster = cluster_data[['Latitude', 'Longitude']].values
                        distances = []
                        for i in range(len(coords_cluster)):
                            for j in range(i+1, len(coords_cluster)):
                                dist = np.sqrt((coords_cluster[i][0] - coords_cluster[j][0])**2 + 
                                             (coords_cluster[i][1] - coords_cluster[j][1])**2) * 111
                                distances.append(dist)
                        
                        avg_dist = np.mean(distances) if distances else 0
                        cluster_metrics.loc[cluster_metrics['Cluster'] == cluster_id, 'Avg Distance (km)'] = float(avg_dist)
                        cluster_metrics.loc[cluster_metrics['Cluster'] == cluster_id, 'Transport Cost (INR)'] = float(avg_dist * assumptions["mobile_unit_cost_per_km"])
                
                st.session_state.processed_data = {'df': df, 'cluster_metrics': cluster_metrics, 'kmeans': kmeans}
            
            st.success("✅ Clustering completed successfully!")
            st.balloons()
        
        if st.session_state.processed_data:
            data = st.session_state.processed_data
            df = data['df']
            cluster_metrics = data['cluster_metrics']
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 📊 Cluster Summary")
            
            # Cluster metrics
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.dataframe(cluster_metrics.style.format({
                    'Total Stubble (tons)': '{:.0f}',
                    'Avg Distance (km)': '{:.1f}',
                    'Transport Cost (INR)': '₹{:,.0f}'
                }), use_container_width=True)
            
            with col2:
                total_stubble = df['Stubble (tons)'].sum()
                mobile_cost = cluster_metrics['Transport Cost (INR)'].sum()
                logistics = calculate_logistics_savings(mobile_cost, total_stubble)
                
                st.markdown(f"""
                <div class="metric-glass-card">
                    <div class="metric-label">Logistics Saved</div>
                    <div class="metric-value">{logistics['reduction_pct']:.0f}%</div>
                    <div class="metric-label" style="font-size: 0.8rem;">vs Central Plant</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="glass-alert-success" style="margin-top: 1rem;">
                    <strong>💰 Cost Savings:</strong><br>
                    ₹{logistics['savings']:,.0f} saved in logistics
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 🗺️ Interactive Cluster Map")
            st.caption("Mobile bio-refinery units deployed across farmer clusters with optimized routes")
            
            m = folium.Map(location=[30.7333, 76.7794], zoom_start=8)
            colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightblue', 'darkgreen']
            
            for idx, row in df.iterrows():
                folium.CircleMarker(
                    location=[row['Latitude'], row['Longitude']],
                    radius=5 + row['Stubble (tons)'] / 2,
                    popup=f"<b>{row['Farmer Name']}</b><br>Village: {row['Village']}<br>Stubble: {row['Stubble (tons)']} tons<br>Cluster: {int(row['Cluster']) + 1}",
                    color=colors[int(row['Cluster']) % len(colors)],
                    fill=True, fillColor=colors[int(row['Cluster']) % len(colors)],
                    fillOpacity=0.7
                ).add_to(m)
            
            for cluster_id in range(len(cluster_metrics)):
                cluster_data = df[df['Cluster'] == cluster_id]
                center_lat = cluster_data['Latitude'].mean()
                center_lon = cluster_data['Longitude'].mean()
                
                folium.Marker(
                    location=[center_lat, center_lon],
                    popup=f"<b>Mobile Unit {cluster_id + 1}</b><br>Stubble: {cluster_metrics.iloc[cluster_id]['Total Stubble (tons)']} tons<br>Farmers: {cluster_metrics.iloc[cluster_id]['Farmers']}",
                    icon=folium.Icon(color=colors[cluster_id % len(colors)], icon='truck', prefix='fa')
                ).add_to(m)
            
            folium_static(m, width=1400, height=500)
            
            col1, col2, col3 = st.columns(3)
            col1.info("🔵 **Circles** = Farmers (size = stubble volume)")
            col2.success("🚛 **Trucks** = Mobile unit deployment centers")
            col3.warning(f"📍 **{logistics['reduction_pct']:.0f}% logistics reduction** vs central plant")
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 💰 Cost Comparison Analysis")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div class="metric-glass-card">
                    <div class="metric-label">Mobile Units Cost</div>
                    <div class="metric-value">₹{logistics['mobile_cost']/1000:.0f}K</div>
                    <div class="metric-label" style="font-size: 0.8rem;">Total transport</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-glass-card">
                    <div class="metric-label">Central Plant Cost</div>
                    <div class="metric-value">₹{logistics['central_cost']/1000:.0f}K</div>
                    <div class="metric-label" style="font-size: 0.8rem;">Estimated</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-glass-card">
                    <div class="metric-label">Cost Reduction</div>
                    <div class="metric-value">{logistics['reduction_pct']:.1f}%</div>
                    <div class="metric-label" style="font-size: 0.8rem;">₹{logistics['savings']:,.0f} saved</div>
                </div>
                """, unsafe_allow_html=True)
    
    # TAB 4: ECONOMICS
    with tab4:
        st.markdown("### 💰 Processing & Economic Simulation")
        
        if not st.session_state.processed_data:
            st.markdown("""
            <div class="glass-alert-warning">
                <strong>⚠️ No Data Available</strong><br>
                Please complete Layer 2 (Clustering) first to view economics analysis.
            </div>
            """, unsafe_allow_html=True)
            return
        
        df = st.session_state.processed_data['df']
        cluster_metrics = st.session_state.processed_data['cluster_metrics']
        total_stubble = df['Stubble (tons)'].sum()
        assumptions = SCENARIOS[st.session_state.scenario]
        transport_cost = cluster_metrics['Transport Cost (INR)'].sum()
        
        economics = calculate_unit_economics(total_stubble, assumptions, transport_cost)
        
        # Success banner
        st.markdown("""
        <div class="glass-alert-success">
            <strong>✅ Economics Calculated:</strong> Using """ + st.session_state.scenario + """ scenario with industry-standard assumptions
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### 🔬 Processing Parameters")
        
        # Parameters in glass cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="glass-card">
                <h4 style="text-align: center; color: #5a9367 !important;">🌾 Bio-briquettes</h4>
                <div style="text-align: center; margin: 1rem 0;">
                    <div style="font-size: 2.5rem; font-weight: 900; color: #2d5f3f;">
                        {assumptions['briquette_yield'] * 100:.0f}%
                    </div>
                    <div style="color: #666; margin-top: 0.5rem;">Yield Rate</div>
                </div>
                <div style="text-align: center; margin-top: 1rem;">
                    <div style="font-size: 1.8rem; font-weight: 700; color: #5a9367;">
                        ₹{assumptions['briquette_price']}/kg
                    </div>
                    <div style="color: #666;">Market Price</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="glass-card">
                <h4 style="text-align: center; color: #7db88a !important;">♻️ Bio-char</h4>
                <div style="text-align: center; margin: 1rem 0;">
                    <div style="font-size: 2.5rem; font-weight: 900; color: #2d5f3f;">
                        {assumptions['biochar_yield'] * 100:.0f}%
                    </div>
                    <div style="color: #666; margin-top: 0.5rem;">Yield Rate</div>
                </div>
                <div style="text-align: center; margin-top: 1rem;">
                    <div style="font-size: 1.8rem; font-weight: 700; color: #7db88a;">
                        ₹{assumptions['biochar_price']}/kg
                    </div>
                    <div style="color: #666;">Market Price</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="glass-card">
                <h4 style="text-align: center; color: #2196f3 !important;">💸 Economics</h4>
                <div style="text-align: center; margin: 1rem 0;">
                    <div style="font-size: 2.5rem; font-weight: 900; color: #2d5f3f;">
                        ₹{assumptions['carbon_credit_per_ton']}
                    </div>
                    <div style="color: #666; margin-top: 0.5rem;">Carbon Credit/ton</div>
                </div>
                <div style="text-align: center; margin-top: 1rem;">
                    <div style="font-size: 1.8rem; font-weight: 700; color: #2196f3;">
                        ₹{assumptions['farmer_payment_per_ton']}
                    </div>
                    <div style="color: #666;">Farmer Payment/ton</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Financial Analysis Section
        st.markdown("#### 📊 Financial Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 💰 Revenue Breakdown")
            
            revenue_data = pd.DataFrame({
                'Source': ['Bio-briquettes', 'Bio-char', 'Carbon Credits'],
                'Amount (INR)': [economics['revenue']['briquette'], 
                                economics['revenue']['biochar'], 
                                economics['revenue']['carbon']],
                'Percentage': [
                    economics['revenue']['briquette']/economics['revenue']['total']*100,
                    economics['revenue']['biochar']/economics['revenue']['total']*100,
                    economics['revenue']['carbon']/economics['revenue']['total']*100
                ]
            })
            
            fig_revenue = px.pie(revenue_data, values='Amount (INR)', names='Source', 
                                title=f'Total Revenue: ₹{economics["revenue"]["total"]:,.0f}',
                                color_discrete_sequence=['#5a9367', '#7db88a', '#9bc49f'],
                                hole=0.4)
            fig_revenue.update_traces(textposition='inside', textinfo='percent+label')
            fig_revenue.update_layout(
                showlegend=True,
                height=400,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_revenue, use_container_width=True)
            
            # Revenue details table
            st.dataframe(
                revenue_data.style.format({
                    'Amount (INR)': '₹{:,.0f}',
                    'Percentage': '{:.1f}%'
                }),
                use_container_width=True,
                hide_index=True
            )
        
        with col2:
            st.markdown("##### 💸 Cost Structure")
            
            cost_data = pd.DataFrame({
                'Category': ['Processing', 'Farmer Payment', 'Transport'],
                'Amount (INR)': [economics['cost']['processing'], 
                               economics['cost']['farmer_payment'], 
                               economics['cost']['transport']],
                'Percentage': [
                    economics['cost']['processing']/economics['cost']['total']*100,
                    economics['cost']['farmer_payment']/economics['cost']['total']*100,
                    economics['cost']['transport']/economics['cost']['total']*100
                ]
            })
            
            fig_cost = px.pie(cost_data, values='Amount (INR)', names='Category',
                             title=f'Total Cost: ₹{economics["cost"]["total"]:,.0f}',
                             color_discrete_sequence=['#f44336', '#ff9800', '#ffc107'],
                             hole=0.4)
            fig_cost.update_traces(textposition='inside', textinfo='percent+label')
            fig_cost.update_layout(
                showlegend=True,
                height=400,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_cost, use_container_width=True)
            
            # Cost details table
            st.dataframe(
                cost_data.style.format({
                    'Amount (INR)': '₹{:,.0f}',
                    'Percentage': '{:.1f}%'
                }),
                use_container_width=True,
                hide_index=True
            )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Profitability Metrics
        st.markdown("#### 📈 Profitability Analysis")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-glass-card">
                <div class="metric-label">Gross Profit</div>
                <div class="metric-value">₹{economics['metrics']['profit']/100000:.1f}L</div>
                <div class="metric-label" style="font-size: 0.8rem;">Total earnings</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-glass-card">
                <div class="metric-label">Profit Margin</div>
                <div class="metric-value">{economics['metrics']['margin']:.1f}%</div>
                <div class="metric-label" style="font-size: 0.8rem;">Net margin</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-glass-card">
                <div class="metric-label">Profit per Ton</div>
                <div class="metric-value">₹{economics['metrics']['profit']/total_stubble:,.0f}</div>
                <div class="metric-label" style="font-size: 0.8rem;">Unit economics</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-glass-card">
                <div class="metric-label">Break-even</div>
                <div class="metric-value">{economics['metrics']['breakeven_tons']:.0f}</div>
                <div class="metric-label" style="font-size: 0.8rem;">Tons needed</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Production Summary
        st.markdown("#### 🏭 Production Summary")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 📦 Production Output")
            
            prod_summary = pd.DataFrame({
                'Product': ['Bio-briquettes', 'Bio-char'],
                'Production (kg)': [
                    economics['production']['briquette_kg'],
                    economics['production']['biochar_kg']
                ],
                'Revenue (₹)': [
                    economics['revenue']['briquette'],
                    economics['revenue']['biochar']
                ],
                'Price per kg (₹)': [
                    assumptions['briquette_price'],
                    assumptions['biochar_price']
                ]
            })
            
            st.dataframe(
                prod_summary.style.format({
                    'Production (kg)': '{:,.0f}',
                    'Revenue (₹)': '₹{:,.0f}',
                    'Price per kg (₹)': '₹{:.0f}'
                }),
                use_container_width=True,
                hide_index=True
            )
        
        with col2:
            st.markdown("##### 📊 Key Financial Ratios")
            
            financial_ratios = pd.DataFrame({
                'Ratio': ['Revenue per Ton', 'Cost per Ton', 'Net Profit per Ton', 'ROI'],
                'Value': [
                    f"₹{economics['metrics']['revenue_per_ton']:,.0f}",
                    f"₹{economics['metrics']['cost_per_ton']:,.0f}",
                    f"₹{economics['metrics']['profit']/total_stubble:,.0f}",
                    f"{economics['metrics']['margin']:.1f}%"
                ]
            })
            
            st.dataframe(financial_ratios, use_container_width=True, hide_index=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Profitability Status
        if economics['metrics']['margin'] > 25:
            st.markdown(f"""
            <div class="glass-alert-success">
                <strong>✅ HIGHLY PROFITABLE ({economics['metrics']['margin']:.1f}% margin)</strong><br>
                This operation is financially viable with strong profit margins. The business model is sustainable.
            </div>
            """, unsafe_allow_html=True)
        elif economics['metrics']['margin'] > 15:
            st.markdown(f"""
            <div class="glass-alert-info">
                <strong>📊 MODERATELY PROFITABLE ({economics['metrics']['margin']:.1f}% margin)</strong><br>
                The operation is profitable with acceptable margins. Consider optimization for better returns.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="glass-alert-warning">
                <strong>⚠️ LOW MARGINS ({economics['metrics']['margin']:.1f}%)</strong><br>
                Profit margins are below optimal. Review assumptions and explore cost reduction strategies.
            </div>
            """, unsafe_allow_html=True)
    
    # TAB 5: DASHBOARD
    with tab5:
        st.markdown("### 📊 Executive Dashboard - Complete Overview")
        
        if not st.session_state.processed_data or st.session_state.farmer_data.empty:
            st.markdown("""
            <div class="glass-alert-warning">
                <strong>⚠️ Dashboard Not Ready</strong><br>
                Please complete the previous steps first to view the executive dashboard:
                <ol style="margin-top: 0.5rem;">
                    <li>Add farmer data in <strong>Data Input</strong></li>
                    <li>Generate clusters in <strong>Clustering</strong></li>
                    <li>Return here to view complete analytics</li>
                </ol>
            </div>
            """, unsafe_allow_html=True)
            
            st.info("👈 Use the sidebar to navigate between tabs")
            return
        
        df = st.session_state.processed_data['df']
        cluster_metrics = st.session_state.processed_data['cluster_metrics']
        total_stubble = df['Stubble (tons)'].sum()
        assumptions = SCENARIOS[st.session_state.scenario]
        transport_cost = cluster_metrics['Transport Cost (INR)'].sum()
        
        economics = calculate_unit_economics(total_stubble, assumptions, transport_cost)
        environmental = calculate_environmental_impact(total_stubble, assumptions)
        logistics = calculate_logistics_savings(transport_cost, total_stubble)
        
        # Success banner
        st.markdown("""
        <div class="glass-alert-success">
            <strong>✅ Dashboard Ready:</strong> All calculations complete. Scenario: """ + st.session_state.scenario + """ | 
            Operational Months: """ + str(st.session_state.operational_months) + """/year
        </div>
        """, unsafe_allow_html=True)
        
        # Executive Summary KPIs
        st.markdown("#### 🎯 Executive Summary")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"""
            <div class="metric-glass-card">
                <div class="metric-label">Total Stubble</div>
                <div class="metric-value">{total_stubble:,.0f}t</div>
                <div class="metric-label" style="font-size: 0.8rem;">Processed</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-glass-card">
                <div class="metric-label">Farmers</div>
                <div class="metric-value">{len(df)}</div>
                <div class="metric-label" style="font-size: 0.8rem;">Beneficiaries</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-glass-card">
                <div class="metric-label">Mobile Units</div>
                <div class="metric-value">{len(cluster_metrics)}</div>
                <div class="metric-label" style="font-size: 0.8rem;">Deployed</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-glass-card">
                <div class="metric-label">Net Profit</div>
                <div class="metric-value">₹{economics['metrics']['profit']/100000:.1f}L</div>
                <div class="metric-label" style="font-size: 0.8rem;">{economics['metrics']['margin']:.1f}% margin</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div class="metric-glass-card">
                <div class="metric-label">CO₂ Avoided</div>
                <div class="metric-value">{environmental['co2_avoided']:,.0f}t</div>
                <div class="metric-label" style="font-size: 0.8rem;">Emissions saved</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # MAP VIEW
        st.markdown("## 🗺️ 1. Map View - Clusters & Routes")
        st.caption("Mobile bio-refinery units with optimized collection routes across farmer clusters")
        
        center_lat = df['Latitude'].mean()
        center_lon = df['Longitude'].mean()
        m = folium.Map(location=[center_lat, center_lon], zoom_start=9)
        colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightblue', 'darkgreen']
        
        for idx, row in df.iterrows():
            folium.CircleMarker(
                location=[row['Latitude'], row['Longitude']],
                radius=5 + row['Stubble (tons)'] / 2,
                popup=f"<b>{row['Farmer Name']}</b><br>Village: {row['Village']}<br>Stubble: {row['Stubble (tons)']} tons<br>Cluster: {int(row['Cluster']) + 1}",
                color=colors[int(row['Cluster']) % len(colors)],
                fill=True, fillColor=colors[int(row['Cluster']) % len(colors)],
                fillOpacity=0.7
            ).add_to(m)
        
        for cluster_id in range(len(cluster_metrics)):
            cluster_data = df[df['Cluster'] == cluster_id]
            center_lat = cluster_data['Latitude'].mean()
            center_lon = cluster_data['Longitude'].mean()
            
            folium.Marker(
                location=[center_lat, center_lon],
                popup=f"<b>Mobile Unit {cluster_id + 1}</b><br>Stubble: {cluster_metrics.iloc[cluster_id]['Total Stubble (tons)']} tons<br>Farmers: {cluster_metrics.iloc[cluster_id]['Farmers']}",
                icon=folium.Icon(color=colors[cluster_id % len(colors)], icon='truck', prefix='fa')
            ).add_to(m)
        
        folium_static(m, width=1400, height=500)
        
        col1, col2, col3 = st.columns(3)
        col1.info("🔵 **Circles** = Farmers (size proportional to stubble volume)")
        col2.success("🚛 **Truck icons** = Mobile bio-refinery deployment centers")
        col3.warning(f"📍 **{logistics['reduction_pct']:.0f}% cost reduction** vs centralized processing")
        
        st.markdown("---")
        
        # OPERATIONS PANEL
        st.markdown("## ⚙️ 2. Operations Panel")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"""
            <div class="metric-glass-card">
                <div class="metric-label">Tons Collected</div>
                <div class="metric-value">{total_stubble:,.0f}</div>
                <div class="metric-label" style="font-size: 0.8rem;">Stubble processed</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-glass-card">
                <div class="metric-label">Villages</div>
                <div class="metric-value">{df['Village'].nunique()}</div>
                <div class="metric-label" style="font-size: 0.8rem;">Covered</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-glass-card">
                <div class="metric-label">Units Deployed</div>
                <div class="metric-value">{len(cluster_metrics)}</div>
                <div class="metric-label" style="font-size: 0.8rem;">Mobile refineries</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-glass-card">
                <div class="metric-label">Farmers</div>
                <div class="metric-value">{len(df)}</div>
                <div class="metric-label" style="font-size: 0.8rem;">Enrolled</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div class="metric-glass-card">
                <div class="metric-label">Avg Route</div>
                <div class="metric-value">{cluster_metrics['Avg Distance (km)'].mean():.1f}</div>
                <div class="metric-label" style="font-size: 0.8rem;">Kilometers</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### 📋 Cluster-wise Operations")
        
        ops_display = cluster_metrics.copy()
        ops_display['Unit ID'] = ['Unit-' + str(i+1) for i in ops_display['Cluster']]
        ops_display['Processing Time (hrs)'] = (pd.to_numeric(ops_display['Total Stubble (tons)'], errors='coerce') * assumptions['processing_time_per_ton']).round(1)
        ops_display = ops_display[['Unit ID', 'Villages', 'Farmers', 'Total Stubble (tons)', 'Avg Distance (km)', 'Processing Time (hrs)']]
        
        st.dataframe(
            ops_display.style.format({
                'Total Stubble (tons)': '{:.0f}',
                'Avg Distance (km)': '{:.1f}',
                'Processing Time (hrs)': '{:.1f}'
            }),
            use_container_width=True,
            hide_index=True
        )
        
        st.markdown("---")
        
        # ECONOMICS PANEL
        st.markdown("## 💰 3. Economics Panel")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="metric-glass-card">
                <div class="metric-label">Cost per Ton</div>
                <div class="metric-value">₹{economics['metrics']['cost_per_ton']:,.0f}</div>
                <div class="metric-label" style="font-size: 0.8rem;">Processing + Transport</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-glass-card">
                <div class="metric-label">Revenue per Ton</div>
                <div class="metric-value">₹{economics['metrics']['revenue_per_ton']:,.0f}</div>
                <div class="metric-label" style="font-size: 0.8rem;">+₹{economics['metrics']['revenue_per_ton'] - economics['metrics']['cost_per_ton']:,.0f} profit</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-glass-card">
                <div class="metric-label">Profit Margin</div>
                <div class="metric-value">{economics['metrics']['margin']:.1f}%</div>
                <div class="metric-label" style="font-size: 0.8rem;">₹{economics['metrics']['profit']:,.0f} total</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 💰 Revenue Streams")
            revenue_df = pd.DataFrame({
                'Source': ['Bio-briquettes', 'Bio-char', 'Carbon Credits'],
                'Amount': [economics['revenue']['briquette'], 
                          economics['revenue']['biochar'], 
                          economics['revenue']['carbon']],
                'Percentage': [
                    economics['revenue']['briquette']/economics['revenue']['total']*100,
                    economics['revenue']['biochar']/economics['revenue']['total']*100,
                    economics['revenue']['carbon']/economics['revenue']['total']*100
                ]
            })
            fig_rev = px.pie(revenue_df, values='Amount', names='Source',
                            title=f'Total Revenue: ₹{economics["revenue"]["total"]:,.0f}',
                            color_discrete_sequence=['#5a9367', '#7db88a', '#9bc49f'],
                            hole=0.4)
            fig_rev.update_traces(textposition='inside', textinfo='percent+label')
            fig_rev.update_layout(showlegend=True, height=350, paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_rev, use_container_width=True)
        
        with col2:
            st.markdown("##### 💸 Cost Breakdown")
            cost_df = pd.DataFrame({
                'Category': ['Processing', 'Farmer Payment', 'Transport'],
                'Amount': [economics['cost']['processing'], 
                          economics['cost']['farmer_payment'], 
                          economics['cost']['transport']],
                'Percentage': [
                    economics['cost']['processing']/economics['cost']['total']*100,
                    economics['cost']['farmer_payment']/economics['cost']['total']*100,
                    economics['cost']['transport']/economics['cost']['total']*100
                ]
            })
            fig_cost = px.pie(cost_df, values='Amount', names='Category',
                             title=f'Total Cost: ₹{economics["cost"]["total"]:,.0f}',
                             color_discrete_sequence=['#f44336', '#ff9800', '#ffc107'],
                             hole=0.4)
            fig_cost.update_traces(textposition='inside', textinfo='percent+label')
            fig_cost.update_layout(showlegend=True, height=350, paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_cost, use_container_width=True)
        
        st.markdown("---")
        
        # IMPACT PANEL
        st.markdown("## 🌍 4. Impact Panel - Environmental & Social")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="metric-glass-card">
                <div class="metric-label">Emissions Avoided</div>
                <div class="metric-value">{environmental['co2_avoided']:,.0f}t</div>
                <div class="metric-label" style="font-size: 0.8rem;">CO₂ prevented</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-glass-card">
                <div class="metric-label">Farmer Income</div>
                <div class="metric-value">₹{economics['cost']['farmer_payment']/100000:.2f}L</div>
                <div class="metric-label" style="font-size: 0.8rem;">₹{economics['cost']['farmer_payment']/len(df):,.0f} per farmer</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-glass-card">
                <div class="metric-label">Coal Replaced</div>
                <div class="metric-value">{environmental['coal_replaced']:,.0f}t</div>
                <div class="metric-label" style="font-size: 0.8rem;">Clean energy</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### 👨‍🌾 Farmer Income Distribution")
        st.caption("Top 10 farmers by income - demonstrating direct financial benefit vs. ₹0 from traditional burning")
        
        farmer_income_df = df.copy()
        farmer_income_df['Income (INR)'] = farmer_income_df['Stubble (tons)'] * assumptions['farmer_payment_per_ton']
        farmer_income_df = farmer_income_df.sort_values('Income (INR)', ascending=False).head(10)
        
        fig_income = px.bar(
            farmer_income_df, 
            x='Farmer Name', 
            y='Income (INR)',
            title='Top 10 Farmers by Income Generation',
            color='Income (INR)', 
            color_continuous_scale='Greens',
            labels={'Income (INR)': 'Income (₹)'}
        )
        fig_income.update_layout(
            showlegend=False,
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig_income, use_container_width=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="glass-card">
                <h5 style="color: #5a9367 !important;">🌍 Environmental Wins</h5>
                <ul style="color: #666; line-height: 2;">
                    <li>🌳 <strong>""" + f"{environmental['trees_equivalent']:,}" + """ trees equivalent</strong> planted</li>
                    <li>🚗 <strong>""" + f"{environmental['cars_equivalent']:,}" + """ cars</strong> off road for 1 year</li>
                    <li>🏠 Powers <strong>""" + f"{environmental['homes_powered']:,}" + """ homes</strong> for a year</li>
                    <li>☀️ <strong>100% renewable</strong> energy source</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="glass-card">
                <h5 style="color: #2196f3 !important;">👥 Social Impact</h5>
                <ul style="color: #666; line-height: 2;">
                    <li>👨‍🌾 <strong>""" + f"{len(df)}" + """ farmers</strong> earning income</li>
                    <li>🏘️ <strong>""" + f"{df['Village'].nunique()}" + """ villages</strong> benefiting</li>
                    <li>💼 <strong>""" + f"{len(cluster_metrics) * 5}" + """ jobs</strong> created (operators + support)</li>
                    <li>🌾 <strong>Zero waste</strong> agricultural model</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # SUMMARY & EXPORT
        st.markdown("## 📋 Executive Summary & Reports")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="glass-card">
                <h5 style="color: #5a9367 !important;">🎯 Key Achievements</h5>
                <ul style="color: #666; line-height: 1.8;">
                    <li>✅ <strong>""" + f"{total_stubble:.0f}" + """t</strong> stubble processed</li>
                    <li>✅ <strong>₹""" + f"{economics['metrics']['profit']/100000:.2f}" + """L</strong> profit generated</li>
                    <li>✅ <strong>""" + f"{economics['metrics']['margin']:.1f}" + """%</strong> profit margin</li>
                    <li>✅ <strong>""" + f"{logistics['reduction_pct']:.0f}" + """%</strong> logistics saved</li>
                    <li>✅ <strong>""" + f"{environmental['co2_avoided']:.0f}" + """t</strong> CO₂ avoided</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            pilot_summary = pd.DataFrame({
                'Metric': ['Stubble Processed', 'Total Revenue', 'Total Cost', 'Net Profit', 'Farmers Enrolled', 'CO₂ Avoided'],
                'Value': [
                    f"{total_stubble:.0f} tons",
                    f"₹{economics['revenue']['total']:,.0f}",
                    f"₹{economics['cost']['total']:,.0f}",
                    f"₹{economics['metrics']['profit']:,.0f}",
                    len(df),
                    f"{environmental['co2_avoided']:.0f} tons"
                ]
            })
            
            st.markdown("##### 📥 Download Reports")
            
            csv_summary = pilot_summary.to_csv(index=False)
            st.download_button(
                "📑 Pilot Summary (CSV)",
                csv_summary,
                "pilot_summary.csv",
                "text/csv",
                use_container_width=True
            )
            
            farmer_csv = df.to_csv(index=False)
            st.download_button(
                "📄 Farmer Data (CSV)",
                farmer_csv,
                "farmer_data.csv",
                "text/csv",
                use_container_width=True
            )
            
            cluster_csv = cluster_metrics.to_csv(index=False)
            st.download_button(
                "📊 Cluster Report (CSV)",
                cluster_csv,
                "cluster_report.csv",
                "text/csv",
                use_container_width=True
            )
        
        with col3:
            st.markdown("""
            <div class="glass-card">
                <h5 style="color: #2196f3 !important;">📊 Scenario Details</h5>
                <p style="color: #666; margin: 0.5rem 0;"><strong>Current Scenario:</strong> """ + st.session_state.scenario + """</p>
                <ul style="color: #666; line-height: 1.8; margin-top: 1rem;">
                    <li>Briquette yield: <strong>""" + f"{assumptions['briquette_yield']*100:.0f}" + """%</strong></li>
                    <li>Biochar yield: <strong>""" + f"{assumptions['biochar_yield']*100:.0f}" + """%</strong></li>
                    <li>Processing: <strong>₹""" + f"{assumptions['processing_cost_per_ton']}" + """/ton</strong></li>
                    <li>Farmer payment: <strong>₹""" + f"{assumptions['farmer_payment_per_ton']}" + """/ton</strong></li>
                    <li>Operational: <strong>""" + f"{st.session_state.operational_months}" + """ months/year</strong></li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Final status indicator
        if economics['metrics']['margin'] > 25:
            st.markdown(f"""
            <div class="glass-alert-success">
                <strong>✅ EXCELLENT BUSINESS VIABILITY</strong><br>
                The project shows strong profitability ({economics['metrics']['margin']:.1f}% margin) with significant environmental and social impact. 
                This model is highly sustainable and ready for scaling.
            </div>
            """, unsafe_allow_html=True)
        elif economics['metrics']['margin'] > 15:
            st.markdown(f"""
            <div class="glass-alert-info">
                <strong>📊 GOOD BUSINESS VIABILITY</strong><br>
                The project demonstrates solid profitability ({economics['metrics']['margin']:.1f}% margin) with meaningful impact. 
                Consider optimization strategies for enhanced returns.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(
                f"""
                <div class="glass-alert-warning">
                <strong>⚠️ MODERATE VIABILITY</strong><br>
                Margins are at {economics['metrics']['margin']:.1f}%. 
                Review assumptions and explore cost reduction or revenue enhancement strategies.
                </div>""",
                unsafe_allow_html=True
            )
            color_discrete_sequence=['#f44336', '#ff9800', '#ffc107']
            st.plotly_chart(fig_cost, use_container_width=True)
        
        st.markdown("---")
    
    # FOOTER
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="footer">
        <div class="hero-logo" style="font-size: 2.5rem;">🌾</div>
        <h3 style="color: #2d5f3f !important; margin: 1rem 0;">Stubble2Power</h3>
        <p style="font-size: 1.2rem; color: #666; margin-bottom: 1.5rem;">
            Mobile Bio-Refineries Transforming Waste into Clean Energy
        </p>
        <div style="margin: 1.5rem 0;">
            <span class="tech-badge">🚛 Mobile Units</span>
            <span class="tech-badge">♻️ Zero Emission</span>
            <span class="tech-badge">💰 70% Savings</span>
            <span class="tech-badge">🌍 Carbon Negative</span>
        </div>
        <p style="opacity: 0.7; font-size: 0.95rem; margin-top: 2rem;">
            Track: Energy & Sustainability | Ideas for India Innovation Challenge<br>
            Powered by Algorithmic Clustering + Real-time Analytics | © 2025 Stubble2Power
        </p>
        <p style="opacity: 0.6; font-size: 0.85rem; margin-top: 1rem;">
            Version 1.0.0 | Pilot-Ready Prototype
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()