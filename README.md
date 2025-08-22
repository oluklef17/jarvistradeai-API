# JarvisTrade FastAPI Backend

A modern, high-performance backend API for JarvisTrade built with FastAPI and SQLAlchemy.

## Features

- **FastAPI**: High-performance web framework with automatic API documentation
- **SQLAlchemy ORM**: Type-safe database operations
- **PostgreSQL**: Robust relational database
- **JWT Authentication**: Secure token-based authentication
- **Pydantic Validation**: Automatic request/response validation
- **Alembic Migrations**: Database schema versioning
- **CORS Support**: Cross-origin resource sharing
- **OpenAPI Documentation**: Auto-generated API docs

## Tech Stack

- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL with SQLAlchemy 2.0
- **Authentication**: JWT with python-jose
- **Password Hashing**: bcrypt with passlib
- **Validation**: Pydantic 2.5
- **Migrations**: Alembic
- **Server**: Uvicorn

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL database
- pip (Python package manager)

### Installation

1. **Clone and navigate to backend directory**

   ```bash
   cd backend
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the backend directory:

   ```env
   DATABASE_URL=postgresql://username:password@localhost/jarvistrade
   SECRET_KEY=your-secret-key-here
   ```

5. **Initialize database**

   ```bash
   # Create tables
   python -c "from database import engine; from models import Base; Base.metadata.create_all(bind=engine)"

   # Seed database
   python seed.py
   ```

6. **Run the server**

   ```bash
   python main.py
   ```

7. **Access the API**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

## API Endpoints

### Authentication

- `POST /api/auth/login` - Login with email/password
- `GET /api/users/me` - Get current user info

### Products

- `GET /api/products` - List all products (with filtering)
- `GET /api/products/{id}` - Get specific product
- `POST /api/products` - Create new product (admin only)
- `PUT /api/products/{id}` - Update product (admin only)
- `DELETE /api/products/{id}` - Delete product (admin only)

### Query Parameters for Products

- `skip` - Number of records to skip (pagination)
- `limit` - Number of records to return (max 50)
- `category` - Filter by category
- `search` - Search in name and description
- `featured` - Filter featured products (true/false)

## Database Models

### User

- `id` (UUID, primary key)
- `email` (unique)
- `name`
- `hashed_password`
- `is_admin` (boolean)
- `is_client` (boolean)
- `rating` (float)
- `total_reviews` (integer)
- `created_at`, `updated_at`

### Product

- `id` (UUID, primary key)
- `name`, `description`, `short_description`
- `price`, `original_price`
- `category`, `tags` (array)
- `is_active`, `is_featured` (boolean)
- `stock`, `downloads`, `rating`, `total_reviews`
- `sku`, `weight`, `dimensions`
- `requirements`, `features` (array), `changelog`
- `images` (array)
- `created_at`, `updated_at`

## Authentication

The API uses JWT tokens for authentication:

1. **Login** to get an access token
2. **Include token** in Authorization header: `Bearer <token>`
3. **Admin endpoints** require admin privileges

### Example Usage

```bash
# Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@jarvistrade.com", "password": "admin123"}'

# Use token for authenticated requests
curl -X GET "http://localhost:8000/api/products" \
  -H "Authorization: Bearer <your-token>"
```

## Development

### Project Structure

```
backend/
├── main.py              # FastAPI application
├── database.py          # Database configuration
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── auth.py              # Authentication logic
├── seed.py              # Database seeding
├── requirements.txt     # Python dependencies
├── alembic.ini         # Alembic configuration
└── README.md           # This file
```

### Database Migrations

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Create a new migration
alembic revision --autogenerate -m "Add new field"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Adding New Endpoints

1. **Create schema** in `schemas.py`
2. **Add model** in `models.py` (if needed)
3. **Create endpoint** in `main.py`
4. **Add authentication** if required
5. **Test** with the auto-generated docs

### Environment Variables

| Variable       | Description                  | Required |
| -------------- | ---------------------------- | -------- |
| `DATABASE_URL` | PostgreSQL connection string | Yes      |
| `SECRET_KEY`   | JWT secret key               | Yes      |

## Production Deployment

### Docker (Recommended)

1. **Create Dockerfile**

   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. **Build and run**
   ```bash
   docker build -t jarvistrade-backend .
   docker run -p 8000:8000 jarvistrade-backend
   ```

### Manual Deployment

1. **Set up server** with Python 3.8+
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Configure environment variables**
4. **Set up PostgreSQL database**
5. **Run migrations**: `alembic upgrade head`
6. **Start server**: `uvicorn main:app --host 0.0.0.0 --port 8000`

### Using Gunicorn (Production)

```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Testing

### Manual Testing

- Use the auto-generated docs at `/docs`
- Test with curl or Postman
- Check the interactive API documentation

### Automated Testing

```bash
# Install test dependencies
pip install pytest httpx

# Run tests
pytest
```

## API Documentation

The API automatically generates documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Default Credentials

After running `python seed.py`:

- **Admin**: admin@jarvistrade.com / admin123
- **User**: user@jarvistrade.com / user123

**⚠️ Change these passwords in production!**

## Troubleshooting

### Common Issues

1. **Database connection error**

   - Check `DATABASE_URL` in `.env`
   - Ensure PostgreSQL is running
   - Verify database exists

2. **Import errors**

   - Activate virtual environment
   - Install requirements: `pip install -r requirements.txt`

3. **Authentication errors**

   - Check `SECRET_KEY` in `.env`
   - Verify token format: `Bearer <token>`

4. **CORS errors**
   - Update `allow_origins` in `main.py`
   - Add your frontend URL to the list

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.
