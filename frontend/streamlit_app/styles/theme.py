"""
Glassmorphism and modern UI styles for Stubble2Power Streamlit frontend.
"""

GLASSMORPHISM_CSS = """
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
        background: rgba(163, 201, 168, 0.35);
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(255, 255, 255, 0.4);
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
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(15px);
        border-radius: 18px;
        padding: 1.8rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.5);
        transition: all 0.3s ease;
        margin-bottom: 1rem;
    }
    
    .glass-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 35px rgba(0, 0, 0, 0.12);
    }
    
    /* Hero section */
    .hero-section {
        background: linear-gradient(135deg, rgba(163, 201, 168, 0.8), rgba(138, 180, 145, 0.8));
        backdrop-filter: blur(20px);
        border-radius: 25px;
        padding: 2.5rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.4);
        margin-bottom: 2rem;
    }
    
    .hero-logo {
        font-size: 3.5rem;
    }
    
    .hero-title {
        color: white !important;
        font-size: 3.2rem;
        font-weight: 900;
        margin: 0.5rem 0;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    .hero-subtitle {
        color: white;
        font-size: 1.3rem;
        font-weight: 400;
        opacity: 0.95;
    }

    .tech-badge {
        display: inline-block;
        background: rgba(255, 255, 255, 0.3);
        padding: 0.4rem 1rem;
        border-radius: 20px;
        margin: 0.2rem;
        font-weight: 600;
        color: #1e462d;
        border: 1px solid rgba(255, 255, 255, 0.4);
    }
    
    /* Metric cards */
    .metric-glass-card {
        background: linear-gradient(135deg, rgba(163, 201, 168, 0.8), rgba(138, 180, 145, 0.8));
        backdrop-filter: blur(15px);
        padding: 1.5rem;
        border-radius: 18px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.4);
        transition: all 0.3s ease;
        margin-bottom: 0.8rem;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 900;
        margin: 0.3rem 0;
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.15);
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.95;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Alerts */
    .glass-alert-success {
        background: rgba(212, 241, 221, 0.85);
        backdrop-filter: blur(10px);
        border-left: 5px solid #5a9367;
        padding: 1.2rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(90, 147, 103, 0.15);
    }
    
    .glass-alert-warning {
        background: rgba(255, 243, 205, 0.85);
        backdrop-filter: blur(10px);
        border-left: 5px solid #f9c74f;
        padding: 1.2rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(249, 199, 79, 0.15);
    }

    .glass-alert-info {
        background: rgba(227, 242, 253, 0.85);
        backdrop-filter: blur(10px);
        border-left: 5px solid #2196f3;
        padding: 1.2rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(33, 150, 243, 0.15);
    }

    .footer {
        text-align: center;
        padding: 2.5rem;
        background: rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.4);
        margin-top: 3rem;
    }
</style>
"""
