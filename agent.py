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
from frontend import start_frontend
import os
import re
import threading
import sys
import subprocess

load_dotenv()

async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    await ctx.wait_for_participant()
    
    model = openai.realtime.RealtimeModel(
        instructions=INSTRUCTIONS,
        voice="alloy",
        temperature=0.8,
        modalities=["audio", "text"]
    )
    assistant_fnc = AssistantFnc()
    assistant = MultimodalAgent(model=model, fnc_ctx=assistant_fnc)
    assistant.start(ctx.room)
    
    session = model.sessions[0]
    session.conversation.item.create(
        llm.ChatMessage(
            role="assistant",
            content=WELCOME_MESSAGE
        )
    )
    session.response.create()
    
    @session.on("user_speech_committed")
    def on_user_speech_committed(msg: llm.ChatMessage):
        if isinstance(msg.content, list):
            msg.content = "\n".join("[image]" if isinstance(x, llm.ChatImage) else x for x in msg)
        
        # Check if user wants to look up their details
        if "check" in msg.content.lower() or "look up" in msg.content.lower() or "my details" in msg.content.lower():
            handle_lookup_request(msg)
        else:
            if assistant_fnc.has_moving_request():
                handle_query(msg)
            else:
                collect_moving_info(msg)
    
    def handle_lookup_request(msg: llm.ChatMessage):
        # Extract request ID if present in the message
        request_id_match = re.search(r'\b\d{6}\b', msg.content)
        if request_id_match:
            request_id = request_id_match.group(0)
            result = assistant_fnc.lookup_moving_request(request_id)
            session.conversation.item.create(
                llm.ChatMessage(
                    role="system",
                    content=f"Looking up request ID: {request_id}\n{result}"
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
        session.conversation.item.create(
            llm.ChatMessage(
                role="system",
                content=LOOKUP_MOVING_INFO(msg)
            )
        )
        session.response.create()
        
    def handle_query(msg: llm.ChatMessage):
        session.conversation.item.create(
            llm.ChatMessage(
                role="user",
                content=msg.content
            )
        )
        session.response.create()

def run_streamlit():
    """Run the Streamlit frontend in a separate process."""
    try:
        # Get the absolute path of the frontend.py file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        frontend_path = os.path.join(current_dir, 'frontend.py')
        
        # Start Streamlit in a separate process
        subprocess.Popen([
            sys.executable,
            "-m",
            "streamlit",
            "run",
            frontend_path,
            "--server.port=8501",
            "--server.address=localhost"
        ])
    except Exception as e:
        print(f"Error starting Streamlit: {str(e)}")

if __name__ == "__main__":
    # Start Streamlit in a separate process
    streamlit_process = threading.Thread(target=run_streamlit)
    streamlit_process.daemon = True
    streamlit_process.start()
    
    # Run the main agent
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))