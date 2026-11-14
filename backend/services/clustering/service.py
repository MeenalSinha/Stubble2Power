"""
Farmer Clustering and Mobile Bio-Refinery Route Optimization Service.
Replaces planar degree-multiplication with geodesic Haversine distance.
"""

from typing import List, Dict, Optional
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from backend.services.geospatial.service import GeospatialService
from backend.services.economics.service import EconomicsService
from backend.core.config.settings import config_manager
from backend.core.exceptions.base import ValidationError
from backend.schemas.clustering import (
    ClusteringResult,
    ClusterMetricItem,
    ClusterPoint
)


class ClusteringService:
    @staticmethod
    def generate_clusters(
        farmers_df: pd.DataFrame,
        n_clusters: int = 4,
        scenario_name: str = "Base Case",
        assumptions: Optional[Dict[str, float]] = None
    ) -> ClusteringResult:
        """
        Executes spatial K-Means clustering on farmer coordinates and calculates
        mobile refinery transit logistics with geodesic distance metrics.
        """
        if farmers_df.empty:
            raise ValidationError("Cannot perform clustering on an empty farmer dataset.")

        if assumptions is None:
            assumptions = config_manager.get_scenario_assumptions(scenario_name)

        df = farmers_df.copy()
        total_farmers = len(df)
        n_clusters = max(1, min(n_clusters, total_farmers))

        required_cols = {'Farmer Name', 'Village', 'District', 'Latitude', 'Longitude', 'Stubble (tons)'}
        missing = required_cols - set(df.columns)
        if missing:
            raise ValidationError(f"Missing required columns for clustering: {missing}")

        coords = df[['Latitude', 'Longitude']].values.astype(float)

        # Standard K-Means grouping
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        df['Cluster'] = kmeans.fit_predict(coords)

        transit_cost_per_km = float(assumptions.get("mobile_unit_cost_per_km", 150.0))
        processing_time_rate = float(assumptions.get("processing_time_per_ton", 2.0))

        cluster_metrics_list: List[ClusterMetricItem] = []
        assigned_points: List[ClusterPoint] = []

        total_stubble_tons = float(df['Stubble (tons)'].sum())
        total_mobile_transport_cost = 0.0

        for c_id in range(n_clusters):
            c_data = df[df['Cluster'] == c_id]
            c_stubble = float(c_data['Stubble (tons)'].sum())
            c_farmers = len(c_data)
            c_villages = int(c_data['Village'].nunique())
            center_lat = float(c_data['Latitude'].mean())
            center_lon = float(c_data['Longitude'].mean())

            # Geodesic pairwise distances within cluster
            coords_c = c_data[['Latitude', 'Longitude']].values
            distances: List[float] = []
            if len(coords_c) > 1:
                for i in range(len(coords_c)):
                    for j in range(i + 1, len(coords_c)):
                        d = GeospatialService.haversine_distance(
                            coords_c[i][0], coords_c[i][1],
                            coords_c[j][0], coords_c[j][1]
                        )
                        distances.append(d)

            avg_dist = float(np.mean(distances)) if distances else 0.0
            c_transport_cost = avg_dist * transit_cost_per_km
            total_mobile_transport_cost += c_transport_cost
            proc_hours = c_stubble * processing_time_rate

            cluster_metrics_list.append(ClusterMetricItem(
                cluster_id=c_id,
                total_stubble_tons=c_stubble,
                farmer_count=c_farmers,
                village_count=c_villages,
                avg_distance_km=avg_dist,
                transport_cost_inr=c_transport_cost,
                center_latitude=center_lat,
                center_longitude=center_lon,
                processing_time_hours=proc_hours
            ))

        for idx, row in df.iterrows():
            assigned_points.append(ClusterPoint(
                id=int(row.get('id', idx)),
                farmer_name=str(row['Farmer Name']),
                village=str(row['Village']),
                district=str(row['District']),
                latitude=float(row['Latitude']),
                longitude=float(row['Longitude']),
                stubble_tons=float(row['Stubble (tons)']),
                cluster=int(row['Cluster'])
            ))

        logistics = EconomicsService.calculate_logistics_savings(
            mobile_cost=total_mobile_transport_cost,
            stubble_tons=total_stubble_tons
        )

        return ClusteringResult(
            scenario=scenario_name,
            n_clusters=n_clusters,
            total_farmers=total_farmers,
            total_stubble_tons=total_stubble_tons,
            total_mobile_transport_cost_inr=total_mobile_transport_cost,
            central_plant_cost_inr=logistics.central_cost,
            logistics_savings_inr=logistics.savings,
            logistics_reduction_pct=logistics.reduction_pct,
            cluster_metrics=cluster_metrics_list,
            assigned_points=assigned_points
        )
