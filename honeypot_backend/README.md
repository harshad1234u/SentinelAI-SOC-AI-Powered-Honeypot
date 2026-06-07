# AI-Powered Honeypot SOC Backend

A FastAPI backend for monitoring honeypots (Cowrie/OpenCanary) utilizing Loki for ingestion, Qdrant for RAG vector search, and NVIDIA NIM for multi-model AI analysis.

## Quickstart

1. Create a `.env` file based on `.env.example`.
2. Ensure you have NVIDIA NIM, AbuseIPDB, and Telegram credentials.
3. Place `GeoLite2-City.mmdb` and `GeoLite2-ASN.mmdb` in the `data/` directory.
4. Run `docker-compose up -d`.

## Services

- `api`: FastAPI backend running on port 8000.
- `rq-worker`: Background worker processing AI pipelines.
- `postgres`: Relational database for attack data.
- `redis`: Rate limiting, caching, and background queues.
- `qdrant`: Vector database for AI embeddings.

## Key Features

- Ingestion from Loki
- GeoIP & Threat Intelligence (AbuseIPDB) enrichment
- AI-driven Realtime Triage (DeepSeek Flash)
- Deep RAG Investigations (Qwen3 + e5 Embeddings)
- Dynamic rules-based Alerting to Telegram
- WebSocket Live Feed 

For full details, check the source code and configuration.
