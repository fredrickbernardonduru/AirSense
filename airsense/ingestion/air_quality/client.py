from datetime import datetime, timezone
import httpx

BASE_URL = "https://api.openaq.org/v3"

class OpenAQClient:
    def __init__(self, api_key: str, timeout_seconds: float = 30.0):
        if not api_key:
            raise ValueError("OPENAQ_API_KEY is missing. Add your newly rotated key to .env")
        self.client = httpx.Client(
            base_url=BASE_URL,
            timeout=timeout_seconds,
            headers={"X-API-Key": api_key, "User-Agent": "AirSense/0.1"},
        )

    def get_locations_near_city(self, latitude: float, longitude: float, radius_m: int = 25000, limit: int = 100) -> list[dict]:
        response = self.client.get("/locations", params={
            "coordinates": f"{latitude},{longitude}",
            "radius": radius_m,
            "limit": limit,
            "page": 1,
        })
        response.raise_for_status()
        return response.json().get("results", [])

    def get_latest_for_location(self, location_id: int) -> list[dict]:
        response = self.client.get(f"/locations/{location_id}/latest", params={"limit": 100})
        response.raise_for_status()
        return response.json().get("results", [])

    def close(self):
        self.client.close()

def normalize_measurement(raw: dict, city: dict, location: dict) -> dict | None:
    parameter = raw.get("parameter") or {}
    parameter_name = (parameter.get("name") or parameter.get("displayName") or "").lower()
    aliases = {"pm25": "pm2_5", "pm2.5": "pm2_5", "pm10": "pm10", "no2": "no2", "o3": "o3", "co": "co", "so2": "so2"}
    pollutant = aliases.get(parameter_name.replace(".", ""), aliases.get(parameter_name))
    if not pollutant:
        pollutant = aliases.get(parameter_name)
    value = raw.get("value")
    if value is None:
        return None

    dt = raw.get("datetime") or {}
    observed_at = dt.get("utc") if isinstance(dt, dict) else dt
    if not observed_at:
        observed_at = datetime.now(timezone.utc).isoformat()

    coords = raw.get("coordinates") or location.get("coordinates") or {}
    return {
        "event_type": "air_quality_observation",
        "source": "openaq",
        "city_id": city["city_id"],
        "city": city["city"],
        "country_code": city["country_code"],
        "location_id": raw.get("locationsId") or location.get("id"),
        "location_name": location.get("name"),
        "sensor_id": raw.get("sensorsId") or raw.get("sensors_id"),
        "parameter": pollutant or parameter_name or "unknown",
        "parameter_original": parameter_name or None,
        "value": float(value),
        "unit": raw.get("unit") or parameter.get("units"),
        "observed_at": observed_at,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "latitude": coords.get("latitude"),
        "longitude": coords.get("longitude"),
        "source_license": None,
    }
