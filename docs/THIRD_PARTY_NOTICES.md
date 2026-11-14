# Stubble2Power — Third-Party Notices & Open Source Attributions

**Document ID:** S2P-DOC-TPN-2026-V1  
**Classification:** Licensing & Legal Notices  
**Platform Version:** v2.5.0  

---

## 1. NASA Earth Science Data & FIRMS
Stubble2Power uses active fire detection and thermal anomaly data products provided by the National Aeronautics and Space Administration (NASA) Fire Information for Resource Management System (FIRMS), part of NASA's Earth Observing System Data and Information System (EOSDIS).

- **Data Sources:**
  - MODIS (Moderate Resolution Imaging Spectroradiometer) Collection 6.1 (Terra and Aqua satellites).
  - VIIRS (Visible Infrared Imaging Radiometer Suite) 375m active fire data products (Suomi-NPP, NOAA-20, and NOAA-21 satellites).
- **Terms of Use:** NASA Earth science data is provided openly and freely under the NASA Open Data Policy. Users of NASA FIRMS data must acknowledge NASA EOSDIS in published research and operational systems.
- **Citation:** NASA Fire Information for Resource Management System (FIRMS). NASA Land, Atmosphere Near real-time Capability for EOS (LANCE), Earth Science Data and Information System (EOSDIS), NASA Goddard Space Flight Center, Greenbelt, MD, USA.

---

## 2. OpenStreetMap & Nominatim
Geospatial base maps and rural road coordinate references are derived in part from OpenStreetMap.
- **License:** Open Database License (ODbL) 1.0.
- **Attribution:** © OpenStreetMap contributors. Data is available under the Open Database License. Cartography in base map tiles is licensed under CC-BY-SA 2.0.

---

## 3. PostGIS & PostgreSQL
- **PostgreSQL:** Released under the PostgreSQL License, a liberal Open Source license similar to the BSD or MIT licenses. Copyright © 1996-2026 PostgreSQL Global Development Group.
- **PostGIS:** Spatial database extension for PostgreSQL, licensed under the GNU General Public License version 2 (GPLv2).

---

## 4. Python Open Source Libraries & Frameworks

| Library / Tool | Primary Author / Maintainer | License | Usage Scope |
|:---|:---|:---:|:---|
| **FastAPI** | Sebastián Ramírez (tiangolo) | MIT | High-performance asynchronous REST API framework |
| **Streamlit** | Snowflake Inc. / Streamlit Community | Apache 2.0 | Reactive user interface & analytics dashboard |
| **SQLAlchemy** | Michael Bayer | MIT | Database Object Relational Mapping (ORM) and abstraction |
| **Pydantic** | Samuel Colvin | MIT | Data parsing, validation, and type enforcement |
| **Pytest** | Holger Krekel and pytest development team | MIT | Automated testing framework & test runner |
| **Passlib** | Eli Collins | BSD-3-Clause | Password hashing & PBKDF2/Bcrypt implementation |
| **PyJWT** | José Padilla | MIT | JSON Web Token (JWT) encoding and verification |
| **Cryptography** | The Python Cryptographic Authority | Apache 2.0 / BSD | Cryptographic primitives & SHA-256 engines |
| **NumPy** | NumPy Developers | BSD-3-Clause | Numerical arrays and mathematical operations |
| **SciPy** | SciPy Developers | BSD-3-Clause | Geospatial distance matrices & statistical distributions |
| **Folium** | Rob Story and Folium contributors | MIT | Interactive Leaflet mapping in Python |
| **Uvicorn** | Encode OSS | BSD-3-Clause | ASGI web server for FastAPI |
| **Requests** | Kenneth Reitz and Requests contributors | Apache 2.0 | HTTP client for NASA FIRMS ingestion |
| **AnyIO** | Alex Grönholm | MIT | Asynchronous concurrency abstraction layer |

---

## 5. Agronomic & Environmental Data Sources

- **Punjab Agricultural University (PAU):** Crop residue-to-product ratios, package of practices for Kharif and Rabi agricultural seasons.
- **Intergovernmental Panel on Climate Change (IPCC):** Sixth Assessment Report (AR6 WG1) Global Warming Potential values (GWP100).
- **Ministry of New and Renewable Energy (MNRE), Govt. of India:** National Bioenergy Programme guidelines and biomass densification operational standards.
- **Central Electricity Authority (CEA), Govt. of India:** Thermal power plant coal co-firing guidelines and displacement factors.
