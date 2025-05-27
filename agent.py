from __future__ import annotations
from livekit.agents import ( # type: ignore
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm
)
from livekit.agents.multimodal import MultimodalAgent # type: ignore
from livekit.plugins import openai
from dotenv import load_dotenv
from api import AssistantFnc
from prompts import WELCOME_MESSAGE, INSTRUCTIONS, LOOKUP_MOVING_INFO
import os
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def entrypoint(ctx: JobContext):
    """Main entry point for the LiveKit agent."""
    logger.info("Starting LiveKit agent...")
    
    # Connect to the room
    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    await ctx.wait_for_participant()
    
    logger.info("Participant connected, initializing model...")
    
    # Initialize the OpenAI Realtime model
    model = openai.realtime.RealtimeModel(
        instructions=INSTRUCTIONS,
        voice="alloy",
        temperature=0.8,
        modalities=["audio", "text"]
    )
    
    # Initialize assistant functions
    assistant_fnc = AssistantFnc()
    
    # Create the multimodal agent
    assistant = MultimodalAgent(model=model, fnc_ctx=assistant_fnc)
    assistant.start(ctx.room)
    
    logger.info("Agent started successfully")
    
    # Get the session and send welcome message
    session = model.sessions[0]
    session.conversation.item.create(
        llm.ChatMessage(
            role="assistant",
            content=WELCOME_MESSAGE
        )
    )
    session.response.create()
    
    logger.info("Welcome message sent")
    
    @session.on("user_speech_committed")
    def on_user_speech_committed(msg: llm.ChatMessage):
        """Handle user speech input."""
        logger.info(f"User speech committed: {msg.content}")
        
        # Handle list content (images, etc.)
        if isinstance(msg.content, list):
            msg.content = "\n".join("[image]" if isinstance(x, llm.ChatImage) else x for x in msg.content)
        
        # Route the message based on content
        try:
            # Check if user wants to look up their details
            if any(keyword in msg.content.lower() for keyword in ["check", "look up", "my details", "request id"]):
                handle_lookup_request(msg)
            else:
                # Check if we have a complete moving request
                if assistant_fnc.has_moving_request():
                    handle_query(msg)
                else:
                    collect_moving_info(msg)
        except Exception as e:
            logger.error(f"Error processing user message: {str(e)}")
            session.conversation.item.create(
                llm.ChatMessage(
                    role="system",
                    content="I apologize, but I encountered an error processing your request. Could you please try again?"
                )
            )
            session.response.create()
    
    def handle_lookup_request(msg: llm.ChatMessage):
        """Handle request ID lookup."""
        logger.info("Handling lookup request")
        
        # Extract request ID if present in the message
        request_id_match = re.search(r'\b\d{6}\b', msg.content)
        if request_id_match:
            request_id = request_id_match.group(0)
            logger.info(f"Looking up request ID: {request_id}")
            
            try:
                result = assistant_fnc.lookup_moving_request(request_id)
                session.conversation.item.create(
                    llm.ChatMessage(
                        role="system",
                        content=f"Looking up request ID: {request_id}\n{result}"
                    )
                )
            except Exception as e:
                logger.error(f"Error looking up request: {str(e)}")
                session.conversation.item.create(
                    llm.ChatMessage(
                        role="system",
                        content="I encountered an error looking up your request. Please verify your request ID and try again."
                    )
                )
        else:
            session.conversation.item.create(
                llm.ChatMessage(
                    role="system",
                    content="I'll need your request ID to look up your details. Could you please provide your 6-digit request ID?"
                )
            )
        
        session.response.create()
    
    def collect_moving_info(msg: llm.ChatMessage):
        """Collect moving information from user."""
        logger.info("Collecting moving information")
        
        try:
            session.conversation.item.create(
                llm.ChatMessage(
                    role="system",
                    content=LOOKUP_MOVING_INFO(msg)
                )
            )
            session.response.create()
        except Exception as e:
            logger.error(f"Error collecting moving info: {str(e)}")
            session.conversation.item.create(
                llm.ChatMessage(
                    role="system",
                    content="I apologize, but I encountered an error while processing your information. Could you please repeat that?"
                )
            )
            session.response.create()
        
    def handle_query(msg: llm.ChatMessage):
        """Handle general queries when we have a complete moving request."""
        logger.info("Handling general query")
        
        try:
            session.conversation.item.create(
                llm.ChatMessage(
                    role="user",
                    content=msg.content
                )
            )
            session.response.create()
        except Exception as e:
            logger.error(f"Error handling query: {str(e)}")
            session.conversation.item.create(
                llm.ChatMessage(
                    role="system",
                    content="I apologize, but I encountered an error processing your query. Could you please try again?"
                )
            )
            session.response.create()

def main():
    """Main function to run the agent."""
    logger.info("Initializing LiveKit agent application...")
    
    # Verify required environment variables
    required_env_vars = ["LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET", "OPENAI_API_KEY", "DATABASE_URL"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    logger.info("All required environment variables are set")
    
    # Run the LiveKit agent
    try:
        cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
    except Exception as e:
        logger.error(f"Agent failed with error: {str(e)}")
        raise

if __name__ == "__main__":
    main()