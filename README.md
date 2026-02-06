# Event Management System

A serverless event management system built with FastAPI, DynamoDB, and AWS CDK.

## 🚀 Features

- **CRUD Operations**: Create, read, update, and delete events
- **Status Filtering**: Filter events by status (active, draft, cancelled)
- **Serverless Architecture**: Built on AWS Lambda and API Gateway
- **NoSQL Database**: Uses DynamoDB for scalable data storage
- **CORS Enabled**: Ready for web application integration
- **Input Validation**: Comprehensive request validation with Pydantic
- **Error Handling**: Proper HTTP status codes and error messages

## 📋 Event Properties

Each event contains the following properties:
- `eventId`: Unique identifier (string)
- `title`: Event title (string, 1-200 characters)
- `description`: Event description (string)
- `date`: Event date (ISO format string)
- `location`: Event location (string)
- `capacity`: Maximum attendees (positive integer)
- `organizer`: Event organizer (string)
- `status`: Event status (draft, published, cancelled, active)

## 🏗️ Project Structure

```
├── backend/           # FastAPI Python backend application
│   ├── main.py       # Main FastAPI application
│   ├── requirements.txt
│   ├── docs/         # Generated API documentation
│   └── README.md
├── infrastructure/    # CDK TypeScript infrastructure-as-code
│   ├── bin/          # CDK app entry point
│   ├── lib/          # CDK stack definitions
│   ├── package.json
│   ├── cdk.json
│   └── README.md
├── .kiro/            # Kiro configuration (MCP servers)
└── README.md
```

## 🛠️ Setup Instructions

### Prerequisites

- Python 3.12+
- Node.js 20+
- AWS CLI configured
- AWS CDK CLI installed

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/92eda/participant-repo-311889745677.git
   cd participant-repo-311889745677
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

3. **Infrastructure Setup**
   ```bash
   cd infrastructure
   npm install
   npm run build
   ```

### AWS Deployment

1. **Bootstrap CDK (first time only)**
   ```bash
   cd infrastructure
   cdk bootstrap
   ```

2. **Deploy to AWS**
   ```bash
   cdk deploy --require-approval never
   ```

## 📚 API Documentation

### Base URL
```
https://0qdton9e1g.execute-api.us-west-2.amazonaws.com/prod/
```

### Endpoints

#### GET /events
List all events or filter by status.

**Query Parameters:**
- `status` (optional): Filter events by status (active, draft, cancelled)

**Response:** 200 OK
```json
{
  "events": [
    {
      "eventId": "api-test-event-456",
      "title": "API Gateway Test Event",
      "description": "Testing API Gateway integration",
      "date": "2024-12-15",
      "location": "API Test Location",
      "capacity": 200,
      "organizer": "API Test Organizer",
      "status": "active"
    }
  ]
}
```

#### POST /events
Create a new event.

**Request Body:**
```json
{
  "eventId": "api-test-event-456",
  "title": "API Gateway Test Event",
  "description": "Testing API Gateway integration",
  "date": "2024-12-15",
  "location": "API Test Location",
  "capacity": 200,
  "organizer": "API Test Organizer",
  "status": "active"
}
```

**Response:** 201 Created
```json
{
  "eventId": "api-test-event-456",
  "title": "API Gateway Test Event",
  "description": "Testing API Gateway integration",
  "date": "2024-12-15",
  "location": "API Test Location",
  "capacity": 200,
  "organizer": "API Test Organizer",
  "status": "active"
}
```

#### GET /events/{eventId}
Retrieve a specific event by ID.

**Response:** 200 OK
```json
{
  "eventId": "api-test-event-456",
  "title": "API Gateway Test Event",
  "description": "Testing API Gateway integration",
  "date": "2024-12-15",
  "location": "API Test Location",
  "capacity": 200,
  "organizer": "API Test Organizer",
  "status": "active"
}
```

#### PUT /events/{eventId}
Update an existing event.

**Request Body:**
```json
{
  "title": "Updated API Gateway Test Event",
  "capacity": 250
}
```

**Response:** 200 OK
```json
{
  "eventId": "api-test-event-456",
  "title": "Updated API Gateway Test Event",
  "description": "Testing API Gateway integration",
  "date": "2024-12-15",
  "location": "API Test Location",
  "capacity": 250,
  "organizer": "API Test Organizer",
  "status": "active"
}
```

#### DELETE /events/{eventId}
Delete an event.

**Response:** 204 No Content

## 🧪 Testing

### Example API Calls

```bash
# List all events
curl https://0qdton9e1g.execute-api.us-west-2.amazonaws.com/prod/events

# Filter active events
curl "https://0qdton9e1g.execute-api.us-west-2.amazonaws.com/prod/events?status=active"

# Create an event
curl -X POST https://0qdton9e1g.execute-api.us-west-2.amazonaws.com/prod/events \
  -H "Content-Type: application/json" \
  -d '{
    "eventId": "test-event-123",
    "title": "Test Event",
    "description": "A test event",
    "date": "2024-12-15",
    "location": "Test Location",
    "capacity": 100,
    "organizer": "Test Organizer",
    "status": "active"
  }'

# Get specific event
curl https://0qdton9e1g.execute-api.us-west-2.amazonaws.com/prod/events/test-event-123

# Update event
curl -X PUT https://0qdton9e1g.execute-api.us-west-2.amazonaws.com/prod/events/test-event-123 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Test Event",
    "capacity": 150
  }'

# Delete event
curl -X DELETE https://0qdton9e1g.execute-api.us-west-2.amazonaws.com/prod/events/test-event-123
```

## 🏛️ Architecture

- **API Gateway**: HTTP API endpoint
- **AWS Lambda**: Serverless compute for FastAPI application
- **DynamoDB**: NoSQL database for event storage
- **CDK**: Infrastructure as Code for AWS resources

## 🔧 Technologies Used

- **Backend**: FastAPI, Pydantic, Boto3, Mangum
- **Infrastructure**: AWS CDK, TypeScript
- **Database**: Amazon DynamoDB
- **Deployment**: AWS Lambda, API Gateway
- **Documentation**: pdoc

## 📝 MCP Servers Configured

- AWS Knowledge Server
- AWS Frontend MCP Server
- AWS CDK Server
- Brave Search Server
- Fetch Server
- Context7

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.