# Documentation Index

Welcome to the Smart Greenhouse Intelligence Platform documentation.

## Contents

| Document | Description |
|---|---|
| [architecture.md](./architecture.md) | System design, component diagram, key decisions, failure modes |
| [data-pipeline.md](./data-pipeline.md) | Spark + dbt + Airflow flow, schemas, data quality gates |
| [ml-pipeline.md](./ml-pipeline.md) | Dataset, features, training, evaluation, MLflow, serving |
| [api.md](./api.md) | Full REST API reference with roles and examples |
| [auth.md](./auth.md) | JWT strategy, refresh rotation, RBAC matrix, bootstrap |
| [deployment.md](./deployment.md) | Free-tier hosting, production checklist |
| [development.md](./development.md) | Local setup, common workflows, testing recipes |
| [troubleshooting.md](./troubleshooting.md) | Common errors and their fixes |

## Suggested Reading Order

1. **New to the project?** Start with the top-level [README.md](../README.md), then `architecture.md`.
2. **Interviewing/reviewing?** Read `architecture.md` → `data-pipeline.md` → `ml-pipeline.md`.
3. **Setting up locally?** `development.md` → `troubleshooting.md`.
4. **Deploying?** `deployment.md`.
5. **Integrating?** `api.md` and `auth.md`.