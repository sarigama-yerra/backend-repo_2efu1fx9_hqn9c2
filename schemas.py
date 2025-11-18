"""
Database Schemas for Chat App

Each Pydantic model represents a collection in MongoDB.
Collection name is the lowercase of the class name.
"""

from pydantic import BaseModel, Field
from typing import Optional, List

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user"
    """
    username: str = Field(..., min_length=2, max_length=32, description="Unique display name")
    avatar: Optional[str] = Field(None, description="Avatar URL")

class Conversation(BaseModel):
    """
    Conversations collection schema
    Collection name: "conversation"
    """
    title: str = Field(..., description="Conversation title e.g., General")
    members: Optional[List[str]] = Field(default=None, description="Optional list of usernames; None for public room")

class Message(BaseModel):
    """
    Messages collection schema
    Collection name: "message"
    """
    conversation_id: str = Field(..., description="Conversation identifier (stringified ObjectId)")
    sender: str = Field(..., min_length=2, max_length=32, description="Sender username")
    text: str = Field(..., min_length=1, max_length=4000, description="Message content")
