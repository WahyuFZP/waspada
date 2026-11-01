FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATA_DIR=/data
COPY requirements.txt .
RUN pip install --no-cache-dir --root-user-action=ignore -r requirements.txt
COPY . .
# bukan root: APK dari luar diurai di sini, jadi hak akses sekecil mungkin
RUN useradd --system --uid 10001 scanner && mkdir -p /data && chown scanner /data
USER scanner
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
