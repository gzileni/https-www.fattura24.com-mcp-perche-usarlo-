FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home bridge
RUN mkdir -p /data && chown bridge:bridge /data
COPY --chown=bridge:bridge core.py server.py fattura24_client.py fattura24_extra.py official_gateway.py ./
COPY --chown=bridge:bridge scripts/smoke_test.py scripts/connect_official.py ./
USER bridge
EXPOSE 8765
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD python -c "import urllib.request; r=urllib.request.urlopen('http://127.0.0.1:8765/health',timeout=3); assert r.status == 200 and r.read() == b'ok'"
CMD ["uvicorn","server:app","--host","0.0.0.0","--port","8765","--workers","1","--no-access-log"]
