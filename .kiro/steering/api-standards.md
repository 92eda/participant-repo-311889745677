---
inclusion: fileMatch
fileMatchPattern: "**/*{api,main,handler,route,endpoint}*.{py,ts,js}"
---

# API Standards and Best Practices

This steering file defines REST API conventions and standards for this project. Follow these guidelines when working with API-related code.

## HTTP Methods

Use the appropriate HTTP method for each operation:

- **GET**: Retrieve resources (read-only, idempotent)
- **POST**: Create new resources (non-idempotent)
- **PUT**: Update existing resources (replace entire resource, idempotent)
- **PATCH**: Partially update existing resources (idempotent)
- **DELETE**: Remove resources (idempotent)

## HTTP Status Codes

Use standard HTTP status codes consistently:

### Success Codes (2xx)
- **200 OK**: Successful GET, PUT, PATCH requests
- **201 Created**: Successful POST request that creates a resource
- **204 No Content**: Successful DELETE request or PUT/PATCH with no response body

### Client Error Codes (4xx)
- **400 Bad Request**: Invalid request data or validation errors
- **401 Unauthorized**: Authentication required or failed
- **403 Forbidden**: Authenticated but not authorized
- **404 Not Found**: Resource does not exist
- **409 Conflict**: Resource conflict (e.g., duplicate)
- **422 Unprocessable Entity**: Validation errors with detailed information

### Server Error Codes (5xx)
- **500 Internal Server Error**: Unexpected server errors
- **503 Service Unavailable**: Service temporarily unavailable

## JSON Response Format Standards

### Success Response Format

All successful responses should follow this structure:

```json
{
  "data": {
    // Resource data or array of resources
  },
  "metadata": {
    // Optional: pagination, timestamps, etc.
  }
}
```

For single resource:
```json
{
  "eventId": "event-123",
  "title": "Event Title",
  "description": "Event description",
  "date": "2024-12-15",
  "location": "Event Location",
  "capacity": 100,
  "organizer": "Organizer Name",
  "status": "active"
}
```

For list of resources:
```json
{
  "events": [
    {
      "eventId": "event-123",
      "title": "Event Title",
      ...
    }
  ]
}
```

### Error Response Format

All error responses must follow this consistent structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": [
      // Optional: array of detailed error information
    ]
  }
}
```

Examples:

**400 Bad Request:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": [
      {
        "field": "capacity",
        "message": "Must be a positive integer"
      }
    ]
  }
}
```

**404 Not Found:**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Event not found"
  }
}
```

**500 Internal Server Error:**
```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred"
  }
}
```

## REST API Conventions

### Endpoint Naming
- Use plural nouns for resource collections: `/events`, `/users`
- Use lowercase and hyphens for multi-word resources: `/event-categories`
- Use resource IDs in path parameters: `/events/{eventId}`
- Use query parameters for filtering: `/events?status=active`

### Request/Response Headers
- **Content-Type**: `application/json` for JSON payloads
- **Accept**: `application/json` for JSON responses

### CORS Configuration
- Configure appropriate CORS headers for web access
- Allow necessary HTTP methods and headers

### Input Validation
- Validate all input data using schema validation (e.g., Pydantic)
- Return 400 Bad Request with detailed validation errors
- Sanitize user input to prevent injection attacks

### Error Handling
- Always catch and handle exceptions appropriately
- Never expose internal error details or stack traces to clients
- Log errors server-side for debugging
- Return consistent error response format

### Reserved Keywords
- Be mindful of database reserved keywords (e.g., DynamoDB: `status`, `capacity`, `name`)
- Use ExpressionAttributeNames when necessary

## API Documentation
- Document all endpoints with clear descriptions
- Include request/response examples
- Document all possible status codes
- Keep API documentation up-to-date with code changes
