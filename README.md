# vip-data-prep

## Setup
1. Copy `.env.template` to `.env`
2. Fill in your API credentials in `.env`
3. Install dependencies: `pip install -r requirements.txt`


## Go to the app directory
```bash
cd src
```

## Run locally with reload
```bash
cd src && streamlit run app.py
```

## Pre-commit
```bash
pre-commit run --all-files
```

## Docker
```bash
docker build -t  .
docker run -p 8501:8501 vip-data-prep
```

## Docker Compose
```bash
docker-compose up
```

## Docker Compose Rebuid
```bash
docker-compose up --build
```

## Docker Compose Down
```bash
docker-compose down
```
