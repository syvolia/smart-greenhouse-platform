# Architecture

This document describes the Smart Greenhouse Intelligence Platform's design:
its components, the paths data takes, the decisions we made, and the failure
modes we tolerate.

---

## Overview

The platform has three planes that share infrastructure but never block each other:

| Plane | Purpose | Optimised for | Freshness |
|---|---|---|---|
| **Operational** | Sensor → API → Dashboard | Latency | Seconds |
| **Analytical** | Raw → modelled marts | Throughput | Minutes / hours |
| **ML** | Train → register → serve | Reproducibility | On demand |

The operational plane is the source of truth for the raw data. The analytical
plane reads only from `raw` views and writes to `staging`/`analytics`. The ML
plane reads from either, but never writes into the operational schema.

---

## Component Diagram

```mermaid
flowchart TB
    subgraph Client["Client"]
        BROWSER[Browser<br/>React SPA]
    end

    subgraph Edge["Edge"]
        NGINX[Nginx<br/>static + SPA fallback]
    end

    subgraph Application["Application"]
        API[FastAPI<br/>REST + JWT + RBAC]
        SIM[Simulator<br/>72 IoT sensors]
    end

    subgraph Data["Data"]
        PG[(PostgreSQL 16<br/>public / raw / staging / analytics)]
        MLF[MLflow Server]
    end

    subgraph Batch["Batch"]
        AF[Airflow<br/>scheduler + webserver]
        SPK[Spark<br/>master + worker]
    end

    subgraph Modeling["Modelling"]
        DBT[dbt models]
        MLOPS[ML training pipeline]
    end

    BROWSER --> NGINX
    NGINX --> API
    SIM --> API
    API --> PG
    API -.loads models.-> MLF
    PG --> AF
    AF --> SPK
    SPK --> PG
    AF --> DBT
    DBT --> PG
    PG --> MLOPS
    MLOPS --> MLF