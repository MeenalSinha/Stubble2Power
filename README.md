# 🌾 Stubble2Power

**Mobile Bio-Refineries Transforming Agricultural Waste into Clean Energy**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Important Disclaimer](#important-disclaimer)
- [The Problem](#the-problem)
- [Our Solution](#our-solution)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Business Model](#business-model)
- [Impact Metrics](#impact-metrics)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## 🎯 Overview

**Stubble2Power** is a pilot planning and simulation platform designed to evaluate the feasibility of mobile bio-refineries for agricultural waste management in India. By modeling the deployment of mobile processing units directly to farms, this tool helps assess the potential to eliminate stubble burning while creating economic value for farmers.

This application provides simulation tools for:
- **Cluster-based route cost estimation** using K-Means algorithms
- **Economic modeling** with multiple scenario planning
- **Environmental impact** estimation and tracking
- **Farmer enrollment** simulation and data management
- **Analytics dashboards** for feasibility assessment

**Track:** Energy & Sustainability  
**Challenge:** Ideas for India Innovation Challenge  
**Version:** 1.0.0 (Pilot Planning Prototype)

---

## ⚠️ Important Disclaimer

> **This repository contains a pilot planning and simulation prototype.**
> 
> All economic, environmental, and impact metrics presented are **model-based estimates** derived from standard industry assumptions and academic research benchmarks. The platform is intended for **feasibility validation and pilot design**, not production deployment.
>
> - Financial projections are simulations, not guarantees
> - Environmental impact figures are theoretical calculations
> - Processing yields are based on literature values
> - Market prices reflect current estimates and may vary
>
> **This tool should be used for planning and discussion purposes only.**

---

## 🔥 The Problem

India faces a severe agricultural waste crisis:

- **23 million tons** of stubble burned annually
- **₹20 billion** in estimated economic and health damages
- **AQI levels** reaching 400+ during harvest season
- **Zero income** for farmers from stubble disposal
- **Massive CO₂ emissions** contributing to climate change

Traditional centralized processing plants face high logistics costs and are impractical for widespread adoption.

---

## 💡 Our Solution Concept

**Mobile Bio-Refineries** that visit farmers' fields to process stubble on-site:

### Theoretical Advantages

| Feature | Modeled Benefit |
|---------|---------|
| 🚛 **Mobile Units** | ~70% modeled reduction in logistics costs vs. central plants (base-case assumptions) |
| ⚡ **Fast Processing** | Projected 2 hours per ton on-site conversion |
| 💰 **Direct Payment** | Simulated ₹1,500 per ton payment to farmers |
| ♻️ **Full Utilization** | Designed to utilize the full stubble stream without burning |
| 🌍 **Carbon Negative** | Calculated emissions prevention and carbon credit potential |

### Planned Products

1. **Bio-briquettes** (60-75% modeled yield) - Clean fuel alternative to coal
2. **Bio-char** (15-22% modeled yield) - Soil amendment and carbon sequestration
3. **Carbon Credits** - Potential additional revenue from emission reduction

---

## ✨ Key Features

### 🗺️ Cluster-Based Route Cost Estimation (K-Means)
- K-Means clustering algorithm for optimal mobile unit deployment simulation
- Distance-based logistics cost estimation
- Interactive map visualization using Folium

### 📊 Economic Simulation
- Three scenario models: Conservative, Base Case, Optimistic
- Real-time profitability calculations based on input assumptions
- Revenue and cost breakdown analysis
- Break-even analysis

### 🌍 Environmental Impact Modeling
- CO₂ emissions avoided estimation (based on combustion prevention formulas)
- Coal replacement metrics
- Equivalency calculations (trees, cars, homes)
- Standard emission factor methodology

### 👨‍🌾 Farmer Management Simulation
- Farmer registration interface
- Sample data generation for testing
- Income distribution modeling
- Coverage area analytics

### 📈 Executive Dashboard
- Comprehensive overview of simulated metrics
- Interactive charts and visualizations (Plotly)
- Exportable reports (CSV format)
- Scenario comparison views

---

## 🛠️ Technology Stack

### Core Technologies
- **Python 3.8+** - Backend logic and calculations
- **Streamlit** - Web application framework
- **Pandas** - Data manipulation and analysis
- **NumPy** - Numerical computations

### Algorithms & Visualization
- **Scikit-learn** - K-Means clustering for route optimization
- **Plotly** - Interactive charts and graphs
- **Folium** - Interactive mapping with OpenStreetMap

### UI/UX
- **Custom CSS** - Glassmorphism design theme
- **Responsive Layout** - Wide-screen optimized interface
- **Animation CSS** - Enhanced user experience

---

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

### Step-by-Step Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/stubble2power.git
cd stubble2power
```

2. **Create virtual environment** (recommended)
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the application**
```bash
streamlit run app.py
```

5. **Access the application**
Open your browser and navigate to:
```
http://localhost:8501
```

---

## 📖 Usage

### Quick Start Guide

#### 1. Data Input (Tab 2)
- Click **"Add 20 Sample Farmers"** for instant demo data
- Or manually register simulated farmers with their details
- View registered data in the database table

#### 2. Generate Clusters (Tab 3)
- Select number of mobile units (2-8) to simulate
- Click **"Generate Clusters"**
- View clustered deployment on interactive map
- Review estimated logistics cost savings based on cluster distances

#### 3. View Economics (Tab 4)
- Automatic calculation based on clustering results
- Review simulated revenue and cost breakdowns
- Analyze modeled profitability metrics
- Check break-even analysis

#### 4. Executive Dashboard (Tab 5)
- Comprehensive overview of all simulated metrics
- Interactive visualizations
- Export simulation results as CSV
- Compare scenarios

### Configuration Options

**Sidebar Settings:**
- **Scenario Selection:** Conservative / Base Case / Optimistic
- **Operational Months:** 3-12 months per year (for annualization)
- **Quick Stats:** Live calculation display

### Scenario Assumptions Comparison

| Parameter | Conservative | Base Case | Optimistic |
|-----------|-------------|-----------|------------|
| Briquette Yield | 60% | 70% | 75% |
| Biochar Yield | 15% | 20% | 22% |
| Processing Cost | ₹1,000/ton | ₹800/ton | ₹700/ton |
| Briquette Price | ₹5/kg | ₹6/kg | ₹7/kg |
| Carbon Credit | ₹400/ton | ₹500/ton | ₹600/ton |
| Farmer Payment | ₹1,200/ton | ₹1,500/ton | ₹1,800/ton |

*All values are estimates based on literature review and industry benchmarks*

---

## 📁 Project Structure

```
stubble2power/
│
├── app.py                  # Main application file
├── requirements.txt        # Python dependencies
├── README.md              # Project documentation
│
├── .streamlit/            # Streamlit configuration (optional)
│   └── config.toml
│
└── assets/                # Images and resources (if any)
    └── logo.png
```

### Key Components in app.py

```python
# Configuration
SCENARIOS = {...}          # Economic scenario assumptions
SAMPLE_VILLAGES = {...}    # Punjab village coordinates for demo

# Calculation Functions
calculate_unit_economics()      # Revenue & cost modeling
calculate_environmental_impact() # CO₂ and environmental estimates
calculate_logistics_savings()    # Transport cost comparison

# UI Components
main()                     # Main application flow
- Home Tab                 # Landing page with overview
- Data Input Tab          # Farmer registration simulation
- Clustering Tab          # Cluster-based route cost estimation (K-Means)
- Economics Tab           # Financial analysis simulation
- Dashboard Tab           # Executive overview
```

---

## 💼 Modeled Business Economics (Base Case Scenario)

### Simulated Revenue Streams

1. **Bio-briquette Sales**
   - Estimated market pricing for clean fuel
   - Industrial and residential market potential
   - Projected 40-50% of total revenue

2. **Bio-char Sales**
   - Soil amendment market opportunity
   - Carbon sequestration potential
   - Projected 25-35% of total revenue

3. **Carbon Credits**
   - Emission reduction certificate potential
   - International carbon market pricing
   - Projected 15-25% of total revenue

### Modeled Cost Structure

1. **Processing Costs** (40-50%)
   - Equipment operation estimates
   - Maintenance and repairs
   - Energy and consumables

2. **Farmer Payments** (35-45%)
   - Stubble purchase incentive
   - Direct payment model

3. **Transport Costs** (10-15%)
   - Mobile unit movement
   - Significantly lower than central plant model

### Simulated Unit Economics (Base Case)

```
Estimated Revenue per ton:     ₹6,420
Estimated Cost per ton:        ₹4,450
Projected Profit per ton:      ₹1,970
Modeled Margin:               30.7%
```

*These figures are simulation outputs based on assumed parameters and should be validated with pilot operations*

---

## 🌍 Modeled Impact Estimates (Pilot Scale)

> **Note:** All impact figures below are simulation-based estimates using standard emission factors and conversion ratios from environmental literature.

### Estimated Environmental Impact

**Per 100 tons of stubble processed (theoretical):**
- **~150 tons CO₂** emissions potentially avoided (based on combustion prevention)
- **~80 tons coal** potentially replaced with clean energy

### Illustrative Equivalency Metrics (for interpretability)

The above emissions savings translate to commonly understood comparisons:
- **~4,950 trees** planted equivalency (using standard CO₂ absorption rates)
- **~33 cars** off road for one year equivalency
- **~160 homes** potentially powered for one year (energy content basis)

*These equivalencies use EPA and IPCC standard conversion factors*

### Projected Social Impact

- **Estimated farmer income:** ₹1,500 per ton (vs. ₹0 from burning) in Base Case
- **Potential job creation:** ~5 jobs per mobile unit (operators + support)
- **Village coverage:** Designed for remote farming community access
- **Health benefits:** Modeled reduction in air pollution and respiratory issues

### Estimated Economic Impact

- **Logistics savings:** ~70% modeled reduction vs. centralized processing (base-case assumptions)
- **Processing speed:** Projected 3x faster than traditional methods
- **Farmer adoption:** Direct payment incentive model
- **Scalability:** Mobile approach enables distributed deployment

*All metrics require real-world validation through pilot operations*

---

## 🤝 Contributing

We welcome contributions to improve this simulation platform! Here's how you can help:

### Contribution Areas

1. **Algorithm Improvements**
   - Optimize clustering algorithms
   - Add new optimization features
   - Improve calculation accuracy

2. **Documentation**
   - Enhance README
   - Add technical documentation
   - Create user guides

3. **Features**
   - Weather data integration
   - Advanced analytics
   - Additional visualization options

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/ImprovementName`)
3. Commit your changes (`git commit -m 'Add specific improvement'`)
4. Push to the branch (`git push origin feature/ImprovementName`)
5. Open a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Add docstrings to functions
- Include comments for complex calculations
- Test thoroughly before submitting

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Team

**Stubble2Power Team**
- Track: Energy & Sustainability
- Challenge: Ideas for India Innovation Challenge

---

## 📞 Contact

For questions, suggestions, or collaboration opportunities:

- **Email:** stubble2power@example.com
- **GitHub:** [@stubble2power](https://github.com/stubble2power)

---

## 🙏 Acknowledgments

- **Ideas for India** - Innovation Challenge platform
- **Punjab Farmers** - Inspiration and problem validation
- **Open Source Community** - Streamlit, Plotly, Folium, Scikit-learn
- **Academic Research** - Emission factors and yield assumptions from published literature

---

## 🔮 Development Roadmap

### Phase 1 (Current - Completed)
- ✅ Pilot planning and simulation platform
- ✅ K-Means clustering for route optimization
- ✅ Economic modeling with multiple scenarios
- ✅ Interactive dashboard and reporting

### Phase 2 (Planned - Pilot Validation)
- 🔄 Ground-truth validation with field trials
- 🔄 Real-world data collection from test deployments
- 🔄 Refine assumptions based on actual operations
- 🔄 Mobile app prototype for farmer registration

### Phase 3 (Planned - 6-12 months)
- 📋 GPS tracking integration for mobile units
- 📋 Data-driven demand forecasting
- 📋 Payment system integration
- 📋 Weather data integration for harvest timing

### Phase 4 (Long-term Vision)
- 📋 Regional scaling based on pilot results
- 📋 Advanced processing technology integration
- 📋 Partnership development with government agencies
- 📋 Expansion to additional agricultural waste streams

---

## 📊 System Requirements

### Minimum Requirements
- **OS:** Windows 10, macOS 10.14+, Linux (Ubuntu 18.04+)
- **RAM:** 4 GB
- **Storage:** 500 MB free space
- **Browser:** Chrome 90+, Firefox 88+, Safari 14+

### Recommended Requirements
- **OS:** Windows 11, macOS 12+, Linux (Ubuntu 22.04+)
- **RAM:** 8 GB or more
- **Storage:** 1 GB free space
- **Browser:** Latest version of Chrome, Firefox, or Safari

---

## 🐛 Known Limitations

- Map rendering may be slow with 50+ data points
- CSV export tested with datasets under 1000 rows
- All calculations are estimates requiring validation
- Mobile responsive design optimized for tablets and above
- Clustering algorithm assumes Euclidean distance (geographic simplification)

For bug reports or feature requests, please open an issue on GitHub.

---

## 📝 Changelog

### Version 1.0.0 (Current)
- Initial release of simulation platform
- Complete pilot planning interface
- K-Means clustering implementation
- Economic simulation with 3 scenarios
- Environmental impact estimation
- Executive dashboard with CSV export capability

---

## 📚 References & Assumptions

This simulation is built on assumptions derived from:

1. **Biomass Processing Literature**
   - Yield rates from peer-reviewed agricultural engineering papers
   - Standard conversion efficiencies for pyrolysis processes

2. **Market Research**
   - Bio-briquette pricing from Indian renewable energy markets
   - Carbon credit valuations from international registries

3. **Transportation Economics**
   - Cost per km estimates from logistics industry standards
   - Distance calculations using geographic coordinates

4. **Environmental Factors**
   - CO₂ emission factors from IPCC guidelines
   - Combustion prevention calculations from EPA methodologies

**For academic or investment decisions, independent validation is strongly recommended.**

---

## ⭐ Support This Project

If you find this simulation tool useful for planning or research, please consider:
- Giving it a star on GitHub
- Sharing with others in the sustainability space
- Contributing improvements or feedback
- Citing in your research or reports

---

**Made with 💚 for Evidence-Based Sustainability Planning**

*A simulation tool for evaluating mobile bio-refinery deployment strategies*
