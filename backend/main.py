"""
Event Management API

A FastAPI-based REST API for managing events with DynamoDB storage.
This module provides CRUD operations for events with proper validation,
error handling, and CORS support.

The API is designed to run on AWS Lambda using the Mangum ASGI adapter
and stores data in Amazon DynamoDB.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key
import os
import uuid
from mangum import Mangum

# Event Management API - Updated for test requirements
app = FastAPI(title="Event Management API", version="1.0.0")

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
table_name = os.environ.get('DYNAMODB_TABLE', 'EventsTable')
table = dynamodb.Table(table_name)

# Pydantic models
class Event(BaseModel):
    """
    Event model for creating and storing events.
    
    Attributes:
        eventId: Unique identifier for the event (optional, auto-generated if not provided)
        title: Event title (1-200 characters)
        description: Detailed description of the event
        date: Event date in ISO format
        location: Event location
        capacity: Maximum number of attendees (positive integer)
        organizer: Name of the event organizer
        status: Event status (defaults to "draft")
    """
    eventId: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    date: str = Field(..., description="ISO format date")
    location: str = Field(..., min_length=1)
    capacity: int = Field(..., gt=0)
    organizer: str = Field(..., min_length=1)
    status: str = Field(default="draft")
    
    class Config:
        extra = "allow"  # Allow extra fields

class EventUpdate(BaseModel):
    """
    Event update model for partial updates.
    
    All fields are optional to allow partial updates.
    
    Attributes:
        title: Updated event title (1-200 characters)
        description: Updated event description
        date: Updated event date in ISO format
        location: Updated event location
        capacity: Updated maximum number of attendees (positive integer)
        organizer: Updated event organizer name
        status: Updated event status
    """
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    date: Optional[str] = None
    location: Optional[str] = Field(None, min_length=1)
    capacity: Optional[int] = Field(None, gt=0)
    organizer: Optional[str] = Field(None, min_length=1)
    status: Optional[str] = None
    
    class Config:
        extra = "allow"  # Allow extra fields

@app.get("/")
async def root():
    """
    Root endpoint that returns a welcome message.
    
    Returns:
        dict: Welcome message with API information
    """
    return {"message": "Event Management API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify API status.
    
    Returns:
        dict: Health status information
    """
    return {"status": "healthy", "message": "API is running"}

@app.post("/events", status_code=201)
async def create_event(event: Event):
    """
    Create a new event.
    
    Args:
        event (Event): Event data to create
        
    Returns:
        dict: Created event data with generated or provided eventId
        
    Raises:
        HTTPException: 500 if creation fails
    """
    try:
        # Use provided eventId or generate new one
        event_id = event.eventId if event.eventId else str(uuid.uuid4())
        event_data = event.dict(exclude_unset=True)
        event_data['eventId'] = event_id
        
        # Ensure capacity is stored as a number
        if 'capacity' in event_data:
            event_data['capacity'] = int(event_data['capacity'])
        
        table.put_item(Item=event_data)
        return event_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create event: {str(e)}")

@app.get("/events")
async def list_events(status: Optional[str] = None):
    """
    List all events or filter by status.
    
    Args:
        status (Optional[str]): Filter events by status (active, draft, cancelled)
        
    Returns:
        dict: Dictionary containing list of events
        
    Raises:
        HTTPException: 500 if listing fails
    """
    try:
        response = table.scan()
        events = response.get('Items', [])
        
        # Filter by status if provided
        if status:
            events = [e for e in events if e.get('status') == status]
        
        return {"events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list events: {str(e)}")

@app.get("/events/{event_id}")
async def get_event(event_id: str):
    """
    Retrieve a specific event by ID.
    
    Args:
        event_id (str): Unique identifier of the event
        
    Returns:
        dict: Event data
        
    Raises:
        HTTPException: 404 if event not found, 500 if retrieval fails
    """
    try:
        response = table.get_item(Key={'eventId': event_id})
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="Event not found")
        return response['Item']
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get event: {str(e)}")

@app.put("/events/{event_id}")
async def update_event(event_id: str, event_update: EventUpdate):
    """
    Update an existing event.
    
    Args:
        event_id (str): Unique identifier of the event to update
        event_update (EventUpdate): Fields to update
        
    Returns:
        dict: Updated event data
        
    Raises:
        HTTPException: 404 if event not found, 400 if no fields to update, 500 if update fails
    """
    try:
        # Check if event exists
        response = table.get_item(Key={'eventId': event_id})
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Build update expression
        update_data = {k: v for k, v in event_update.dict(exclude_unset=True).items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Ensure capacity is stored as a number
        if 'capacity' in update_data:
            update_data['capacity'] = int(update_data['capacity'])
        
        # Use ExpressionAttributeNames to handle reserved keywords
        update_expression = "SET " + ", ".join([f"#{k} = :{k}" for k in update_data.keys()])
        expression_attribute_names = {f"#{k}": k for k in update_data.keys()}
        expression_attribute_values = {f":{k}": v for k, v in update_data.items()}
        
        response = table.update_item(
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
    """
    Delete an event.
    
    Args:
        event_id (str): Unique identifier of the event to delete
        
    Returns:
        None: 204 No Content status
        
    Raises:
        HTTPException: 404 if event not found, 500 if deletion fails
    """
    try:
        # Check if event exists
        response = table.get_item(Key={'eventId': event_id})
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="Event not found")
        
        table.delete_item(Key={'eventId': event_id})
        return None  # 204 No Content
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete event: {str(e)}")

# Lambda handler
handler = Mangum(app)