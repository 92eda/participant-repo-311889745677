# User Registration Feature Specification

## Overview
This specification defines the user registration system for events, including user management, event capacity constraints, waitlist functionality, and registration management.

## Status
- **Current Phase**: Requirements & Design
- **Implementation Status**: Not Started
- **Last Updated**: 2026-02-06

## Functional Requirements

### 1. User Management

#### 1.1 User Creation
- Users can be created with basic information
- Required fields:
  - `userId`: Unique identifier for the user (string)
  - `name`: User's full name (string)
- Optional fields:
  - `email`: User's email address (string)
  - `createdAt`: Timestamp of user creation (ISO 8601 format)

#### 1.2 User Data Model
```json
{
  "userId": "user-123",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "createdAt": "2024-12-15T10:30:00Z"
}
```

### 2. Event Capacity Management

#### 2.1 Capacity Configuration
- Events must support capacity constraints
- Required fields for capacity management:
  - `capacity`: Maximum number of attendees (positive integer)
  - `currentAttendees`: Current number of registered users (integer, default: 0)
  - `hasWaitlist`: Boolean flag to enable/disable waitlist (default: false)
  - `waitlistCapacity`: Maximum waitlist size (optional, positive integer or unlimited)

#### 2.2 Enhanced Event Data Model
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

### 3. Event Registration

#### 3.1 Registration Process
Users can register for events with the following logic:

**Case 1: Event has available capacity**
- User is added to the event's attendee list
- `currentAttendees` is incremented
- Registration status: `confirmed`

**Case 2: Event is full, no waitlist**
- Registration is denied
- Return error: "Event is full"
- HTTP Status: 409 Conflict

**Case 3: Event is full, waitlist enabled and available**
- User is added to the waitlist
- Registration status: `waitlisted`
- User receives waitlist position

**Case 4: Event is full, waitlist is also full**
- Registration is denied
- Return error: "Event and waitlist are full"
- HTTP Status: 409 Conflict

#### 3.2 Registration Data Model
```json
{
  "registrationId": "reg-456",
  "userId": "user-123",
  "eventId": "event-123",
  "status": "confirmed",
  "registeredAt": "2024-12-15T10:30:00Z",
  "waitlistPosition": null
}
```

For waitlisted users:
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

### 4. Event Unregistration

#### 4.1 Unregistration Process
Users can unregister from events with the following logic:

**Case 1: User has confirmed registration**
- User is removed from attendee list
- `currentAttendees` is decremented
- If waitlist exists and has users:
  - First user in waitlist is promoted to confirmed
  - Waitlist positions are updated for remaining users

**Case 2: User is on waitlist**
- User is removed from waitlist
- Waitlist positions are updated for remaining users

**Case 3: User is not registered**
- Return error: "User is not registered for this event"
- HTTP Status: 404 Not Found

### 5. User's Registered Events List

#### 5.1 List User Registrations
Users can retrieve a list of all events they are registered for, including:
- Confirmed registrations
- Waitlisted registrations
- Registration details (status, date, waitlist position if applicable)

#### 5.2 Response Format
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

## API Endpoints

### User Management

#### POST /users
Create a new user
- **Request Body**:
  ```json
  {
    "userId": "user-123",
    "name": "John Doe",
    "email": "john.doe@example.com"
  }
  ```
- **Response**: 201 Created
- **Error Cases**: 400 (validation error), 409 (user already exists)

#### GET /users/{userId}
Retrieve user information
- **Response**: 200 OK
- **Error Cases**: 404 (user not found)

### Event Registration

#### POST /events/{eventId}/registrations
Register a user for an event
- **Request Body**:
  ```json
  {
    "userId": "user-123"
  }
  ```
- **Response**: 201 Created (confirmed) or 201 Created (waitlisted)
- **Error Cases**: 
  - 400 (validation error)
  - 404 (event or user not found)
  - 409 (event full, already registered)

#### DELETE /events/{eventId}/registrations/{userId}
Unregister a user from an event
- **Response**: 204 No Content
- **Error Cases**: 
  - 404 (registration not found)

#### GET /events/{eventId}/registrations
List all registrations for an event (admin/organizer)
- **Query Parameters**: 
  - `status`: Filter by status (confirmed, waitlisted)
- **Response**: 200 OK
- **Error Cases**: 404 (event not found)

### User Registrations

#### GET /users/{userId}/registrations
List all events a user is registered for
- **Query Parameters**: 
  - `status`: Filter by status (confirmed, waitlisted)
- **Response**: 200 OK
- **Error Cases**: 404 (user not found)

## Data Storage

### DynamoDB Tables

#### Users Table
- **Primary Key**: `userId` (String)
- **Attributes**: name, email, createdAt

#### Events Table (Enhanced)
- **Primary Key**: `eventId` (String)
- **Attributes**: title, description, date, location, capacity, currentAttendees, organizer, status, hasWaitlist, waitlistCapacity

#### Registrations Table
- **Primary Key**: `registrationId` (String)
- **GSI 1**: `userId` (Partition Key), `registeredAt` (Sort Key)
- **GSI 2**: `eventId` (Partition Key), `status` (Sort Key)
- **Attributes**: userId, eventId, status, registeredAt, waitlistPosition

## Business Rules

1. **Capacity Enforcement**
   - `currentAttendees` must never exceed `capacity`
   - Waitlist size must not exceed `waitlistCapacity` (if set)

2. **Waitlist Management**
   - Waitlist positions start at 1
   - When a confirmed user unregisters, first waitlisted user is automatically promoted
   - Waitlist positions are recalculated after any waitlist change

3. **Registration Constraints**
   - A user cannot register for the same event twice
   - A user cannot register for past events
   - Only active events accept registrations

4. **Automatic Promotion**
   - When capacity becomes available, waitlisted users are promoted in order
   - Promoted users should be notified (future enhancement)

## Validation Rules

### User Creation
- `userId`: Required, unique, 3-50 characters
- `name`: Required, 1-100 characters
- `email`: Optional, valid email format

### Event Registration
- `userId`: Must exist in Users table
- `eventId`: Must exist in Events table
- Event must be active and not in the past

### Event Capacity
- `capacity`: Must be positive integer
- `currentAttendees`: Must be >= 0 and <= capacity
- `waitlistCapacity`: If set, must be positive integer

## Error Handling

All errors follow the API standards defined in `.kiro/steering/api-standards.md`:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": []
  }
}
```

### Common Error Codes
- `USER_NOT_FOUND`: User does not exist
- `EVENT_NOT_FOUND`: Event does not exist
- `EVENT_FULL`: Event has reached capacity
- `WAITLIST_FULL`: Event and waitlist are both full
- `ALREADY_REGISTERED`: User is already registered for this event
- `NOT_REGISTERED`: User is not registered for this event
- `VALIDATION_ERROR`: Input validation failed
- `EVENT_INACTIVE`: Event is not active or is in the past

## Testing Scenarios

### Scenario 1: Successful Registration
1. Create user
2. Create event with capacity 2
3. Register user 1 → Success (confirmed)
4. Register user 2 → Success (confirmed)
5. Verify currentAttendees = 2

### Scenario 2: Waitlist Registration
1. Create event with capacity 2, waitlist enabled
2. Register user 1 → Success (confirmed)
3. Register user 2 → Success (confirmed)
4. Register user 3 → Success (waitlisted, position 1)
5. Register user 4 → Success (waitlisted, position 2)

### Scenario 3: Automatic Promotion
1. Setup: Event full, user on waitlist
2. Confirmed user unregisters
3. Verify: Waitlisted user promoted to confirmed
4. Verify: Waitlist positions updated

### Scenario 4: Full Event and Waitlist
1. Create event with capacity 2, waitlist capacity 1
2. Register 3 users (2 confirmed, 1 waitlisted)
3. Register 4th user → Error (event and waitlist full)

### Scenario 5: List User Registrations
1. User registers for multiple events
2. Retrieve user's registrations
3. Verify all registrations returned with correct status

## Future Enhancements

1. **Notifications**
   - Email notifications for registration confirmation
   - Notifications when promoted from waitlist
   - Reminders before event date

2. **Priority Waitlist**
   - VIP or priority users get preference
   - Early bird registration periods

3. **Group Registrations**
   - Register multiple users at once
   - Group capacity management

4. **Registration Deadlines**
   - Close registration before event date
   - Automatic waitlist closure

## Implementation Notes

- Use DynamoDB transactions for atomic operations (registration/unregistration)
- Implement optimistic locking to prevent race conditions
- Consider using DynamoDB Streams for automatic promotion logic
- Cache frequently accessed event capacity information
- Implement proper indexing for efficient queries

## Dependencies

- Existing Event Management API
- DynamoDB for data storage
- AWS Lambda for serverless compute
- API Gateway for HTTP endpoints

## Success Criteria

- [ ] Users can be created with userId and name
- [ ] Events support capacity constraints
- [ ] Events support optional waitlist
- [ ] Users can register for events
- [ ] Full events deny registration (no waitlist)
- [ ] Full events add users to waitlist (with waitlist)
- [ ] Users can unregister from events
- [ ] Waitlisted users are promoted when capacity available
- [ ] Users can list their registered events
- [ ] All API endpoints follow REST standards
- [ ] All responses follow JSON format standards
- [ ] Proper error handling and validation
