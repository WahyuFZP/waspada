FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir --root-user-action=ignore -r requirements.txt
# database lokasi IP di luar /app: folder /app ditimpa mount kode live di docker-compose
COPY geoip_fetch.py /tmp/
RUN python /tmp/geoip_fetch.py
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-graceful-shutdown", "2"]
