"""
Repository for Farmer and Farm entity data access.
"""

from typing import List, Optional
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from backend.models.entities import Farmer
from backend.schemas.farmer import FarmerCreate, FarmerUpdate
from backend.core.exceptions.base import DataNotFoundError


class FarmerRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, farmer_in: FarmerCreate) -> Farmer:
        farmer = Farmer(
            name=farmer_in.name,
            village=farmer_in.village,
            district=farmer_in.district,
            state=farmer_in.state,
            country=farmer_in.country,
            acres=farmer_in.acres,
            stubble_tons=farmer_in.stubble_tons,
            harvest_date=farmer_in.harvest_date,
            latitude=farmer_in.latitude,
            longitude=farmer_in.longitude
        )
        self.db.add(farmer)
        self.db.commit()
        self.db.refresh(farmer)
        return farmer

    def get_by_id(self, farmer_id: int) -> Optional[Farmer]:
        return self.db.get(Farmer, farmer_id)

    def list_all(
        self,
        district: Optional[str] = None,
        village: Optional[str] = None,
        min_stubble: Optional[float] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[Farmer]:
        stmt = select(Farmer)
        filters = []
        if district:
            filters.append(Farmer.district.ilike(f"%{district}%"))
        if village:
            filters.append(Farmer.village.ilike(f"%{village}%"))
        if min_stubble is not None:
            filters.append(Farmer.stubble_tons >= min_stubble)

        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = stmt.order_by(Farmer.id.desc()).limit(limit).offset(offset)
        return list(self.db.scalars(stmt).all())

    def update(self, farmer_id: int, farmer_in: FarmerUpdate) -> Farmer:
        farmer = self.get_by_id(farmer_id)
        if not farmer:
            raise DataNotFoundError("Farmer", farmer_id)

        update_data = farmer_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(farmer, field, value)

        self.db.commit()
        self.db.refresh(farmer)
        return farmer

    def delete(self, farmer_id: int) -> bool:
        farmer = self.get_by_id(farmer_id)
        if not farmer:
            return False
        self.db.delete(farmer)
        self.db.commit()
        return True

    def count(self) -> int:
        stmt = select(func.count(Farmer.id))
        return self.db.scalar(stmt) or 0

    def total_stubble(self) -> float:
        stmt = select(func.sum(Farmer.stubble_tons))
        return float(self.db.scalar(stmt) or 0.0)

    def to_dataframe(self) -> pd.DataFrame:
        farmers = self.list_all(limit=50000)
        if not farmers:
            return pd.DataFrame(columns=[
                'id', 'Farmer Name', 'Village', 'District', 'State',
                'Acres', 'Stubble (tons)', 'Harvest Date', 'Latitude', 'Longitude'
            ])
        records = [{
            'id': f.id,
            'Farmer Name': f.name,
            'Village': f.village,
            'District': f.district,
            'State': f.state,
            'Acres': f.acres,
            'Stubble (tons)': f.stubble_tons,
            'Harvest Date': f.harvest_date,
            'Latitude': f.latitude,
            'Longitude': f.longitude
        } for f in farmers]
        return pd.DataFrame(records)
