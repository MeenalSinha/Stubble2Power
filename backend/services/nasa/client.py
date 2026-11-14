"""
NASA FIRMS API Client.
Communicates with NASA FIRMS endpoints with retry, backoff, and secret protection.
Official Documentation: https://firms.modaps.eosdis.nasa.gov/api/
"""

import io
import time
import requests
import pandas as pd
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from backend.core.config.settings import app_settings
from backend.core.exceptions.base import NASAAPIError, ConfigurationError
from backend.core.logging.logger import get_logger

logger = get_logger("stubble2power.nasa.client")


class NASAClient:
    """Client for NASA Fire Information for Resource Management System (FIRMS) API."""

    VALID_SOURCES = {
        "MODIS_NRT": {"instrument": "MODIS", "satellite": "Terra/Aqua", "resolution_m": 1000},
        "MODIS_SP": {"instrument": "MODIS", "satellite": "Terra/Aqua", "resolution_m": 1000},
        "VIIRS_NOAA20_NRT": {"instrument": "VIIRS", "satellite": "NOAA-20", "resolution_m": 375},
        "VIIRS_SNPP_NRT": {"instrument": "VIIRS", "satellite": "Suomi-NPP", "resolution_m": 375},
        "VIIRS_NOAA21_NRT": {"instrument": "VIIRS", "satellite": "NOAA-21", "resolution_m": 375},
    }

    COUNTRY_BOUNDING_BOXES = {
        "IND": [68.0, 8.0, 97.0, 37.0],        # India
        "USA": [-125.0, 24.0, -66.5, 49.5],    # United States
        "CAN": [-141.0, 41.7, -52.6, 83.1],    # Canada
        "PUNJAB": [73.8, 29.5, 76.9, 32.5]     # Punjab Regional AOI
    }

    def __init__(self, map_key: Optional[str] = None, base_url: Optional[str] = None):
        self.map_key = map_key or app_settings.nasa_firms_map_key
        self.base_url = (base_url or app_settings.nasa_firms_base_url).rstrip("/")
        self.timeout_seconds = 30
        self.max_retries = 3

    def is_configured(self) -> bool:
        """Checks if a valid NASA MAP_KEY has been provided."""
        return bool(self.map_key and len(self.map_key.strip()) >= 10)

    def get_data_availability(self, source: str = "MODIS_NRT") -> Dict[str, Any]:
        """Queries NASA FIRMS data availability for a product."""
        if not self.is_configured():
            raise ConfigurationError(
                message="NASA FIRMS MAP_KEY is not configured. Live API calls cannot be executed.",
                parameter="NASA_FIRMS_MAP_KEY"
            )

        if source not in self.VALID_SOURCES:
            raise NASAAPIError(f"Unsupported NASA FIRMS source '{source}'. Valid sources: {list(self.VALID_SOURCES.keys())}")

        url = f"{self.base_url}/api/data_availability/csv/{self.map_key}/{source}"
        response_text = self._execute_request(url)
        try:
            df = pd.read_csv(io.StringIO(response_text))
            return {"source": source, "availability": df.to_dict(orient="records")}
        except Exception as e:
            raise NASAAPIError(f"Failed to parse NASA data availability: {str(e)}")

    def fetch_country_fires(
        self,
        country_code: str,
        source: str = "VIIRS_NOAA20_NRT",
        day_range: int = 1,
        date_str: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves satellite fire observations for a specific country.
        Endpoint: /api/country/csv/[MAP_KEY]/[SOURCE]/[COUNTRY]/[DAY_RANGE]/[DATE]
        """
        if not self.is_configured():
            raise ConfigurationError(
                message="NASA FIRMS MAP_KEY is not configured.",
                parameter="NASA_FIRMS_MAP_KEY"
            )

        if source not in self.VALID_SOURCES:
            raise NASAAPIError(f"Unsupported satellite source '{source}'.")

        country_code = country_code.upper()
        day_range = max(1, min(day_range, 10))

        try:
            if date_str:
                url = f"{self.base_url}/api/country/csv/{self.map_key}/{source}/{country_code}/{day_range}/{date_str}"
            else:
                url = f"{self.base_url}/api/country/csv/{self.map_key}/{source}/{country_code}/{day_range}"

            csv_data = self._execute_request(url)
            return self._parse_csv_response(csv_data, source)
        except NASAAPIError as e:
            # NASA FIRMS occasionally marks /api/country deprecated in favor of Area API with country bounds
            if country_code in self.COUNTRY_BOUNDING_BOXES:
                logger.info(f"Country endpoint unavailable for {country_code}; falling back to Area API with country bounding box.")
                return self.fetch_area_fires(
                    bbox=self.COUNTRY_BOUNDING_BOXES[country_code],
                    source=source,
                    day_range=day_range,
                    date_str=date_str
                )
            raise

    def fetch_area_fires(
        self,
        bbox: List[float],
        source: str = "VIIRS_NOAA20_NRT",
        day_range: int = 1,
        date_str: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves satellite fire observations for a custom bounding box.
        Endpoint: /api/area/csv/[MAP_KEY]/[SOURCE]/[min_lon,min_lat,max_lon,max_lat]/[DAY_RANGE]/[DATE]
        """
        if not self.is_configured():
            raise ConfigurationError(
                message="NASA FIRMS MAP_KEY is not configured.",
                parameter="NASA_FIRMS_MAP_KEY"
            )

        if source not in self.VALID_SOURCES:
            raise NASAAPIError(f"Unsupported satellite source '{source}'.")

        if len(bbox) != 4:
            raise NASAAPIError("Bounding box must contain exactly 4 coordinates: [min_lon, min_lat, max_lon, max_lat].")

        bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
        day_range = max(1, min(day_range, 10))

        if date_str:
            url = f"{self.base_url}/api/area/csv/{self.map_key}/{source}/{bbox_str}/{day_range}/{date_str}"
        else:
            url = f"{self.base_url}/api/area/csv/{self.map_key}/{source}/{bbox_str}/{day_range}"

        csv_data = self._execute_request(url)
        return self._parse_csv_response(csv_data, source)

    def _execute_request(self, url: str) -> str:
        """Executes HTTP request with exponential backoff and secret scrubbing in logs."""
        # Sanitize URL for logging
        sanitized_url = url
        if self.map_key and self.map_key in url:
            sanitized_url = url.replace(self.map_key, "[MAP_KEY_REDACTED]")

        headers = {"User-Agent": "Stubble2Power-EarthObservation/2.0"}

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"NASA FIRMS API request: {sanitized_url} (attempt {attempt}/{self.max_retries})")
                response = requests.get(url, headers=headers, timeout=self.timeout_seconds)

                if response.status_code == 200:
                    text = response.text.strip()
                    # NASA FIRMS returns errors as text even on 200 (e.g. "Bad MAP_KEY", "Invalid date")
                    if text.startswith("Bad MAP_KEY") or text.startswith("Invalid key"):
                        raise ConfigurationError(
                            message="NASA FIRMS API returned 'Bad MAP_KEY'. Please verify your NASA MAP_KEY.",
                            parameter="NASA_FIRMS_MAP_KEY"
                        )
                    if "Invalid" in text and len(text) < 100:
                        raise NASAAPIError(f"NASA FIRMS error response: {text}")
                    return text

                elif response.status_code in [429, 502, 503, 504]:
                    backoff = 2 ** attempt
                    logger.warning(f"NASA API returned {response.status_code}. Retrying in {backoff}s...")
                    time.sleep(backoff)
                else:
                    raise NASAAPIError(
                        message=f"NASA FIRMS API request failed with HTTP status {response.status_code}.",
                        status_code=response.status_code,
                        endpoint=sanitized_url
                    )

            except requests.RequestException as e:
                if attempt == self.max_retries:
                    raise NASAAPIError(f"NASA FIRMS connection error: {str(e)}", endpoint=sanitized_url)
                time.sleep(2 ** attempt)

        raise NASAAPIError(f"Failed to complete NASA FIRMS request after {self.max_retries} attempts.")

    def _parse_csv_response(self, csv_data: str, source: str) -> List[Dict[str, Any]]:
        """Parses NASA FIRMS CSV stream into structured dictionaries while preserving source metadata."""
        if not csv_data:
            return []

        try:
            df = pd.read_csv(io.StringIO(csv_data))
            if df.empty:
                return []

            records = df.to_dict(orient="records")
            source_meta = self.VALID_SOURCES.get(source, {})

            # Attach satellite source metadata
            for r in records:
                r["_source_product"] = source
                r["_instrument"] = source_meta.get("instrument", "UNKNOWN")
                r["_satellite"] = source_meta.get("satellite", r.get("satellite", "UNKNOWN"))

            return records
        except Exception as e:
            raise NASAAPIError(f"Failed to parse NASA CSV response: {str(e)}")
