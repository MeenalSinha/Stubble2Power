"""
Farmer and Farm management business service.
Enforces validation, coordinates persistence, and manages import/export operations.
"""

from typing import List, Dict, Any, Optional
import io
import pandas as pd
from datetime import date
from sqlalchemy.orm import Session
from backend.repositories.farmer_repository import FarmerRepository
from backend.schemas.farmer import FarmerCreate, FarmerResponse
from backend.services.geospatial.service import GeospatialService
from backend.core.exceptions.base import ValidationError


class FarmerService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = FarmerRepository(db)

    def register_farmer(self, farmer_in: FarmerCreate) -> FarmerResponse:
        """Validates geographic coordinates and persists a new farmer."""
        GeospatialService.validate_coordinates(farmer_in.latitude, farmer_in.longitude)
        if farmer_in.acres <= 0:
            raise ValidationError("Cultivated acres must be greater than zero.", field="acres")
        if farmer_in.stubble_tons <= 0:
            raise ValidationError("Stubble tonnage must be greater than zero.", field="stubble_tons")

        farmer = self.repo.create(farmer_in)
        return FarmerResponse.model_validate(farmer)

    def list_farmers(
        self,
        district: Optional[str] = None,
        village: Optional[str] = None,
        min_stubble: Optional[float] = None
    ) -> List[FarmerResponse]:
        entities = self.repo.list_all(district=district, village=village, min_stubble=min_stubble)
        return [FarmerResponse.model_validate(f) for f in entities]

    def get_farmer_dataframe(self) -> pd.DataFrame:
        """Returns standard DataFrame for clustering and analytics UI."""
        return self.repo.to_dataframe()

    def get_summary_stats(self) -> Dict[str, Any]:
        count = self.repo.count()
        stubble = self.repo.total_stubble()
        df = self.repo.to_dataframe()
        villages = int(df['Village'].nunique()) if not df.empty else 0
        acres = float(df['Acres'].sum()) if not df.empty else 0.0

        return {
            "total_farmers": count,
            "total_stubble_tons": stubble,
            "total_acres": acres,
            "total_villages": villages
        }

    def import_farmers_csv(self, csv_content: str) -> Dict[str, Any]:
        """Parses and validates CSV input, inserting records idempotently."""
        df = pd.read_csv(io.StringIO(csv_content))
        name_col = next((c for c in df.columns if 'name' in c.lower()), None)
        lat_col = next((c for c in df.columns if 'lat' in c.lower()), None)
        lon_col = next((c for c in df.columns if 'lon' in c.lower() or 'lng' in c.lower()), None)
        stubble_col = next((c for c in df.columns if 'stubble' in c.lower()), None)
        village_col = next((c for c in df.columns if 'village' in c.lower()), None)

        if not all([name_col, lat_col, lon_col, stubble_col]):
            raise ValidationError(
                f"CSV must contain farmer name, latitude, longitude, and stubble columns. Found: {list(df.columns)}"
            )

        imported = 0
        errors = []

        for idx, row in df.iterrows():
            try:
                lat = float(row[lat_col])
                lon = float(row[lon_col])
                GeospatialService.validate_coordinates(lat, lon)
                stubble = float(row[stubble_col])
                if stubble <= 0:
                    continue

                farmer_in = FarmerCreate(
                    name=str(row[name_col]),
                    village=str(row.get(village_col, "Unknown")),
                    district=str(row.get('District', row.get('district', 'Punjab'))),
                    state=str(row.get('State', row.get('state', 'Punjab'))),
                    acres=float(row.get('Acres', row.get('acres', max(1.0, stubble / 2.0)))),
                    stubble_tons=stubble,
                    harvest_date=date.today(),
                    latitude=lat,
                    longitude=lon
                )
                self.repo.create(farmer_in)
                imported += 1
            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")

        return {
            "records_imported": imported,
            "errors_count": len(errors),
            "errors": errors[:10]
        }
