from fastapi import FastAPI, WebSocket
from typing import Dict, List
import json
from chat.chat import process_email
from chat.models import Message

app = FastAPI()

# Store conversation history for each client
conversations: Dict[str, List[Message]] = {}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_id = str(id(websocket))
    conversations[client_id] = []
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Process the message using existing chat logic
            response = process_email(message, conversations[client_id])
            
            # Update conversation history
            conversations[client_id].extend(response["messages"])
            
            # Send response back to client
            await websocket.send_json({
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "additional_kwargs": getattr(msg, "additional_kwargs", {})
                    }
                    for msg in response["messages"]
                ]
            })
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up when client disconnects
        if client_id in conversations:
            del conversations[client_id] 