# Event Management API Backend

A FastAPI-based REST API for managing events with DynamoDB storage.

## 🚀 Features

- **RESTful API**: Full CRUD operations for events
- **Data Validation**: Pydantic models for request/response validation
- **Error Handling**: Comprehensive error handling with proper HTTP status codes
- **CORS Support**: Cross-origin resource sharing enabled
- **DynamoDB Integration**: Scalable NoSQL database storage
- **Lambda Ready**: Optimized for AWS Lambda deployment with Mangum

## 📋 API Endpoints

### Events Management

| Method | Endpoint | Description | Status Code |
|--------|----------|-------------|-------------|
| GET | `/events` | List all events | 200 |
| GET | `/events?status=active` | Filter events by status | 200 |
| POST | `/events` | Create new event | 201 |
| GET | `/events/{eventId}` | Get specific event | 200 |
| PUT | `/events/{eventId}` | Update event | 200 |
| DELETE | `/events/{eventId}` | Delete event | 204 |

### Health Check

| Method | Endpoint | Description | Status Code |
|--------|----------|-------------|-------------|
| GET | `/` | API welcome message | 200 |
| GET | `/health` | Health check | 200 |

## 🏗️ Data Models

### Event Model

```python
class Event(BaseModel):
    eventId: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    date: str = Field(..., description="ISO format date")
    location: str = Field(..., min_length=1)
    capacity: int = Field(..., gt=0)
    organizer: str = Field(..., min_length=1)
    status: str = Field(default="draft")
```

### EventUpdate Model

```python
class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    date: Optional[str] = None
    location: Optional[str] = Field(None, min_length=1)
    capacity: Optional[int] = Field(None, gt=0)
    organizer: Optional[str] = Field(None, min_length=1)
    status: Optional[str] = None
```

## 🛠️ Setup & Development

### Prerequisites

- Python 3.12+
- pip or poetry

### Installation

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables**
   ```bash
   export DYNAMODB_TABLE=your-table-name
   ```

3. **Run locally**
   ```bash
   uvicorn main:app --reload
   ```

4. **Access API documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 📚 Dependencies

- **FastAPI**: Modern, fast web framework for building APIs
- **Pydantic**: Data validation and settings management
- **Boto3**: AWS SDK for Python
- **Uvicorn**: ASGI server implementation
- **Mangum**: Adapter for running ASGI applications on AWS Lambda

## 🔧 Configuration

### Environment Variables

- `DYNAMODB_TABLE`: Name of the DynamoDB table (required)

### CORS Configuration

The API is configured to allow:
- All origins (`*`)
- All methods (GET, POST, PUT, DELETE, etc.)
- All headers

## 🧪 Testing

### Manual Testing

```bash
# Health check
curl http://localhost:8000/health

# List events
curl http://localhost:8000/events

# Create event
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "eventId": "test-123",
    "title": "Test Event",
    "description": "A test event",
    "date": "2024-12-15",
    "location": "Test Location",
    "capacity": 100,
    "organizer": "Test Organizer",
    "status": "active"
  }'
```

## 🚀 Deployment

This API is designed to run on AWS Lambda using the Mangum ASGI adapter. The `handler` function in `main.py` provides the Lambda entry point.

### Lambda Handler

```python
from mangum import Mangum
handler = Mangum(app)
```

## 📖 API Documentation

Detailed API documentation is available in the `docs/` folder, generated using pdoc.

## 🔍 Error Handling

The API provides comprehensive error handling:

- **400 Bad Request**: Invalid input data
- **404 Not Found**: Event not found
- **500 Internal Server Error**: Server-side errors

All errors return JSON responses with descriptive messages.

## 🔒 DynamoDB Reserved Keywords

The API handles DynamoDB reserved keywords (like `status` and `capacity`) using ExpressionAttributeNames to avoid conflicts.