FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home bridge
RUN mkdir -p /data && chown bridge:bridge /data
COPY --chown=bridge:bridge core.py server.py fattura24_client.py fattura24_extra.py ./
USER bridge
EXPOSE 8765
CMD ["uvicorn","server:app","--host","0.0.0.0","--port","8765","--workers","1"]
