"""
Event Management API with User Registration

A FastAPI-based REST API for managing events and user registrations with DynamoDB storage.
This module provides CRUD operations for events, users, and registrations with proper validation,
error handling, and CORS support.

The API is designed to run on AWS Lambda using the Mangum ASGI adapter
and stores data in Amazon DynamoDB.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
import os
import uuid
from mangum import Mangum

# Event Management API
app = FastAPI(title="Event Management API", version="2.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DynamoDB setup
dynamodb = boto3.resource('dynamodb')
events_table_name = os.environ.get('DYNAMODB_TABLE', 'EventsTable')
users_table_name = os.environ.get('USERS_TABLE', 'UsersTable')
registrations_table_name = os.environ.get('REGISTRATIONS_TABLE', 'RegistrationsTable')

events_table = dynamodb.Table(events_table_name)
users_table = dynamodb.Table(users_table_name)
registrations_table = dynamodb.Table(registrations_table_name)

# Pydantic models for Events
class Event(BaseModel):
    """Event model for creating and storing events."""
    eventId: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    date: str = Field(..., description="ISO format date")
    location: str = Field(..., min_length=1)
    capacity: int = Field(..., gt=0)
    currentAttendees: int = Field(default=0, ge=0)
    organizer: str = Field(..., min_length=1)
    status: str = Field(default="draft")
    hasWaitlist: bool = Field(default=False)
    waitlistCapacity: Optional[int] = Field(None, gt=0)
    
    class Config:
        extra = "allow"

class EventUpdate(BaseModel):
    """Event update model for partial updates."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    date: Optional[str] = None
    location: Optional[str] = Field(None, min_length=1)
    capacity: Optional[int] = Field(None, gt=0)
    organizer: Optional[str] = Field(None, min_length=1)
    status: Optional[str] = None
    hasWaitlist: Optional[bool] = None
    waitlistCapacity: Optional[int] = Field(None, gt=0)
    
    class Config:
        extra = "allow"

# Pydantic models for Users
class User(BaseModel):
    """User model for creating and storing users."""
    userId: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9-]+$')
    name: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    createdAt: Optional[str] = None

# Pydantic models for Registrations
class RegistrationRequest(BaseModel):
    """Registration request model."""
    userId: str = Field(..., min_length=3, max_length=50)

class Registration(BaseModel):
    """Registration response model."""
    registrationId: str
    userId: str
    eventId: str
    status: Literal["confirmed", "waitlisted"]
    registeredAt: str
    waitlistPosition: Optional[int] = None

# Helper functions
def get_current_timestamp():
    """Get current timestamp in ISO 8601 format."""
    return datetime.utcnow().isoformat() + "Z"

def check_user_exists(user_id: str) -> bool:
    """Check if a user exists in the database."""
    try:
        response = users_table.get_item(Key={'userId': user_id})
        return 'Item' in response
    except Exception:
        return False

def check_event_exists(event_id: str) -> Optional[dict]:
    """Check if an event exists and return it."""
    try:
        response = events_table.get_item(Key={'eventId': event_id})
        return response.get('Item')
    except Exception:
        return None

def check_already_registered(user_id: str, event_id: str) -> bool:
    """Check if user is already registered for an event."""
    try:
        response = registrations_table.query(
            IndexName='UserRegistrationsIndex',
            KeyConditionExpression=Key('userId').eq(user_id)
        )
        registrations = response.get('Items', [])
        return any(r['eventId'] == event_id for r in registrations)
    except Exception:
        return False

def get_waitlist_count(event_id: str) -> int:
    """Get the current waitlist count for an event."""
    try:
        response = registrations_table.query(
            IndexName='EventRegistrationsIndex',
            KeyConditionExpression=Key('eventId').eq(event_id),
            FilterExpression='#status = :waitlisted',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':waitlisted': 'waitlisted'}
        )
        return len(response.get('Items', []))
    except Exception:
        return 0

def get_next_waitlist_position(event_id: str) -> int:
    """Get the next waitlist position for an event."""
    try:
        response = registrations_table.query(
            IndexName='EventRegistrationsIndex',
            KeyConditionExpression=Key('eventId').eq(event_id),
            FilterExpression='#status = :waitlisted',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':waitlisted': 'waitlisted'}
        )
        items = response.get('Items', [])
        if not items:
            return 1
        max_position = max(item.get('waitlistPosition', 0) for item in items)
        return max_position + 1
    except Exception:
        return 1

def get_first_waitlisted_user(event_id: str) -> Optional[dict]:
    """Get the first user on the waitlist."""
    try:
        response = registrations_table.query(
            IndexName='EventRegistrationsIndex',
            KeyConditionExpression=Key('eventId').eq(event_id),
            FilterExpression='#status = :waitlisted',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':waitlisted': 'waitlisted'}
        )
        items = response.get('Items', [])
        if not items:
            return None
        # Sort by waitlistPosition and return first
        sorted_items = sorted(items, key=lambda x: x.get('waitlistPosition', 999))
        return sorted_items[0] if sorted_items else None
    except Exception:
        return None

def update_waitlist_positions(event_id: str):
    """Update waitlist positions after a change."""
    try:
        response = registrations_table.query(
            IndexName='EventRegistrationsIndex',
            KeyConditionExpression=Key('eventId').eq(event_id),
            FilterExpression='#status = :waitlisted',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':waitlisted': 'waitlisted'}
        )
        items = response.get('Items', [])
        # Sort by registeredAt to maintain order
        sorted_items = sorted(items, key=lambda x: x.get('registeredAt', ''))
        
        # Update positions
        for index, item in enumerate(sorted_items, start=1):
            if item.get('waitlistPosition') != index:
                registrations_table.update_item(
                    Key={'registrationId': item['registrationId']},
                    UpdateExpression='SET waitlistPosition = :pos',
                    ExpressionAttributeValues={':pos': index}
                )
    except Exception as e:
        print(f"Error updating waitlist positions: {str(e)}")

# Root endpoints
@app.get("/")
async def root():
    """Root endpoint that returns a welcome message."""
    return {"message": "Event Management API with User Registration", "version": "2.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint to verify API status."""
    return {"status": "healthy", "message": "API is running"}

# Event endpoints
@app.post("/events", status_code=201)
async def create_event(event: Event):
    """Create a new event."""
    try:
        event_id = event.eventId if event.eventId else str(uuid.uuid4())
        event_data = event.dict(exclude_unset=True)
        event_data['eventId'] = event_id
        event_data['currentAttendees'] = 0
        
        if 'capacity' in event_data:
            event_data['capacity'] = int(event_data['capacity'])
        
        events_table.put_item(Item=event_data)
        return event_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create event: {str(e)}")

@app.get("/events")
async def list_events(status: Optional[str] = None):
    """List all events or filter by status."""
    try:
        response = events_table.scan()
        events = response.get('Items', [])
        
        if status:
            events = [e for e in events if e.get('status') == status]
        
        return {"events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list events: {str(e)}")

@app.get("/events/{event_id}")
async def get_event(event_id: str):
    """Retrieve a specific event by ID."""
    try:
        response = events_table.get_item(Key={'eventId': event_id})
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="Event not found")
        return response['Item']
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get event: {str(e)}")

@app.put("/events/{event_id}")
async def update_event(event_id: str, event_update: EventUpdate):
    """Update an existing event."""
    try:
        response = events_table.get_item(Key={'eventId': event_id})
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="Event not found")
        
        update_data = {k: v for k, v in event_update.dict(exclude_unset=True).items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        if 'capacity' in update_data:
            update_data['capacity'] = int(update_data['capacity'])
        
        update_expression = "SET " + ", ".join([f"#{k} = :{k}" for k in update_data.keys()])
        expression_attribute_names = {f"#{k}": k for k in update_data.keys()}
        expression_attribute_values = {f":{k}": v for k, v in update_data.items()}
        
        response = events_table.update_item(
            Key={'eventId': event_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="ALL_NEW"
        )
        return response['Attributes']
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update event: {str(e)}")

@app.delete("/events/{event_id}", status_code=204)
async def delete_event(event_id: str):
    """Delete an event."""
    try:
        response = events_table.get_item(Key={'eventId': event_id})
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="Event not found")
        
        events_table.delete_item(Key={'eventId': event_id})
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete event: {str(e)}")

# User endpoints
@app.post("/users", status_code=201)
async def create_user(user: User):
    """Create a new user."""
    try:
        # Check if user already exists
        if check_user_exists(user.userId):
            raise HTTPException(status_code=409, detail={
                "error": {
                    "code": "USER_ALREADY_EXISTS",
                    "message": "User with this userId already exists"
                }
            })
        
        user_data = user.dict(exclude_unset=True)
        user_data['createdAt'] = get_current_timestamp()
        
        users_table.put_item(Item=user_data)
        return user_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    """Retrieve a specific user by ID."""
    try:
        response = users_table.get_item(Key={'userId': user_id})
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail={
                "error": {
                    "code": "USER_NOT_FOUND",
                    "message": "User does not exist"
                }
            })
        return response['Item']
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")

# Registration endpoints
@app.post("/events/{event_id}/registrations", status_code=201)
async def register_for_event(event_id: str, registration_request: RegistrationRequest):
    """Register a user for an event."""
    try:
        user_id = registration_request.userId
        
        # Validate user exists
        if not check_user_exists(user_id):
            raise HTTPException(status_code=404, detail={
                "error": {
                    "code": "USER_NOT_FOUND",
                    "message": "User does not exist"
                }
            })
        
        # Validate event exists and get event data
        event = check_event_exists(event_id)
        if not event:
            raise HTTPException(status_code=404, detail={
                "error": {
                    "code": "EVENT_NOT_FOUND",
                    "message": "Event does not exist"
                }
            })
        
        # Check if event is active
        if event.get('status') != 'active':
            raise HTTPException(status_code=409, detail={
                "error": {
                    "code": "EVENT_INACTIVE",
                    "message": "Event is not active or is in the past"
                }
            })
        
        # Check if already registered
        if check_already_registered(user_id, event_id):
            raise HTTPException(status_code=409, detail={
                "error": {
                    "code": "ALREADY_REGISTERED",
                    "message": "User is already registered for this event"
                }
            })
        
        # Check capacity
        current_attendees = event.get('currentAttendees', 0)
        capacity = event.get('capacity', 0)
        has_waitlist = event.get('hasWaitlist', False)
        waitlist_capacity = event.get('waitlistCapacity')
        
        registration_id = str(uuid.uuid4())
        registered_at = get_current_timestamp()
        
        # Case 1: Available capacity
        if current_attendees < capacity:
            registration_data = {
                'registrationId': registration_id,
                'userId': user_id,
                'eventId': event_id,
                'status': 'confirmed',
                'registeredAt': registered_at,
                'statusRegisteredAt': f"confirmed#{registered_at}"
            }
            
            # Use transaction to ensure atomicity
            try:
                dynamodb.meta.client.transact_write_items(
                    TransactItems=[
                        {
                            'Put': {
                                'TableName': registrations_table_name,
                                'Item': {k: {'S': str(v)} if isinstance(v, str) else {'N': str(v)} if isinstance(v, (int, float)) else {'S': str(v)} for k, v in registration_data.items()},
                                'ConditionExpression': 'attribute_not_exists(registrationId)'
                            }
                        },
                        {
                            'Update': {
                                'TableName': events_table_name,
                                'Key': {'eventId': {'S': event_id}},
                                'UpdateExpression': 'SET currentAttendees = currentAttendees + :inc',
                                'ConditionExpression': 'currentAttendees < capacity',
                                'ExpressionAttributeValues': {':inc': {'N': '1'}}
                            }
                        }
                    ]
                )
            except ClientError as e:
                if e.response['Error']['Code'] == 'TransactionCanceledException':
                    # Capacity was reached, try waitlist
                    if not has_waitlist:
                        raise HTTPException(status_code=409, detail={
                            "error": {
                                "code": "EVENT_FULL",
                                "message": "Event has reached capacity"
                            }
                        })
                    # Fall through to waitlist logic
                else:
                    raise
            else:
                return registration_data
        
        # Case 2 & 3: Event full, check waitlist
        if not has_waitlist:
            raise HTTPException(status_code=409, detail={
                "error": {
                    "code": "EVENT_FULL",
                    "message": "Event has reached capacity"
                }
            })
        
        # Check waitlist capacity
        waitlist_count = get_waitlist_count(event_id)
        if waitlist_capacity and waitlist_count >= waitlist_capacity:
            raise HTTPException(status_code=409, detail={
                "error": {
                    "code": "WAITLIST_FULL",
                    "message": "Event and waitlist are both full"
                }
            })
        
        # Add to waitlist
        waitlist_position = get_next_waitlist_position(event_id)
        registration_data = {
            'registrationId': registration_id,
            'userId': user_id,
            'eventId': event_id,
            'status': 'waitlisted',
            'registeredAt': registered_at,
            'waitlistPosition': waitlist_position,
            'statusRegisteredAt': f"waitlisted#{registered_at}"
        }
        
        registrations_table.put_item(Item=registration_data)
        return registration_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register for event: {str(e)}")

@app.delete("/events/{event_id}/registrations/{user_id}", status_code=204)
async def unregister_from_event(event_id: str, user_id: str):
    """Unregister a user from an event."""
    try:
        # Find the registration
        response = registrations_table.query(
            IndexName='UserRegistrationsIndex',
            KeyConditionExpression=Key('userId').eq(user_id)
        )
        
        registrations = [r for r in response.get('Items', []) if r['eventId'] == event_id]
        if not registrations:
            raise HTTPException(status_code=404, detail={
                "error": {
                    "code": "NOT_REGISTERED",
                    "message": "User is not registered for this event"
                }
            })
        
        registration = registrations[0]
        registration_id = registration['registrationId']
        status = registration['status']
        
        # Delete the registration
        registrations_table.delete_item(Key={'registrationId': registration_id})
        
        # If confirmed, decrement attendees and promote from waitlist
        if status == 'confirmed':
            events_table.update_item(
                Key={'eventId': event_id},
                UpdateExpression='SET currentAttendees = currentAttendees - :dec',
                ExpressionAttributeValues={':dec': 1}
            )
            
            # Check for waitlisted users to promote
            first_waitlisted = get_first_waitlisted_user(event_id)
            if first_waitlisted:
                # Promote first waitlisted user
                registrations_table.update_item(
                    Key={'registrationId': first_waitlisted['registrationId']},
                    UpdateExpression='SET #status = :confirmed, statusRegisteredAt = :statusReg REMOVE waitlistPosition',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':confirmed': 'confirmed',
                        ':statusReg': f"confirmed#{first_waitlisted['registeredAt']}"
                    }
                )
                
                # Increment attendees
                events_table.update_item(
                    Key={'eventId': event_id},
                    UpdateExpression='SET currentAttendees = currentAttendees + :inc',
                    ExpressionAttributeValues={':inc': 1}
                )
                
                # Update remaining waitlist positions
                update_waitlist_positions(event_id)
        
        # If waitlisted, update positions
        elif status == 'waitlisted':
            update_waitlist_positions(event_id)
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to unregister from event: {str(e)}")

@app.get("/users/{user_id}/registrations")
async def list_user_registrations(user_id: str, status: Optional[str] = Query(None)):
    """List all registrations for a user."""
    try:
        # Check if user exists
        if not check_user_exists(user_id):
            raise HTTPException(status_code=404, detail={
                "error": {
                    "code": "USER_NOT_FOUND",
                    "message": "User does not exist"
                }
            })
        
        # Query registrations
        response = registrations_table.query(
            IndexName='UserRegistrationsIndex',
            KeyConditionExpression=Key('userId').eq(user_id)
        )
        
        registrations = response.get('Items', [])
        
        # Filter by status if provided
        if status:
            registrations = [r for r in registrations if r.get('status') == status]
        
        # Fetch event details for each registration
        for reg in registrations:
            event = check_event_exists(reg['eventId'])
            if event:
                reg['eventTitle'] = event.get('title', '')
        
        return {
            "userId": user_id,
            "registrations": registrations
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list user registrations: {str(e)}")

@app.get("/events/{event_id}/registrations")
async def list_event_registrations(event_id: str, status: Optional[str] = Query(None)):
    """List all registrations for an event."""
    try:
        # Check if event exists
        if not check_event_exists(event_id):
            raise HTTPException(status_code=404, detail={
                "error": {
                    "code": "EVENT_NOT_FOUND",
                    "message": "Event does not exist"
                }
            })
        
        # Query registrations
        response = registrations_table.query(
            IndexName='EventRegistrationsIndex',
            KeyConditionExpression=Key('eventId').eq(event_id)
        )
        
        registrations = response.get('Items', [])
        
        # Filter by status if provided
        if status:
            registrations = [r for r in registrations if r.get('status') == status]
        
        # Sort waitlisted by position
        if status == 'waitlisted' or not status:
            registrations.sort(key=lambda x: (x.get('status') != 'waitlisted', x.get('waitlistPosition', 999)))
        
        # Fetch user details for each registration
        for reg in registrations:
            user_response = users_table.get_item(Key={'userId': reg['userId']})
            if 'Item' in user_response:
                reg['userName'] = user_response['Item'].get('name', '')
        
        return {
            "eventId": event_id,
            "registrations": registrations
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list event registrations: {str(e)}")

# Lambda handler
handler = Mangum(app)
