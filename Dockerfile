# Unverified: Docker is not available in this environment; this file was not
# build-tested. See docs/SECURITY_REVIEW.md.
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

ENV MCP_CONSIST_HOST=0.0.0.0
ENV PORT=7860
EXPOSE 7860

CMD ["python", "demo/app.py"]