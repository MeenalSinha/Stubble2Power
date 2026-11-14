# Crop Calendar & Harvest Window Methodology

## 1. Scientific Basis
Agricultural stubble burning in Northwestern India is driven by the tight agronomic turnaround window between Kharif (monsoon) rice harvesting and Rabi (winter) wheat sowing:
- **Paddy Maturation**: Mid-October to late November.
- **Wheat Sowing Window**: Optimal germination requires seeding between October 25 and November 15.
- **Turnaround Window**: Farmers face a 10 to 18-day turnaround to clear high-volume non-basmati paddy residue (averaging 5.5 to 7.0 tonnes per hectare).

---

## 2. Temporal Attribution Windows

The platform models three distinct temporal zones for each crop:
1. **Peak Burn Window ($W_{\text{peak}}$)**:
   - Defined by historical peak harvesting reports from PAU and satellite fire density maxima.
   - Example (Punjab Kharif Paddy): **October 15 to November 20**.
2. **Extended Harvest Season ($W_{\text{ext}}$)**:
   - Accounts for variable sowing dates, variety maturation spans (early PR-126 vs late Pusa-44), and late-season field drying.
   - Includes official buffer of $\pm 10$ days around the standard harvest interval.
   - Example: **September 20 to December 10**.
3. **Off-Season**:
   - Dates outside active crop harvesting. A satellite hotspot occurring during this period is classified as `OTHER_LAND_USE_CONTEXT` or `UNKNOWN_OR_INSUFFICIENT_EVIDENCE`.

---

## 3. Handling Multi-Year and Cross-Year Schedules
Certain agricultural crops (e.g. Autumn-planted Sugarcane) span across calendar years (December to February):
$$\text{If } M_{\text{end}} < M_{\text{start}}, \quad \text{Observation in Month } M \le M_{\text{end}} \implies \text{Window Start in Year } (Y - 1)$$
This algorithm prevents calendar discontinuity errors across annual boundary rollovers.
