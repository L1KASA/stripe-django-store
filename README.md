# Stripe Django Store

## Getting Started

### 1. Environment Configuration

Copy `.env.example` to `.env` and fill it

### 2. Run with Docker

```bash
docker-compose up -d --build
```

The application will be available at `http://localhost:8000/`.

### 3. Initialize Database

Run migrations and create a superuser:

```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```
