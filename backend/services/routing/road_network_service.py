"""
Road-Network Routing & Transport Modeling Service.
Calculates realistic rural road distances, travel durations, and fuel consumption
using National Rural Infrastructure Development Agency (NRIDA) road network tortuosity factors.
"""

from typing import List, Dict, Any, Tuple
from backend.services.geospatial.service import GeospatialService
from backend.core.config.settings import config_manager
from backend.core.logging.logger import get_logger

logger = get_logger("stubble2power.routing.road")


class RoadNetworkService:
    def __init__(self):
        self.geo_svc = GeospatialService()
        self.tortuosity = float(config_manager.get("refinery.transport.road_tortuosity_factor"))
        self.fuel_rate = float(config_manager.get("refinery.transport.fuel_consumption_liters_per_km"))
        self.avg_rural_speed_kmh = 35.0  # Average tractor-trailer transit speed on rural link roads

    def calculate_road_route(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float
    ) -> Dict[str, Any]:
        """
        Calculates road distance, travel duration, and diesel fuel consumed between two coordinates.
        Never substitutes flat straight-line distance without realistic tortuosity correction.
        """
        geodesic_dist = self.geo_svc.haversine_distance(origin_lat, origin_lon, dest_lat, dest_lon)
        road_distance_km = round(geodesic_dist * self.tortuosity, 2)
        travel_duration_hours = round(road_distance_km / max(10.0, self.avg_rural_speed_kmh), 2)
        fuel_consumed_liters = round(road_distance_km * self.fuel_rate, 2)

        return {
            "geodesic_distance_km": round(geodesic_dist, 2),
            "road_distance_km": road_distance_km,
            "tortuosity_factor": self.tortuosity,
            "travel_duration_hours": travel_duration_hours,
            "fuel_consumed_liters": fuel_consumed_liters,
            "routing_provider": "NRIDA Rural Road Network Model (Calibrated PMGSY Tortuosity Factor)",
            "speed_kmh": self.avg_rural_speed_kmh
        }

    def solve_multi_stop_route(
        self,
        depot_coords: Tuple[float, float],
        stops: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Sequences stops using nearest-neighbor heuristic starting and ending at the depot.
        Returns total road distance, fuel consumed, and sequenced stops.
        """
        if not stops:
            return {
                "total_distance_km": 0.0,
                "total_duration_hours": 0.0,
                "total_fuel_liters": 0.0,
                "sequenced_stops": []
            }

        unvisited = list(stops)
        curr_lat, curr_lon = depot_coords
        sequenced: List[Dict[str, Any]] = []
        total_dist = 0.0
        total_dur = 0.0
        total_fuel = 0.0
        seq = 1

        # Add initial depot stop
        sequenced.append({
            "sequence": seq,
            "stop_name": "Depot Departure",
            "latitude": curr_lat,
            "longitude": curr_lon,
            "action": "DEPOT_START",
            "payload_tons": 0.0,
            "distance_from_prev_km": 0.0
        })

        while unvisited:
            # Find nearest unvisited stop
            best_idx = 0
            best_dist = 999999.0
            for i, st in enumerate(unvisited):
                d = self.geo_svc.haversine_distance(curr_lat, curr_lon, st["latitude"], st["longitude"])
                if d < best_dist:
                    best_dist = d
                    best_idx = i

            next_stop = unvisited.pop(best_idx)
            leg = self.calculate_road_route(curr_lat, curr_lon, next_stop["latitude"], next_stop["longitude"])
            total_dist += leg["road_distance_km"]
            total_dur += leg["travel_duration_hours"]
            total_fuel += leg["fuel_consumed_liters"]

            curr_lat = next_stop["latitude"]
            curr_lon = next_stop["longitude"]
            seq += 1

            sequenced.append({
                "sequence": seq,
                "stop_name": next_stop.get("farm_name", f"Farm #{next_stop.get('farm_id')}"),
                "latitude": curr_lat,
                "longitude": curr_lon,
                "action": "FARM_COLLECTION",
                "payload_tons": next_stop.get("biomass_tons", 0.0),
                "distance_from_prev_km": leg["road_distance_km"]
            })

        # Return to depot
        depot_lat, depot_lon = depot_coords
        return_leg = self.calculate_road_route(curr_lat, curr_lon, depot_lat, depot_lon)
        total_dist += return_leg["road_distance_km"]
        total_dur += return_leg["travel_duration_hours"]
        total_fuel += return_leg["fuel_consumed_liters"]
        seq += 1

        sequenced.append({
            "sequence": seq,
            "stop_name": "Depot Return & Offload",
            "latitude": depot_lat,
            "longitude": depot_lon,
            "action": "DEPOT_END",
            "payload_tons": 0.0,
            "distance_from_prev_km": return_leg["road_distance_km"]
        })

        return {
            "total_distance_km": round(total_dist, 2),
            "total_duration_hours": round(total_dur, 2),
            "total_fuel_liters": round(total_fuel, 2),
            "sequenced_stops": sequenced
        }
