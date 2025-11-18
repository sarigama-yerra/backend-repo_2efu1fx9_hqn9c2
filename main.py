import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User, Conversation, Message

app = FastAPI(title="Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Utilities
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


# Basic health route
@app.get("/")
def read_root():
    return {"message": "Chat backend running"}


# Onboarding: ensure default room exists
@app.post("/api/bootstrap")
def bootstrap():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    room = db["conversation"].find_one({"title": "General"})
    if not room:
        create_document("conversation", {"title": "General", "members": None})
    return {"status": "ok"}


# Users
@app.post("/api/users", response_model=dict)
def create_user(user: User):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    existing = db["user"].find_one({"username": user.username})
    if existing:
        return {"id": str(existing.get("_id")), "username": user.username}
    new_id = create_document("user", user)
    return {"id": new_id, "username": user.username}


# Conversations
@app.get("/api/conversations", response_model=List[dict])
def list_conversations():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    convs = get_documents("conversation")
    return [
        {"id": str(c["_id"]), "title": c.get("title", ""), "members": c.get("members")}
        for c in convs
    ]


# Messages
class SendMessageBody(BaseModel):
    conversation_id: str
    sender: str
    text: str

@app.get("/api/messages/{conversation_id}", response_model=List[dict])
def get_messages(conversation_id: str, limit: int = 50):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    if not ObjectId.is_valid(conversation_id):
        raise HTTPException(400, "Invalid conversation id")
    msgs = (
        db["message"]
        .find({"conversation_id": conversation_id})
        .sort("created_at", 1)
        .limit(limit)
    )
    return [
        {
            "id": str(m["_id"]),
            "conversation_id": m.get("conversation_id"),
            "sender": m.get("sender"),
            "text": m.get("text"),
            "created_at": m.get("created_at"),
        }
        for m in msgs
    ]

@app.post("/api/messages", response_model=dict)
def send_message(body: SendMessageBody):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    # ensure conversation exists
    if not ObjectId.is_valid(body.conversation_id):
        raise HTTPException(400, "Invalid conversation id")
    conv = db["conversation"].find_one({"_id": ObjectId(body.conversation_id)})
    if not conv:
        raise HTTPException(404, "Conversation not found")
    # optionally ensure user exists
    user = db["user"].find_one({"username": body.sender})
    if not user:
        create_document("user", {"username": body.sender})
    new_id = create_document(
        "message",
        {"conversation_id": body.conversation_id, "sender": body.sender, "text": body.text},
    )
    return {"id": new_id}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available" if db is None else "✅ Connected",
    }
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
