import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from typing import Literal, Dict, List
from chat.models import Message
from chat.prompts import triage_system_prompt, triage_user_prompt, agent_system_prompt
from chat.tools import analyze_prediction
from langgraph.graph import add_messages
from typing_extensions import TypedDict, Annotated
from chat.config import profile, prompt_instructions
from chat.models import Router

_ = load_dotenv()

# Initialize LLM
llm = init_chat_model("openai:gpt-4o-mini")
llm_router = llm.with_structured_output(Router)

class State(TypedDict):
    email_input: dict
    messages: Annotated[list, add_messages]

def create_prompt(state):
    return [
        {
            "role": "system", 
            "content": agent_system_prompt.format(
                instructions="Use these tools when appropriate to help manage tasks efficiently.",
                name="Assistant",
                full_name="AI Assistant"
            )
        }
    ] + state['messages']

def triage_router(state: State) -> Command[Literal["response_agent", "__end__"]]:
    author = state['email_input']['author']
    to = state['email_input']['to']
    subject = state['email_input']['subject']
    email_thread = state['email_input']['email_thread']

    system_prompt = triage_system_prompt.format(
        full_name=profile["full_name"],
        name=profile["name"],
        user_profile_background=profile["user_profile_background"],
        triage_no=prompt_instructions["triage_rules"]["ignore"],
        triage_notify=prompt_instructions["triage_rules"]["notify"],
        triage_email=prompt_instructions["triage_rules"]["respond"],
        examples=None
    )
    user_prompt = triage_user_prompt.format(
        author=author, 
        to=to, 
        subject=subject, 
        email_thread=email_thread
    )
    result = llm_router.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )
    if result.classification == "respond":
        print("📧 Classification: RESPOND - This email requires a response")
        goto = "response_agent"
        update = {
            "messages": [
                {
                    "role": "user",
                    "content": f"Respond to the email {state['email_input']}",
                }
            ]
        }
    elif result.classification == "ignore":
        print("🚫 Classification: IGNORE - This email can be safely ignored")
        update = None
        goto = END
    elif result.classification == "notify":
        print("🔔 Classification: NOTIFY - This email contains important information")
        update = None
        goto = END
    else:
        raise ValueError(f"Invalid classification: {result.classification}")
    return Command(goto=goto, update=update)

# Create the agent
tools = [analyze_prediction]
agent = create_react_agent(
    "openai:gpt-4o",
    tools=tools,
    prompt=create_prompt,
)

def process_email(email_input: dict, conversation_history: List[Message] = None) -> Dict:
    """
    Process an email input and return a response.
    
    Args:
        email_input: The email input to process
        conversation_history: Optional list of previous messages in the conversation
        
    Returns:
        Dict containing the response messages
    """
    # Initialize conversation history if not provided
    if conversation_history is None:
        conversation_history = []
    
    # Create state with conversation history
    state = {
        "email_input": email_input,
        "messages": [
            {"role": msg.role, "content": msg.content}
            for msg in conversation_history
        ]
    }
    
    # Add current message
    state["messages"].append({
        "role": "user",
        "content": f"Respond to: {email_input['email_thread']}"
    })
    
    # Process message
    response = agent.invoke(state)
    
    return response