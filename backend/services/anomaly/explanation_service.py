"""
Anomaly Explanation Service.
Generates human-readable, scientifically grounded diagnostic explanations
for detected fire activity anomalies.
"""

from typing import Dict, Any, Optional
from datetime import date


class AnomalyExplanationService:
    @staticmethod
    def generate_explanation(
        observation_date: date,
        grid_id: str,
        region_id: str,
        observed_val: float,
        baseline_val: float,
        metric_name: str,
        z_score: float,
        mad_score: float,
        anomaly_type: str,
        severity_level: str,
        data_sufficiency_status: str,
        co_occurring_count: int = 0
    ) -> Dict[str, Any]:
        """
        Builds a comprehensive diagnostic breakdown for an anomalous fire activity event.
        """
        diff = observed_val - baseline_val
        if baseline_val > 0.0:
            pct_increase = (diff / baseline_val) * 100.0
            pct_str = f"+{pct_increase:.1f}%"
        else:
            pct_increase = 0.0
            pct_str = "new emergence over zero baseline"

        # Construct clear summary narrative
        if anomaly_type == "SPIKE":
            summary = (
                f"Severe fire activity spike detected in {grid_id} ({region_id}) on {observation_date.isoformat()}. "
                f"Observed {metric_name} of {observed_val:.1f} exceeds historical median {baseline_val:.1f} by {diff:.1f} ({pct_str})."
            )
        elif anomaly_type == "UNSEASONAL_TIMING":
            summary = (
                f"Unseasonal fire activity detected on {observation_date.isoformat()} outside expected seasonal burn window. "
                f"Recorded {observed_val:.1f} against near-zero baseline expectation of {baseline_val:.1f}."
            )
        elif anomaly_type == "PROLONGED_ELEVATION":
            summary = (
                f"Prolonged elevated fire activity across multiple days in {grid_id}. "
                f"Sustained level {observed_val:.1f} vs expected norm {baseline_val:.1f}."
            )
        elif anomaly_type == "SPATIAL_CLUSTER":
            summary = (
                f"High-density spatial fire cluster detected in {grid_id} with {co_occurring_count} adjacent active cells, "
                f"exceeding normal dispersed burning patterns."
            )
        else:
            summary = (
                f"Anomalous fire activity level {observed_val:.1f} in {grid_id} on {observation_date.isoformat()}, "
                f"deviating significantly from historical baseline."
            )

        statistical_evidence = (
            f"Parametric Z-Score: {z_score:+.2f} standard deviations. "
            f"Non-parametric MAD multiplier: {mad_score:+.2f} MADs. "
            f"Classification severity: {severity_level}."
        )

        spatial_context = (
            f"Grid cell {grid_id} in {region_id}. "
            + (f"Co-occurring with {co_occurring_count} neighboring active cells." if co_occurring_count > 0 else "Isolated cell event.")
        )

        if data_sufficiency_status == "SUFFICIENT":
            data_sufficiency_reason = "High confidence: Multi-year baseline has >= 60% observation coverage with verified dual-sensor overpasses."
        elif data_sufficiency_status == "LIMITED_HISTORY":
            data_sufficiency_reason = "Moderate confidence: Baseline computed with limited multi-year historical depth (< 3 seasons)."
        else:
            data_sufficiency_reason = "Cautious interpretation: Satellite overpass coverage was limited or partially cloud-impacted."

        return {
            "summary": summary,
            "metric_observed": round(observed_val, 2),
            "baseline_expected": round(baseline_val, 2),
            "deviation_absolute": round(diff, 2),
            "deviation_percent": round(pct_increase, 1),
            "z_score": round(z_score, 2),
            "mad_score": round(mad_score, 2),
            "statistical_evidence": statistical_evidence,
            "spatial_context": spatial_context,
            "data_sufficiency_reason": data_sufficiency_reason,
            "severity_level": severity_level,
            "anomaly_type": anomaly_type
        }
