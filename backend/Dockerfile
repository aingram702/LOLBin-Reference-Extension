# Build context is the repository root (see docker-compose.yml) so this
# Dockerfile can bundle both the backend app and the shared seed database.
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app/ ./app/

# Bundle the seed database so `python -m app.seed_data` works inside the
# container (the repo's extension/ tree is not otherwise present here).
COPY extension/data/lolbin_db.json ./app/data/lolbin_db.json

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
