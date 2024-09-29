FROM python:3.12-alpine

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

ENV DJANGO_SETTINGS_MODULE=social_network.settings.cloud_settings

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]