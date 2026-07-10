# P13 — Estimation et Prédiction des Effectifs Scolaires

Plateforme Data Science industrialisée pour **Rennes Métropole** : prédiction des effectifs scolaires (maternelle / élémentaire) à partir de données démographiques, immobilières et éducatives.

## Architecture Docker

| Service | Port | Description |
|---------|------|-------------|
| **PostgreSQL** | 5433 | Base de données centralisée |
| **FastAPI** | 8000 | API REST de prédiction |
| **Streamlit** | 8501 | Dashboard interactif |
| **Jupyter Lab** | 8889 | Exploration & notebooks |
| **MLflow UI** | 5001 | Tracking expériences ML |
| **ETL** | — | Chargement CSV → PostgreSQL |

```
DATA/ (CSV)  ──►  ETL  ──►  PostgreSQL  ◄──  Jupyter
                              ▲    │
                              │    ▼
                           FastAPI ──► Streamlit
                              │
                           ML Models (joblib + MLflow)
```

## Démarrage rapide

### Prérequis
- Docker & Docker Compose
- Données dans le dossier `DATA/`

### 1. Configuration

```bash
cp .env.example .env
```

### 2. Lancer l'infrastructure

```bash
docker compose up -d postgres api streamlit jupyter
```

### 3. Charger les données (ETL)

```bash
docker compose --profile postgres --profile etl run --rm etl
```

> **Note** : `Ficdep22.csv` (~3,5 Go) n'est pas chargé automatiquement. Utilisez Jupyter pour l'explorer par morceaux (filtre département 35).

### 4. Entraîner les modèles ML

```bash
curl -X POST http://localhost:8000/ml/train
```

Ou via le dashboard Streamlit → **ML Training**.

## Accès aux services

| URL | Accès |
|-----|-------|
| http://localhost:${API_HOST_PORT} (défaut 8000) | API Swagger |
| http://localhost:${STREAMLIT_HOST_PORT} (défaut 8501) | Dashboard Streamlit |
| http://localhost:${JUPYTER_HOST_PORT} (défaut 8889) | Jupyter Lab (token: `JUPYTER_TOKEN`) |
| http://localhost:${MLFLOW_HOST_PORT} (défaut 5001) | MLflow UI |

## Cas d'usage métier

### Prédiction unitaire (logement à livrer)

```bash
curl -X POST http://localhost:8000/predictions/logement \
  -H "Content-Type: application/json" \
  -d '{"code_insee":"35238","surface_m2":75,"nb_pieces":4,"nb_logements":1}'
```

### Prédiction batch (CSV)

Fichier CSV avec colonnes : `code_insee`, `surface_m2`, `nb_pieces`, `nb_logements` (optionnel).

```bash
curl -X POST http://localhost:8000/predictions/batch \
  -F "file=@logements.csv"
```

## Données intégrées

| Source | Table PostgreSQL |
|--------|-----------------|
| communes_rennes_metropole.csv | `communes` |
| donnee_statistique_commune_rennes_metropole.csv | `stats_communes` |
| fr-en-ecoles-effectifs-nb_classes.csv | `ecoles_effectifs` |
| population-par-sexe-age-et-nationalite-par-commune-2014.csv | `population_2014` |
| mutation_immobiliere_dvf_rm.csv | `mutations_dvf` |
| permis_de_construire_*.csv | `permis_construire` |
| referentiel-batiment-*.csv | `referentiel_batiment` |
| nombre-et-type-de-logement-*.csv | `logements_parcelle` |

## Modèles ML

- **Baseline** : Régression linéaire, Ridge
- **Avancés** : Random Forest, Gradient Boosting
- **Métriques** : RMSE, MAE, R², MAPE
- **Tracking** : MLflow
- **Explainability** : corrélations + SHAP (notebook)

## Structure du projet

```
P13/
├── DATA/                    # Données sources
├── docker/                  # Dockerfiles
├── database/
│   ├── init/01_schema.sql   # Schéma PostgreSQL
│   └── scripts/load_data.py # ETL
├── src/p13/                 # Package Python partagé
│   ├── config.py
│   ├── db.py
│   └── ml/                  # train, predict, features
├── api/                     # FastAPI
├── streamlit/app/           # Dashboard
├── jupyter/notebooks/       # Notebooks EDA, SHAP, evaluation
├── models/                  # Modèles entraînés
└── docker-compose.yml
```

## Commandes utiles

```bash
docker compose logs -f api
docker compose build --no-cache
docker compose down
docker compose down -v   # reset PostgreSQL
```
