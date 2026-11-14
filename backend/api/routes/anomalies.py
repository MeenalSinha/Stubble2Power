"""
Fire Activity Anomaly Detection API Endpoints.
"""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.models.database import get_db
from backend.models.entities import FireActivityAnomaly
from backend.services.anomaly.detector import StatisticalAnomalyDetector
from backend.schemas.anomaly import (
    AnomalyDetectRequest,
    AnomalyResponse,
    AnomalySummaryResponse
)

router = APIRouter(prefix="/anomalies", tags=["Anomaly Detection"])


@router.get("", response_model=List[AnomalyResponse])
def get_anomalies(
    region_id: Optional[str] = None,
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    severity_level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieves detected fire activity anomalies with optional filtering."""
    detector = StatisticalAnomalyDetector(db)
    return detector.get_anomalies(
        region_id=region_id,
        date_start=date_start,
        date_end=date_end,
        severity_level=severity_level
    )


@router.post("/detect", response_model=AnomalySummaryResponse)
def detect_anomalies(
    payload: AnomalyDetectRequest,
    db: Session = Depends(get_db)
):
    """Runs statistical anomaly detection across harmonized fire observations."""
    detector = StatisticalAnomalyDetector(db)
    anomalies = detector.detect_anomalies(
        date_start=payload.date_start,
        date_end=payload.date_end,
        region_id=payload.region_id,
        zscore_threshold=payload.zscore_threshold,
        mad_threshold=payload.mad_threshold,
        min_frp_mw=payload.min_frp_mw
    )

    severity_counts = {
        "CRITICAL": sum(1 for a in anomalies if a.severity_level == "CRITICAL"),
        "HIGH": sum(1 for a in anomalies if a.severity_level == "HIGH"),
        "MODERATE": sum(1 for a in anomalies if a.severity_level == "MODERATE"),
        "LOW": sum(1 for a in anomalies if a.severity_level == "LOW"),
    }

    type_counts = {}
    for a in anomalies:
        type_counts[a.anomaly_type] = type_counts.get(a.anomaly_type, 0) + 1

    return AnomalySummaryResponse(
        total_anomalies=len(anomalies),
        severity_counts=severity_counts,
        type_counts=type_counts,
        anomalies=[
            AnomalyResponse(
                id=a.id,
                observation_date=a.observation_date,
                grid_id=a.grid_id,
                region_id=a.region_id,
                observed_activity=a.observed_activity,
                baseline_metric=a.baseline_metric,
                baseline_value=a.baseline_value,
                z_score=a.z_score,
                mad_score=a.mad_score,
                ewma_score=a.ewma_score,
                anomaly_type=a.anomaly_type,
                severity_level=a.severity_level,
                data_sufficiency_flag=a.data_sufficiency_flag,
                explanation_json=a.explanation_json,
                centroid_lat=a.centroid_lat,
                centroid_lon=a.centroid_lon,
                created_at=a.created_at
            )
            for a in anomalies
        ]
    )


@router.get("/{anomaly_id}", response_model=AnomalyResponse)
def get_anomaly_detail(
    anomaly_id: int,
    db: Session = Depends(get_db)
):
    """Retrieves deep diagnostic evidence and explanation for an anomaly."""
    anomaly = db.scalars(select(FireActivityAnomaly).where(FireActivityAnomaly.id == anomaly_id)).first()
    if not anomaly:
        raise HTTPException(status_code=404, detail=f"Anomaly with id {anomaly_id} not found.")
    return anomaly
