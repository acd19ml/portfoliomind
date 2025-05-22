import asyncio
import websockets
import json
from chat.utils import pretty_print
from chat.models import Message

async def chat_client():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        print("Connected to server. Type 'quit' to exit.")
        
        while True:
            # Get user input
            user_input = input("\nYou: ")
            if user_input.lower() == 'quit':
                break
                
            # Create message object
            message = {
                "author": "user",
                "to": "assistant",
                "subject": "Chat",
                "email_thread": user_input
            }
            
            # Send message to server
            await websocket.send(json.dumps(message))
            
            # Receive response
            response = await websocket.recv()
            messages = json.loads(response)["messages"]
            
            # Print response
            for msg in messages:
                message_obj = Message(
                    role=msg["role"],
                    content=msg["content"],
                    additional_kwargs=msg.get("additional_kwargs", {})
                )
                pretty_print(message_obj)

if __name__ == "__main__":
    asyncio.run(chat_client()) 