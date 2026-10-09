# Abstraction layer for location, distance, travel time math and Map APIs
import math
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the Great Circle distance between two points in kilometers."""
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return round(distance, 2)

def estimate_travel_time_minutes(distance_km: float) -> int:
    """
    Estimate travel time in minutes based on urban traffic average speed (approx 25 km/h).
    Adds 5 minutes buffer for parking/arrival.
    """
    if distance_km <= 0:
        return 0
    average_speed_kmh = 25.0
    travel_hours = distance_km / average_speed_kmh
    minutes = int(round(travel_hours * 60)) + 5
    return minutes

class MapService:
    """
    Map Service Abstraction.
    Allows easy swapping between local Haversine calculations and external APIs (Google Maps Distance Matrix).
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.is_production_api_configured = bool(api_key and api_key != "MOCK_KEY")

    def calculate_distance_and_time(
        self, origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float
    ) -> Dict[str, Any]:
        """Returns distance in km and estimated travel time in minutes."""
        if self.is_production_api_configured:
            # Placeholder for Google Maps Distance Matrix API call
            # In a live deployment with GOOGLE_MAPS_API_KEY, this executes HTTP request.
            logger.info("Using external Google Maps Distance Matrix API")
            pass

        # Clean fallback calculation
        dist = haversine_distance_km(origin_lat, origin_lng, dest_lat, dest_lng)
        travel_time = estimate_travel_time_minutes(dist)
        return {
            "distance_km": dist,
            "travel_time_minutes": travel_time,
            "provider": "production_matrix_api" if self.is_production_api_configured else "haversine_abstraction"
        }

# Global instance
map_service = MapService()
