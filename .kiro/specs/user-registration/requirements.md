# User Registration Feature - Requirements

## Overview
Define the requirements for implementing a user registration system that allows users to register for events with capacity management and waitlist functionality.

## Functional Requirements

### FR1: User Management
**Priority**: High  
**Status**: Not Started

#### FR1.1: User Creation
- Users can be created with basic information
- Required fields:
  - `userId`: Unique identifier (string, 3-50 characters)
  - `name`: User's full name (string, 1-100 characters)
- Optional fields:
  - `email`: User's email address (valid email format)
  - `createdAt`: Timestamp of creation (ISO 8601 format, auto-generated)

#### FR1.2: User Retrieval
- Users can be retrieved by their userId
- Return user information including all registered events

**Acceptance Criteria**:
- [ ] POST /users endpoint creates a new user
- [ ] GET /users/{userId} endpoint retrieves user information
- [ ] userId must be unique across the system
- [ ] Name field is required and validated
- [ ] Email format is validated if provided

---

### FR2: Event Capacity Management
**Priority**: High  
**Status**: Not Started

#### FR2.1: Capacity Configuration
- Events must support capacity constraints
- Required fields:
  - `capacity`: Maximum number of attendees (positive integer)
  - `currentAttendees`: Current number of registered users (integer, default: 0)
  - `hasWaitlist`: Boolean flag to enable/disable waitlist (default: false)
  - `waitlistCapacity`: Maximum waitlist size (optional, positive integer or unlimited)

#### FR2.2: Capacity Tracking
- System must track current number of attendees
- System must prevent exceeding capacity limits
- System must update attendee count on registration/unregistration

**Acceptance Criteria**:
- [ ] Events can be created with capacity constraints
- [ ] currentAttendees is automatically managed
- [ ] Capacity cannot be exceeded for confirmed registrations
- [ ] Waitlist capacity is enforced when enabled

---

### FR3: Event Registration
**Priority**: High  
**Status**: Not Started

#### FR3.1: Registration Logic
Users can register for events with the following behavior:

**Case 1: Available Capacity**
- User is added to the event's attendee list
- Registration status: `confirmed`
- currentAttendees is incremented
- Return: 201 Created with registration details

**Case 2: Event Full, No Waitlist**
- Registration is denied
- Return: 409 Conflict with error message "Event is full"

**Case 3: Event Full, Waitlist Available**
- User is added to the waitlist
- Registration status: `waitlisted`
- User receives waitlist position
- Return: 201 Created with waitlist details

**Case 4: Event and Waitlist Full**
- Registration is denied
- Return: 409 Conflict with error message "Event and waitlist are full"

#### FR3.2: Registration Constraints
- A user cannot register for the same event twice
- A user cannot register for past events
- Only active events accept registrations
- User must exist in the system

**Acceptance Criteria**:
- [ ] POST /events/{eventId}/registrations endpoint handles all registration cases
- [ ] Confirmed registrations increment currentAttendees
- [ ] Waitlisted registrations assign correct position
- [ ] Duplicate registrations are prevented
- [ ] Past events reject registrations
- [ ] Proper error messages for each failure case

---

### FR4: Event Unregistration
**Priority**: High  
**Status**: Not Started

#### FR4.1: Unregistration Logic
Users can unregister from events with the following behavior:

**Case 1: Confirmed Registration**
- User is removed from attendee list
- currentAttendees is decremented
- If waitlist exists and has users:
  - First user in waitlist is automatically promoted to confirmed
  - Waitlist positions are updated for remaining users
- Return: 204 No Content

**Case 2: Waitlisted Registration**
- User is removed from waitlist
- Waitlist positions are updated for remaining users
- Return: 204 No Content

**Case 3: Not Registered**
- Return: 404 Not Found with error message "User is not registered for this event"

**Acceptance Criteria**:
- [ ] DELETE /events/{eventId}/registrations/{userId} endpoint handles unregistration
- [ ] Confirmed unregistration decrements currentAttendees
- [ ] Waitlisted users are automatically promoted when space available
- [ ] Waitlist positions are recalculated correctly
- [ ] Returns 404 for non-existent registrations

---

### FR5: User's Registered Events List
**Priority**: Medium  
**Status**: Not Started

#### FR5.1: List User Registrations
- Users can retrieve a list of all events they are registered for
- Include both confirmed and waitlisted registrations
- Include registration details:
  - Registration ID
  - Event ID and title
  - Registration status (confirmed/waitlisted)
  - Registration timestamp
  - Waitlist position (if applicable)

#### FR5.2: Filtering
- Optional filter by registration status (confirmed, waitlisted)

**Acceptance Criteria**:
- [ ] GET /users/{userId}/registrations endpoint returns all user registrations
- [ ] Response includes event details for each registration
- [ ] Status filter works correctly
- [ ] Waitlist position is included for waitlisted registrations
- [ ] Returns empty array if user has no registrations

---

### FR6: Event Registrations List
**Priority**: Low  
**Status**: Not Started

#### FR6.1: List Event Registrations
- Retrieve all registrations for a specific event
- Include both confirmed and waitlisted registrations
- Useful for event organizers/administrators

#### FR6.2: Filtering
- Optional filter by registration status (confirmed, waitlisted)

**Acceptance Criteria**:
- [ ] GET /events/{eventId}/registrations endpoint returns all event registrations
- [ ] Response includes user details for each registration
- [ ] Status filter works correctly
- [ ] Waitlist order is maintained

---

## Non-Functional Requirements

### NFR1: Performance
- Registration operations must complete within 2 seconds
- List operations must complete within 1 second
- Support concurrent registrations without race conditions

### NFR2: Data Consistency
- Use DynamoDB transactions for atomic operations
- Implement optimistic locking to prevent race conditions
- Ensure currentAttendees count is always accurate

### NFR3: Scalability
- System must handle 1000+ concurrent users
- Support events with 10,000+ capacity
- Efficient querying using DynamoDB indexes

### NFR4: Security
- Validate all input data
- Prevent SQL injection and other attacks
- Follow API security best practices

### NFR5: API Standards
- Follow REST API conventions defined in `.kiro/steering/api-standards.md`
- Use standard HTTP status codes
- Return consistent JSON response formats
- Provide clear error messages

---

## Business Rules

### BR1: Capacity Enforcement
- currentAttendees must never exceed capacity
- Waitlist size must not exceed waitlistCapacity (if set)
- Capacity changes do not affect existing registrations

### BR2: Waitlist Management
- Waitlist positions start at 1
- Positions are sequential with no gaps
- When a confirmed user unregisters, first waitlisted user is automatically promoted
- Waitlist positions are recalculated after any waitlist change

### BR3: Registration Constraints
- One registration per user per event
- No registrations for past events
- Only active events accept registrations
- Users must exist before registering

### BR4: Automatic Promotion
- Promotion happens immediately upon unregistration
- Promoted users maintain their registration timestamp
- Only the first waitlisted user is promoted per unregistration

---

## Data Requirements

### DR1: User Data
- Store user information persistently
- userId must be unique
- Support efficient lookup by userId

### DR2: Event Data
- Extend existing event data model with capacity fields
- Track current attendee count
- Store waitlist configuration

### DR3: Registration Data
- Store registration information persistently
- Support efficient queries by userId
- Support efficient queries by eventId
- Maintain registration order for waitlist

---

## Integration Requirements

### IR1: Existing Event API
- Integrate with existing event management endpoints
- Extend event data model without breaking existing functionality
- Maintain backward compatibility

### IR2: DynamoDB
- Use existing DynamoDB infrastructure
- Create new tables for users and registrations
- Use Global Secondary Indexes for efficient queries

### IR3: AWS Lambda
- Deploy as serverless functions
- Use existing Lambda infrastructure
- Integrate with API Gateway

---

## Validation Requirements

### VR1: User Validation
- userId: Required, unique, 3-50 characters, alphanumeric and hyphens
- name: Required, 1-100 characters
- email: Optional, valid email format

### VR2: Registration Validation
- userId must exist in Users table
- eventId must exist in Events table
- Event must be active
- Event date must be in the future

### VR3: Capacity Validation
- capacity: Must be positive integer
- currentAttendees: Must be >= 0 and <= capacity
- waitlistCapacity: If set, must be positive integer

---

## Error Handling Requirements

### EH1: Error Response Format
All errors must follow the standard format:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": []
  }
}
```

### EH2: Error Codes
- USER_NOT_FOUND: User does not exist
- EVENT_NOT_FOUND: Event does not exist
- EVENT_FULL: Event has reached capacity
- WAITLIST_FULL: Event and waitlist are both full
- ALREADY_REGISTERED: User is already registered
- NOT_REGISTERED: User is not registered
- VALIDATION_ERROR: Input validation failed
- EVENT_INACTIVE: Event is not active or is in the past

---

## Testing Requirements

### TR1: Unit Tests
- Test all registration logic cases
- Test waitlist promotion logic
- Test validation rules
- Test error handling

### TR2: Integration Tests
- Test end-to-end registration flow
- Test concurrent registrations
- Test DynamoDB operations
- Test API endpoints

### TR3: Test Scenarios
1. Successful registration with available capacity
2. Waitlist registration when event is full
3. Automatic promotion from waitlist
4. Full event and waitlist rejection
5. List user registrations
6. Concurrent registration handling

---

## Success Criteria

The feature is considered complete when:
- [ ] All functional requirements are implemented
- [ ] All acceptance criteria are met
- [ ] All API endpoints are working correctly
- [ ] All test scenarios pass
- [ ] API follows REST standards
- [ ] Error handling is comprehensive
- [ ] Documentation is complete
- [ ] Code is deployed to AWS

---

## Out of Scope

The following are explicitly out of scope for this feature:
- Email notifications for registrations
- Payment processing
- Group registrations
- Priority waitlist
- Registration deadlines
- Event reminders
- User authentication/authorization
- Admin dashboard
