FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY karatmatch ./karatmatch
RUN pip install --no-cache-dir .

EXPOSE 8000
ENV KARATMATCH_DATA_DIR=/app/data
CMD ["uvicorn", "karatmatch.api:app", "--host", "0.0.0.0", "--port", "8000"]
