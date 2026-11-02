import time
from ingestion.common.config import get_setting, load_cities
from ingestion.common.kafka import build_producer, publish
from ingestion.air_quality.client import OpenAQClient, normalize_measurement

def main():
    api_key = get_setting("OPENAQ_API_KEY")
    radius = int(get_setting("OPENAQ_RADIUS_METERS", "25000"))
    limit = int(get_setting("OPENAQ_PAGE_LIMIT", "100"))
    bootstrap = get_setting("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    topic = get_setting("KAFKA_AIR_QUALITY_TOPIC", "airsense.air-quality.raw")
    client = OpenAQClient(api_key, float(get_setting("REQUEST_TIMEOUT_SECONDS", "30")))
    producer = build_producer(bootstrap)
    try:
        for city in load_cities():
            print(f"Discovering OpenAQ locations near {city['city']}...")
            locations = client.get_locations_near_city(city["latitude"], city["longitude"], radius, limit)
            print(f"OpenAQ returned {len(locations)} locations for {city['city']}.")
            for location in locations:
                location_id = location.get("id")
                if not location_id:
                    continue
                # Inspect sensor metadata before requesting latest readings.
                supported = {
                    (sensor.get("parameter") or {}).get("name", "").lower()
                    for sensor in location.get("sensors", [])
                }
                if supported and not supported.intersection({"pm25", "pm2.5", "pm10", "no2", "o3", "co", "so2"}):
                    continue
                try:
                    latest = client.get_latest_for_location(location_id)
                except Exception as exc:
                    print(f"Skipping location {location_id}: {exc}")
                    continue
                for raw in latest:
                    event = normalize_measurement(raw, city, location)
                    if event:
                        key = f"{city['city_id']}:{event.get('location_id')}:{event.get('sensor_id')}:{event['parameter']}"
                        publish(producer, topic, key, event)
                time.sleep(0.15)
    finally:
        producer.flush()
        producer.close()
        client.close()

if __name__ == "__main__":
    main()
