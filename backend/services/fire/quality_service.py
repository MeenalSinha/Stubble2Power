"""
Satellite Data Quality Control and Normalization Pipeline.
Standardizes heterogeneous MODIS and VIIRS observations into a canonical model,
quarantines anomalies with explicit reasons, and generates verifiable quality reports.
"""

import hashlib
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple
from backend.schemas.satellite import NormalizedObservationSchema, QualityControlSummary
from backend.services.geospatial.service import GeospatialService
from backend.core.config.settings import config_manager
from backend.core.logging.logger import get_logger

logger = get_logger("stubble2power.fire.quality")


class QualityControlService:
    @staticmethod
    def generate_observation_hash(
        satellite: str, instrument: str, acq_date_str: str, acq_time_str: str, lat: float, lon: float
    ) -> str:
        """Computes a deterministic MD5 hash for idempotent deduplication."""
        payload = f"{satellite}|{instrument}|{acq_date_str}|{acq_time_str}|{lat:.4f}|{lon:.4f}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def normalize_timestamp(acq_date_val: Any, acq_time_val: Any) -> Tuple[date, str, datetime]:
        """
        Normalizes acquisition date and HHMM string into UTC date, formatted time, and UTC datetime.
        """
        if isinstance(acq_date_val, date):
            acq_d = acq_date_val
        else:
            acq_d = datetime.strptime(str(acq_date_val).strip(), "%Y-%m-%d").date()

        time_str = str(acq_time_val).strip().zfill(4)
        hour = int(time_str[:2])
        minute = int(time_str[2:4])
        dt_utc = datetime(acq_d.year, acq_d.month, acq_d.day, hour, minute)
        formatted_time = f"{hour:02d}:{minute:02d}"

        return acq_d, formatted_time, dt_utc

    @staticmethod
    def normalize_confidence(confidence_raw: Any, instrument: str) -> float:
        """
        Product-aware confidence standardization to [0.0, 1.0].
        MODIS: 0-100 percentage.
        VIIRS: 'l' (low: 0.3), 'n' (nominal: 0.7), 'h' (high: 1.0).
        """
        c_str = str(confidence_raw).strip().lower()

        if instrument == "MODIS":
            try:
                val = float(c_str)
                return max(0.0, min(1.0, val / 100.0))
            except ValueError:
                if c_str in ["h", "high"]:
                    return 1.0
                elif c_str in ["n", "nominal"]:
                    return 0.7
                elif c_str in ["l", "low"]:
                    return 0.3
                return 0.5  # Nominal fallback if unrecognized string

        elif instrument == "VIIRS":
            if c_str in ["h", "high"]:
                return 1.0
            elif c_str in ["n", "nominal"]:
                return 0.7
            elif c_str in ["l", "low"]:
                return 0.3
            else:
                try:
                    val = float(c_str)
                    return max(0.0, min(1.0, val / 100.0 if val > 1.0 else val))
                except ValueError:
                    return 0.5

        return 0.5

    @classmethod
    def process_raw_record(
        cls, raw_record: Dict[str, Any], grid_resolution_deg: Optional[float] = None
    ) -> NormalizedObservationSchema:
        """
        Transforms raw NASA FIRMS dictionary into validated canonical schema.
        Quarantines invalid records with diagnostic reasons.
        """
        if grid_resolution_deg is None:
            grid_resolution_deg = float(config_manager.get("nasa.harmonization.grid_resolution_deg"))

        instrument = raw_record.get("_instrument", "UNKNOWN")
        if instrument == "UNKNOWN":
            instrument = "VIIRS" if "bright_ti4" in raw_record else "MODIS"

        satellite = raw_record.get("_satellite", raw_record.get("satellite", "UNKNOWN"))
        product_version = str(raw_record.get("version", raw_record.get("_source_product", "NRT")))

        # Field mapping (handles column variations between MODIS and VIIRS FIRMS outputs)
        lat_raw = raw_record.get("latitude", raw_record.get("lat"))
        lon_raw = raw_record.get("longitude", raw_record.get("lon"))
        acq_date_raw = raw_record.get("acq_date")
        acq_time_raw = raw_record.get("acq_time", "0000")
        conf_raw = str(raw_record.get("confidence", "nominal"))
        frp_raw = raw_record.get("frp")
        bright_raw = raw_record.get("bright_ti4", raw_record.get("brightness"))
        bright_t31_raw = raw_record.get("bright_ti5", raw_record.get("bright_t31"))
        daynight = str(raw_record.get("daynight", "D")).upper()

        is_valid = True
        quarantine_reason = None

        # 1. Coordinate Validation
        try:
            lat = float(lat_raw)
            lon = float(lon_raw)
            GeospatialService.validate_coordinates(lat, lon)
        except Exception as e:
            lat = 0.0
            lon = 0.0
            is_valid = False
            quarantine_reason = f"Invalid coordinates: {str(e)}"

        # 2. Timestamp Validation & Normalization
        try:
            acq_date, acq_time_utc, timestamp_utc = cls.normalize_timestamp(acq_date_raw, acq_time_raw)
        except Exception as e:
            acq_date = date.today()
            acq_time_utc = "00:00"
            timestamp_utc = datetime.utcnow()
            is_valid = False
            quarantine_reason = (quarantine_reason or "") + f"; Timestamp parsing failed: {str(e)}"

        # 3. Numeric values check
        frp = None
        if frp_raw is not None:
            try:
                frp = max(0.0, float(frp_raw))
            except (ValueError, TypeError):
                pass

        brightness = None
        if bright_raw is not None:
            try:
                b_val = float(bright_raw)
                min_b = float(config_manager.get("fire.qc.min_brightness_kelvin"))
                max_b = float(config_manager.get("fire.qc.max_brightness_kelvin"))
                if min_b <= b_val <= max_b:
                    brightness = b_val
                else:
                    is_valid = False
                    quarantine_reason = (quarantine_reason or "") + f"; Out-of-bounds brightness {b_val}K"
            except (ValueError, TypeError):
                pass

        bright_t31 = None
        if bright_t31_raw is not None:
            try:
                bright_t31 = float(bright_t31_raw)
            except (ValueError, TypeError):
                pass

        # 4. Confidence standardization
        confidence_norm = cls.normalize_confidence(conf_raw, instrument)

        # 5. Spatial Grid Assignment
        grid_id = None
        if is_valid:
            grid_id = GeospatialService.compute_grid_id(lat, lon, grid_resolution_deg)

        # 6. Provenance hash
        rec_hash = cls.generate_observation_hash(
            satellite=satellite,
            instrument=instrument,
            acq_date_str=str(acq_date),
            acq_time_str=acq_time_utc,
            lat=lat,
            lon=lon,
        )

        return NormalizedObservationSchema(
            source_record_hash=rec_hash,
            satellite=satellite,
            instrument=instrument,
            product_version=product_version,
            acquisition_date=acq_date,
            acquisition_time_utc=acq_time_utc,
            timestamp_utc=timestamp_utc,
            latitude=lat,
            longitude=lon,
            brightness=brightness,
            bright_t31=bright_t31,
            frp=frp,
            confidence_raw=conf_raw,
            confidence_normalized=confidence_norm,
            daynight=daynight,
            scan=float(raw_record.get("scan", 0.0)) if raw_record.get("scan") else None,
            track=float(raw_record.get("track", 0.0)) if raw_record.get("track") else None,
            spatial_grid_id=grid_id,
            is_valid=is_valid,
            quarantine_reason=quarantine_reason,
        )

    @classmethod
    def batch_process(
        cls, raw_records: List[Dict[str, Any]], grid_resolution_deg: Optional[float] = None
    ) -> Tuple[List[NormalizedObservationSchema], QualityControlSummary]:
        """
        Processes batch of raw satellite records, categorizing valid vs quarantined observations.
        """
        normalized_list: List[NormalizedObservationSchema] = []
        sensor_counts: Dict[str, int] = {}
        valid_count = 0
        quarantine_count = 0
        seen_hashes = set()
        duplicates_skipped = 0

        min_lat, max_lat = 90.0, -90.0
        min_lon, max_lon = 180.0, -180.0
        dates_seen: List[date] = []

        for raw in raw_records:
            norm = cls.process_raw_record(raw, grid_resolution_deg)
            if norm.source_record_hash in seen_hashes:
                duplicates_skipped += 1
                continue

            seen_hashes.add(norm.source_record_hash)
            sensor_counts[norm.instrument] = sensor_counts.get(norm.instrument, 0) + 1

            if norm.is_valid:
                valid_count += 1
                min_lat = min(min_lat, norm.latitude)
                max_lat = max(max_lat, norm.latitude)
                min_lon = min(min_lon, norm.longitude)
                max_lon = max(max_lon, norm.longitude)
                dates_seen.append(norm.acquisition_date)
            else:
                quarantine_count += 1

            normalized_list.append(norm)

        summary = QualityControlSummary(
            total_raw_records=len(raw_records),
            valid_records=valid_count,
            invalid_quarantined_records=quarantine_count,
            duplicate_records_skipped=duplicates_skipped,
            sensor_counts=sensor_counts,
            date_range_covered={
                "start": str(min(dates_seen)) if dates_seen else "N/A",
                "end": str(max(dates_seen)) if dates_seen else "N/A",
            },
            spatial_bbox_covered={
                "min_lat": round(min_lat, 4) if valid_count > 0 else 0.0,
                "max_lat": round(max_lat, 4) if valid_count > 0 else 0.0,
                "min_lon": round(min_lon, 4) if valid_count > 0 else 0.0,
                "max_lon": round(max_lon, 4) if valid_count > 0 else 0.0,
            },
            processing_version="2.0.0-canonical",
        )

        return normalized_list, summary
