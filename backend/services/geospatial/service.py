"""
Geospatial calculation and normalization service.
Provides geodesic Haversine distance, coordinate validation, and spatial grid generation.
"""

import math
from typing import Tuple, List, Dict, Any, Optional
from backend.core.exceptions.base import ValidationError


class GeospatialService:
    EARTH_RADIUS_KM = 6371.0088

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculates great-circle distance between two geographic coordinates in kilometers.
        Accurate across arbitrary latitudes unlike flat-degree approximations.
        """
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return GeospatialService.EARTH_RADIUS_KM * c

    @staticmethod
    def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Alias for haversine_distance."""
        return GeospatialService.haversine_distance(lat1, lon1, lat2, lon2)

    @staticmethod
    def validate_coordinates(lat: float, lon: float) -> None:
        """Validates that latitude and longitude fall within legal WGS84 ranges."""
        if not (-90.0 <= lat <= 90.0):
            raise ValidationError(
                message=f"Latitude {lat} is out of valid bounds [-90, +90].",
                field="latitude"
            )
        if not (-180.0 <= lon <= 180.0):
            raise ValidationError(
                message=f"Longitude {lon} is out of valid bounds [-180, +180].",
                field="longitude"
            )

    @staticmethod
    def compute_grid_id(lat: float, lon: float, resolution_deg: float) -> str:
        """
        Computes a deterministic spatial grid cell identifier.
        Bins continuous WGS84 coordinates into reproducible discrete cells.
        """
        if resolution_deg <= 0:
            raise ValidationError("Grid resolution must be greater than zero.", field="resolution_deg")
        grid_lat = math.floor(lat / resolution_deg) * resolution_deg
        grid_lon = math.floor(lon / resolution_deg) * resolution_deg
        return f"grid_{grid_lat:.4f}_{grid_lon:.4f}"

    @staticmethod
    def get_grid_cell_center(grid_id: str, resolution_deg: float) -> Tuple[float, float]:
        """Returns the centroid coordinate (lat, lon) for a given grid cell."""
        parts = grid_id.split("_")
        if len(parts) != 3:
            raise ValidationError(f"Malformed grid cell id '{grid_id}'.")
        grid_lat = float(parts[1])
        grid_lon = float(parts[2])
        center_lat = grid_lat + (resolution_deg / 2.0)
        center_lon = grid_lon + (resolution_deg / 2.0)
        return (round(center_lat, 6), round(center_lon, 6))

    @staticmethod
    def point_in_bbox(lat: float, lon: float, bbox: List[float]) -> bool:
        """
        Evaluates whether a point is inside a bounding box [min_lon, min_lat, max_lon, max_lat].
        """
        if len(bbox) != 4:
            raise ValidationError("Bounding box must be [min_lon, min_lat, max_lon, max_lat].")
        min_lon, min_lat, max_lon, max_lat = bbox
        return (min_lat <= lat <= max_lat) and (min_lon <= lon <= max_lon)
