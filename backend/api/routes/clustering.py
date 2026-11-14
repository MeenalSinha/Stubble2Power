"""
Clustering and Mobile Logistics API Endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.models.database import get_db
from backend.services.farmers.service import FarmerService
from backend.services.clustering.service import ClusteringService
from backend.schemas.clustering import ClusteringResult
from backend.core.exceptions.base import ValidationError

router = APIRouter(prefix="/clustering", tags=["Logistics & Clustering"])


@router.post("/run", response_model=ClusteringResult)
def run_clustering(
    n_clusters: int = Query(4, ge=1, le=20), scenario: str = Query("Base Case"), db: Session = Depends(get_db)
):
    """Executes K-Means grouping and mobile refinery route optimization."""
    try:
        farmer_svc = FarmerService(db)
        df = farmer_svc.get_farmer_dataframe()
        if df.empty:
            raise HTTPException(status_code=400, detail="No registered farmers available for clustering.")

        result = ClusteringService.generate_clusters(farmers_df=df, n_clusters=n_clusters, scenario_name=scenario)
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
