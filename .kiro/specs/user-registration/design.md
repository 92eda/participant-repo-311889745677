# User Registration Feature - Design

## Architecture Overview

This feature extends the existing Event Management API with user registration capabilities. The design follows a serverless architecture using AWS Lambda, API Gateway, and DynamoDB.

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  API Gateway    │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Lambda Handler │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│    DynamoDB     │
│  ┌───────────┐  │
│  │  Users    │  │
│  ├───────────┤  │
│  │  Events   │  │
│  ├───────────┤  │
│  │Registration│ │
│  └───────────┘  │
└─────────────────┘
```

---

## Data Model Design

### 1. Users Table

**Table Name**: `UsersTable`

**Primary Key**:
- Partition Key: `userId` (String)

**Attributes**:
```json
{
  "userId": "user-123",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "createdAt": "2024-12-15T10:30:00Z"
}
```

**Indexes**: None required

**Access Patterns**:
- Get user by userId (Primary Key)
- Create new user

---

### 2. Events Table (Enhanced)

**Table Name**: `EventsTable` (existing table)

**Primary Key**:
- Partition Key: `eventId` (String)

**New Attributes**:
```json
{
  "eventId": "event-123",
  "title": "Event Title",
  "description": "Event description",
  "date": "2024-12-15",
  "location": "Event Location",
  "capacity": 100,
  "currentAttendees": 85,
  "organizer": "Organizer Name",
  "status": "active",
  "hasWaitlist": true,
  "waitlistCapacity": 20
}
```

**Indexes**: Existing indexes remain unchanged

**Access Patterns**:
- Get event by eventId (Primary Key)
- Update currentAttendees count
- Check capacity and waitlist availability

---

### 3. Registrations Table

**Table Name**: `RegistrationsTable`

**Primary Key**:
- Partition Key: `registrationId` (String)

**Global Secondary Index 1 (GSI1)**:
- Name: `UserRegistrationsIndex`
- Partition Key: `userId` (String)
- Sort Key: `registeredAt` (String, ISO 8601 timestamp)
- Projection: ALL

**Global Secondary Index 2 (GSI2)**:
- Name: `EventRegistrationsIndex`
- Partition Key: `eventId` (String)
- Sort Key: `status#registeredAt` (String, composite: "confirmed#2024-12-15T10:30:00Z")
- Projection: ALL

**Attributes**:
```json
{
  "registrationId": "reg-456",
  "userId": "user-123",
  "eventId": "event-123",
  "status": "confirmed",
  "registeredAt": "2024-12-15T10:30:00Z",
  "waitlistPosition": null,
  "status#registeredAt": "confirmed#2024-12-15T10:30:00Z"
}
```

**Access Patterns**:
- Get registration by registrationId (Primary Key)
- Get all registrations for a user (GSI1: userId)
- Get all registrations for an event (GSI2: eventId)
- Get waitlisted registrations in order (GSI2: eventId + status)

---

## API Design

### Base URL
```
https://{api-id}.execute-api.{region}.amazonaws.com/prod
```

### Endpoints

#### 1. Create User
```
POST /users
```

**Request Body**:
```json
{
  "userId": "user-123",
  "name": "John Doe",
  "email": "john.doe@example.com"
}
```

**Success Response** (201 Created):
```json
{
  "userId": "user-123",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "createdAt": "2024-12-15T10:30:00Z"
}
```

**Error Responses**:
- 400: Validation error
- 409: User already exists

---

#### 2. Get User
```
GET /users/{userId}
```

**Success Response** (200 OK):
```json
{
  "userId": "user-123",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "createdAt": "2024-12-15T10:30:00Z"
}
```

**Error Responses**:
- 404: User not found

---

#### 3. Register for Event
```
POST /events/{eventId}/registrations
```

**Request Body**:
```json
{
  "userId": "user-123"
}
```

**Success Response - Confirmed** (201 Created):
```json
{
  "registrationId": "reg-456",
  "userId": "user-123",
  "eventId": "event-123",
  "status": "confirmed",
  "registeredAt": "2024-12-15T10:30:00Z"
}
```

**Success Response - Waitlisted** (201 Created):
```json
{
  "registrationId": "reg-789",
  "userId": "user-456",
  "eventId": "event-123",
  "status": "waitlisted",
  "registeredAt": "2024-12-15T11:00:00Z",
  "waitlistPosition": 5
}
```

**Error Responses**:
- 400: Validation error
- 404: Event or user not found
- 409: Event full, already registered, or event inactive

---

#### 4. Unregister from Event
```
DELETE /events/{eventId}/registrations/{userId}
```

**Success Response** (204 No Content)

**Error Responses**:
- 404: Registration not found

---

#### 5. List Event Registrations
```
GET /events/{eventId}/registrations?status={status}
```

**Query Parameters**:
- `status` (optional): Filter by status (confirmed, waitlisted)

**Success Response** (200 OK):
```json
{
  "eventId": "event-123",
  "registrations": [
    {
      "registrationId": "reg-456",
      "userId": "user-123",
      "userName": "John Doe",
      "status": "confirmed",
      "registeredAt": "2024-12-15T10:30:00Z"
    },
    {
      "registrationId": "reg-789",
      "userId": "user-456",
      "userName": "Jane Smith",
      "status": "waitlisted",
      "registeredAt": "2024-12-15T11:00:00Z",
      "waitlistPosition": 1
    }
  ]
}
```

**Error Responses**:
- 404: Event not found

---

#### 6. List User Registrations
```
GET /users/{userId}/registrations?status={status}
```

**Query Parameters**:
- `status` (optional): Filter by status (confirmed, waitlisted)

**Success Response** (200 OK):
```json
{
  "userId": "user-123",
  "registrations": [
    {
      "registrationId": "reg-456",
      "eventId": "event-123",
      "eventTitle": "Event Title",
      "status": "confirmed",
      "registeredAt": "2024-12-15T10:30:00Z"
    },
    {
      "registrationId": "reg-789",
      "eventId": "event-456",
      "eventTitle": "Another Event",
      "status": "waitlisted",
      "registeredAt": "2024-12-15T11:00:00Z",
      "waitlistPosition": 3
    }
  ]
}
```

**Error Responses**:
- 404: User not found

---

## Business Logic Design

### Registration Flow

```
┌─────────────────────────────────────────┐
│  POST /events/{eventId}/registrations   │
└───────────────┬─────────────────────────┘
                │
                ▼
        ┌───────────────┐
        │ Validate Input│
        └───────┬───────┘
                │
                ▼
        ┌───────────────┐
        │ Check User    │
        │ Exists        │
        └───────┬───────┘
                │
                ▼
        ┌───────────────┐
        │ Check Event   │
        │ Exists & Active│
        └───────┬───────┘
                │
                ▼
        ┌───────────────┐
        │ Check Already │
        │ Registered    │
        └───────┬───────┘
                │
                ▼
        ┌───────────────┐
        │ Check Capacity│
        └───────┬───────┘
                │
        ┌───────┴───────┐
        │               │
        ▼               ▼
┌──────────────┐  ┌──────────────┐
│ Available    │  │ Full         │
│ Capacity     │  │              │
└──────┬───────┘  └──────┬───────┘
       │                 │
       ▼                 ▼
┌──────────────┐  ┌──────────────┐
│ Create       │  │ Check        │
│ Confirmed    │  │ Waitlist     │
│ Registration │  │              │
└──────┬───────┘  └──────┬───────┘
       │                 │
       │          ┌──────┴──────┐
       │          │             │
       │          ▼             ▼
       │   ┌──────────┐  ┌──────────┐
       │   │ Waitlist │  │ No       │
       │   │ Available│  │ Waitlist │
       │   └────┬─────┘  └────┬─────┘
       │        │             │
       │        ▼             ▼
       │   ┌──────────┐  ┌──────────┐
       │   │ Create   │  │ Return   │
       │   │Waitlisted│  │ Error    │
       │   │Registration│ │ 409      │
       │   └────┬─────┘  └──────────┘
       │        │
       └────────┴────────┐
                         │
                         ▼
                ┌────────────────┐
                │ Increment      │
                │ currentAttendees│
                │ (if confirmed) │
                └────────┬───────┘
                         │
                         ▼
                ┌────────────────┐
                │ Return 201     │
                └────────────────┘
```

### Unregistration Flow

```
┌──────────────────────────────────────────────┐
│ DELETE /events/{eventId}/registrations/{userId}│
└───────────────┬──────────────────────────────┘
                │
                ▼
        ┌───────────────┐
        │ Find          │
        │ Registration  │
        └───────┬───────┘
                │
        ┌───────┴───────┐
        │               │
        ▼               ▼
┌──────────────┐  ┌──────────────┐
│ Confirmed    │  │ Waitlisted   │
└──────┬───────┘  └──────┬───────┘
       │                 │
       ▼                 ▼
┌──────────────┐  ┌──────────────┐
│ Delete       │  │ Delete       │
│ Registration │  │ Registration │
└──────┬───────┘  └──────┬───────┘
       │                 │
       ▼                 ▼
┌──────────────┐  ┌──────────────┐
│ Decrement    │  │ Update       │
│currentAttendees│ │ Waitlist    │
└──────┬───────┘  │ Positions    │
       │          └──────┬───────┘
       ▼                 │
┌──────────────┐         │
│ Check        │         │
│ Waitlist     │         │
└──────┬───────┘         │
       │                 │
┌──────┴──────┐          │
│             │          │
▼             ▼          │
┌────────┐  ┌────────┐  │
│Waitlist│  │No      │  │
│Exists  │  │Waitlist│  │
└───┬────┘  └───┬────┘  │
    │           │       │
    ▼           │       │
┌────────┐      │       │
│Promote │      │       │
│First   │      │       │
│User    │      │       │
└───┬────┘      │       │
    │           │       │
    └───────────┴───────┘
                │
                ▼
        ┌───────────────┐
        │ Return 204    │
        └───────────────┘
```

---

## Pydantic Models

### User Model
```python
class User(BaseModel):
    userId: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9-]+$')
    name: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    createdAt: Optional[str] = None
```

### Registration Request Model
```python
class RegistrationRequest(BaseModel):
    userId: str = Field(..., min_length=3, max_length=50)
```

### Registration Response Model
```python
class Registration(BaseModel):
    registrationId: str
    userId: str
    eventId: str
    status: Literal["confirmed", "waitlisted"]
    registeredAt: str
    waitlistPosition: Optional[int] = None
```

### Enhanced Event Model
```python
class Event(BaseModel):
    eventId: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    date: str
    location: str = Field(..., min_length=1)
    capacity: int = Field(..., gt=0)
    currentAttendees: int = Field(default=0, ge=0)
    organizer: str = Field(..., min_length=1)
    status: str = Field(default="draft")
    hasWaitlist: bool = Field(default=False)
    waitlistCapacity: Optional[int] = Field(None, gt=0)
```

---

## DynamoDB Operations

### Atomic Operations Using Transactions

#### Registration Transaction
```python
# TransactWriteItems for confirmed registration
[
    {
        'Put': {
            'TableName': 'RegistrationsTable',
            'Item': registration_item,
            'ConditionExpression': 'attribute_not_exists(registrationId)'
        }
    },
    {
        'Update': {
            'TableName': 'EventsTable',
            'Key': {'eventId': event_id},
            'UpdateExpression': 'SET currentAttendees = currentAttendees + :inc',
            'ConditionExpression': 'currentAttendees < capacity',
            'ExpressionAttributeValues': {':inc': 1}
        }
    }
]
```

#### Unregistration with Promotion Transaction
```python
# TransactWriteItems for unregistration with promotion
[
    {
        'Delete': {
            'TableName': 'RegistrationsTable',
            'Key': {'registrationId': registration_id}
        }
    },
    {
        'Update': {
            'TableName': 'RegistrationsTable',
            'Key': {'registrationId': promoted_registration_id},
            'UpdateExpression': 'SET #status = :confirmed, waitlistPosition = :null',
            'ExpressionAttributeNames': {'#status': 'status'},
            'ExpressionAttributeValues': {':confirmed': 'confirmed', ':null': None}
        }
    },
    {
        'Update': {
            'TableName': 'EventsTable',
            'Key': {'eventId': event_id},
            'UpdateExpression': 'SET currentAttendees = currentAttendees',
            # No change needed as we're swapping waitlist to confirmed
        }
    }
]
```

---

## Error Handling Strategy

### Error Response Structure
```python
class ErrorResponse(BaseModel):
    error: ErrorDetail

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: List[Dict[str, str]] = []
```

### Error Codes Mapping
```python
ERROR_CODES = {
    'USER_NOT_FOUND': (404, 'User does not exist'),
    'EVENT_NOT_FOUND': (404, 'Event does not exist'),
    'EVENT_FULL': (409, 'Event has reached capacity'),
    'WAITLIST_FULL': (409, 'Event and waitlist are both full'),
    'ALREADY_REGISTERED': (409, 'User is already registered for this event'),
    'NOT_REGISTERED': (404, 'User is not registered for this event'),
    'VALIDATION_ERROR': (400, 'Input validation failed'),
    'EVENT_INACTIVE': (409, 'Event is not active or is in the past'),
}
```

---

## Concurrency Handling

### Race Condition Prevention

1. **DynamoDB Transactions**: Use TransactWriteItems for atomic operations
2. **Conditional Expressions**: Ensure capacity checks are atomic
3. **Optimistic Locking**: Use version numbers if needed
4. **Idempotency**: Use registrationId to prevent duplicate registrations

### Example Conditional Expression
```python
ConditionExpression='currentAttendees < capacity AND attribute_exists(eventId)'
```

---

## Infrastructure Design (CDK)

### Lambda Functions
```typescript
// User management Lambda
const userHandler = new PythonFunction(this, 'UserHandler', {
  entry: 'backend',
  index: 'user_handler.py',
  handler: 'handler',
  runtime: Runtime.PYTHON_3_12,
  environment: {
    USERS_TABLE: usersTable.tableName,
  },
});

// Registration management Lambda
const registrationHandler = new PythonFunction(this, 'RegistrationHandler', {
  entry: 'backend',
  index: 'registration_handler.py',
  handler: 'handler',
  runtime: Runtime.PYTHON_3_12,
  environment: {
    USERS_TABLE: usersTable.tableName,
    EVENTS_TABLE: eventsTable.tableName,
    REGISTRATIONS_TABLE: registrationsTable.tableName,
  },
});
```

### DynamoDB Tables
```typescript
// Users Table
const usersTable = new Table(this, 'UsersTable', {
  partitionKey: { name: 'userId', type: AttributeType.STRING },
  billingMode: BillingMode.PAY_PER_REQUEST,
});

// Registrations Table with GSIs
const registrationsTable = new Table(this, 'RegistrationsTable', {
  partitionKey: { name: 'registrationId', type: AttributeType.STRING },
  billingMode: BillingMode.PAY_PER_REQUEST,
});

registrationsTable.addGlobalSecondaryIndex({
  indexName: 'UserRegistrationsIndex',
  partitionKey: { name: 'userId', type: AttributeType.STRING },
  sortKey: { name: 'registeredAt', type: AttributeType.STRING },
});

registrationsTable.addGlobalSecondaryIndex({
  indexName: 'EventRegistrationsIndex',
  partitionKey: { name: 'eventId', type: AttributeType.STRING },
  sortKey: { name: 'status#registeredAt', type: AttributeType.STRING },
});
```

---

## Security Considerations

1. **Input Validation**: Validate all inputs using Pydantic models
2. **SQL Injection Prevention**: Use parameterized queries (DynamoDB SDK handles this)
3. **CORS Configuration**: Maintain existing CORS settings
4. **Rate Limiting**: Consider API Gateway throttling
5. **Authentication**: Future enhancement (not in scope)

---

## Performance Optimization

1. **DynamoDB Indexes**: Use GSIs for efficient queries
2. **Batch Operations**: Use batch operations where possible
3. **Caching**: Consider caching event capacity information
4. **Connection Pooling**: Reuse DynamoDB connections in Lambda
5. **Cold Start Optimization**: Keep Lambda functions warm

---

## Monitoring and Logging

1. **CloudWatch Logs**: Log all operations
2. **CloudWatch Metrics**: Track registration rates, errors
3. **X-Ray Tracing**: Enable for debugging
4. **Alarms**: Set up alarms for error rates

---

## Deployment Strategy

1. **Phase 1**: Deploy new DynamoDB tables
2. **Phase 2**: Deploy Lambda functions
3. **Phase 3**: Update API Gateway routes
4. **Phase 4**: Test all endpoints
5. **Phase 5**: Monitor and optimize

---

## Backward Compatibility

- Existing event endpoints remain unchanged
- New fields added to events are optional
- Existing events work without registration features
- No breaking changes to current API
