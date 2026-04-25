FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt pyproject.toml openenv.yaml ./
COPY agent_blackbox ./agent_blackbox
COPY server ./server
COPY examples ./examples
COPY outputs ./outputs
COPY README.md SAFETY.md BENCHMARK_SPEC.md TRAINING.md SUBMISSION_READY.md ./

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
