# Airsense

Air quality monitoring and analytics pipeline.
# AirSense — Phase 1: Data Ingestion

AirSense ingests measured air-quality observations from OpenAQ and weather/current + hourly forecast data from Open-Meteo, normalizes them, and publishes JSON events to Kafka.

## Prerequisites
- Python 3.11+
- Docker Desktop
- An OpenAQ API key (keep it secret)

## Setup (macOS/Linux)
```bash
cp .env.example .env
# Edit .env and add your newly rotated OpenAQ key
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
docker compose up -d
python -m ingestion.air_quality.run
python -m ingestion.weather.run
```

## First audit run
Before running producers, test source connectivity and inspect Nairobi coverage:
```bash
python -m scripts.audit_sources
```

## Kafka
- `airsense.air-quality.raw`
- `airsense.weather.raw`

Kafka is exposed at `localhost:9092`. The local single-node KRaft broker is for development only.

## Security
Never commit `.env`. If an API key has been exposed, rotate it in the provider's account first.
