#!/usr/bin/env python3
"""Example client for the Puntini Agent API.

This script demonstrates how to connect to the API, authenticate,
and interact with the agent via WebSocket.
"""

import asyncio
import json
import websockets
from typing import Dict, Any


class PuntiniAPIClient:
    """Client for interacting with the Puntini Agent API."""
    
    def __init__(self, base_url: str = "ws://localhost:8000"):
        """Initialize the API client.
        
        Args:
            base_url: Base WebSocket URL for the API.
        """
        self.base_url = base_url
        self.websocket = None
        self.session_id = None
    
    async def connect(self, token: str) -> bool:
        """Connect to the API with authentication token.
        
        Args:
            token: JWT authentication token.
            
        Returns:
            True if connection successful, False otherwise.
        """
        try:
            url = f"{self.base_url}/ws/chat?token={token}"
            self.websocket = await websockets.connect(url)
            
            # Initialize session
            await self.send_message({
                "type": "init_session",
                "data": {}
            })
            
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from the API."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
    
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send a message to the API.
        
        Args:
            message: Message to send.
        """
        if self.websocket:
            await self.websocket.send(json.dumps(message))
    
    async def send_prompt(self, prompt: str) -> None:
        """Send a user prompt to the agent.
        
        Args:
            prompt: User prompt text.
        """
        await self.send_message({
            "type": "user_prompt",
            "data": {
                "prompt": prompt
            }
        })
    
    async def listen_for_messages(self) -> None:
        """Listen for incoming messages from the API."""
        if not self.websocket:
            return
        
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_message(data)
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")
        except Exception as e:
            print(f"Error listening for messages: {e}")
    
    async def handle_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming message from the API.
        
        Args:
            message: Parsed message data.
        """
        message_type = message.get("type")
        
        if message_type == "session_ready":
            self.session_id = message.get("session_id")
            print(f"✅ Session ready: {self.session_id}")
            print(f"   Initial graph: {message.get('data', {}).get('initial_graph', {})}")
        
        elif message_type == "assistant_response":
            text = message.get("data", {}).get("text", "")
            chunk = message.get("data", {}).get("chunk", False)
            if chunk:
                print(f"🤖 Agent (chunk): {text}", end="", flush=True)
            else:
                print(f"🤖 Agent: {text}")
        
        elif message_type == "reasoning":
            steps = message.get("data", {}).get("steps", [])
            print("🧠 Reasoning:")
            for i, step in enumerate(steps, 1):
                print(f"   {i}. {step}")
        
        elif message_type == "debug":
            debug_msg = message.get("data", {}).get("message", "")
            level = message.get("data", {}).get("level", "info")
            print(f"🐛 Debug ({level}): {debug_msg}")
        
        elif message_type == "error":
            error_code = message.get("error", {}).get("code", "unknown")
            error_msg = message.get("error", {}).get("message", "Unknown error")
            print(f"❌ Error ({error_code}): {error_msg}")
        
        elif message_type == "pong":
            print("🏓 Pong received")
        
        else:
            print(f"📨 Unknown message type: {message_type}")
            print(f"   Data: {message}")


async def main():
    """Main example function."""
    print("🚀 Puntini Agent API Client Example")
    print("=" * 50)
    
    # For this example, we'll use a mock token
    # In a real application, you would get this from the login endpoint
    token = "mock-token-for-example"
    
    client = PuntiniAPIClient()
    
    # Connect to the API
    print("Connecting to API...")
    if not await client.connect(token):
        print("❌ Failed to connect to API")
        return
    
    print("✅ Connected to API")
    
    # Start listening for messages in the background
    listen_task = asyncio.create_task(client.listen_for_messages())
    
    try:
        # Wait a moment for session to be ready
        await asyncio.sleep(1)
        
        # Send some example prompts
        prompts = [
            "Hello, can you help me create a project management graph?",
            "Add a task called 'Design UI' to the project",
            "Create a dependency between 'Design UI' and 'Implement Backend'",
            "Show me the current project structure"
        ]
        
        for prompt in prompts:
            print(f"\n👤 User: {prompt}")
            await client.send_prompt(prompt)
            
            # Wait for response
            await asyncio.sleep(2)
        
        # Send ping to test heartbeat
        print("\n🏓 Sending ping...")
        await client.send_message({
            "type": "ping",
            "data": {}
        })
        
        # Wait a bit more
        await asyncio.sleep(2)
        
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
    
    finally:
        # Clean up
        listen_task.cancel()
        await client.disconnect()
        print("👋 Disconnected from API")


if __name__ == "__main__":
    asyncio.run(main())
