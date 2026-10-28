FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# ⭐ کپی کردن فایل requirements.txt
COPY requirements.txt .

# نصب پیش‌نیازهای سیستمی
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# کپی کردن پوشه پکیج‌های دانلود شده (آفلاین)
COPY offline_packages /app/offline_packages

# نصب پکیج‌ها از پوشه محلی
RUN pip install --no-index --find-links=/app/offline_packages -r requirements.txt

# کپی کردن کدهای پروژه
COPY app ./app

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]