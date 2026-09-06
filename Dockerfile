FROM python:3.12-slim

WORKDIR /app

# Copy just requirements first -- Docker caches this layer, so rebuilding
# after a code change (not a dependency change) skips reinstalling everything.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the NLTK data the ingredient parser needs, at BUILD time
# rather than the container's first run -- avoids needing internet access
# (or a slow first request) when someone actually starts the container.
RUN python -c "import nltk; nltk.download('averaged_perceptron_tagger_eng')"

# Now copy the actual application code.
COPY . .

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Apply any pending Alembic migrations, THEN start the server. This means
# every time the container starts (including after an update), the
# database schema is automatically brought up to date first.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]