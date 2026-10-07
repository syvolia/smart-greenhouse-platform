# 🌱 Smart Greenhouse Intelligence Platform

> A production-grade, end-to-end IoT platform that ingests greenhouse sensor data,
> runs streaming analytics, detects anomalies, predicts crop yield with ML, and
> serves actionable recommendations through a modern React dashboard.

[![CI](https://github.com/syvolia/smart-greenhouse/actions/workflows/ci.yml/badge.svg)](https://github.com/<your-user>/smart-greenhouse/actions/workflows/ci.yml)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue)
![Node 20](https://img.shields.io/badge/node-20-green)
![Docker](https://img.shields.io/badge/docker-compose-blue)

---

## Business Problem

Commercial greenhouses run on tight margins. A two-degree temperature excursion
or a missed irrigation window can cost thousands of dollars in lost yield. Most
growers rely on manual observation or isolated point solutions with no unified
view and no predictive layer.

This platform solves that end to end: it ingests every sensor reading, evaluates
it against crop targets, flags anomalies, predicts yield with ML, and recommends
concrete actions — all surfaced in a role-aware dashboard.

## Architecture

```mermaid
flowchart LR
    SIM[IoT Simulator<br/>72 sensors] -->|POST /ingestion| API[FastAPI Backend]
    API --> PG[(PostgreSQL 16)]
    PG --> AIR[Airflow]
    AIR --> SPK[Spark]
    SPK --> STG[(staging schema)]
    STG --> DBT[dbt]
    DBT --> ANL[(analytics schema)]
    ANL --> ML[ML Training]
    ML --> MLF[MLflow]
    MLF --> PRED[Prediction API]
    PG --> PRED
    PRED --> UI[React Dashboard]
    API --> UI