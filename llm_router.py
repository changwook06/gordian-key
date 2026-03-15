import os
import time
import ollama
from typing import Generator
import vault

KEYWORD_MAP = {
    "ssn": ["ssn", "social security", "social security number"],
    "bank": ["bank", "routing", "account number", "checking", "savings"],
    "passport": ["passport", "passport number"],
    "address": ["address", "home address", "mailing address"],
    "phone": ["phone", "phone number", "cell", "mobile"],
    "email": ["email", "email address"],
    "name": ["name", "full name", "legal name"],
    "dob": ["dob", "date of birth", "birthday"],
    "insurance": ["insurance", "policy number", "health insurance"],
    "license": ["license", "driver's license", "driver license"]
}

def build_system_prompt(injected_data: dict) -> str:
    """
    Builds the system prompt with optionally injected vault data.
    """
    base_prompt = (
        "You are Gordian Key, a private and secure personal AI assistant. "
        "Your goal is to help the user while protecting their privacy. "
        "You have access to the user's sensitive data ONLY for this session. "
        "Never volunteer or mention this sensitive data unless the user explicitly asks for it. "
        "If the user asks for information you don't have, honestly state that it's not in your vault."
    )
    
    if not injected_data:
        return base_prompt
        
    data_block = "\n\nINJECTED USER DATA (SECURE):\n"
    for label, value in injected_data.items():
        data_block += f"- {label}: {value}\n"
        
    return base_prompt + data_block

def extract_keywords(user_message: str) -> list[str]:
    """
    Identifies relevant vault labels based on the user's message.
    """
    user_message = user_message.lower()
    relevant_labels = set()
    
    for label, keywords in KEYWORD_MAP.items():
        for keyword in keywords:
            if keyword in user_message:
                relevant_labels.add(label)
                break
                
    return list(relevant_labels)

def mock_stream_chat(
    user_message: str, 
    fernet, 
    db_path: str,
    conversation_history: list = None
) -> Generator[str, None, None]:
    """
    Simulates a streaming response for testing without Ollama.
    """
    relevant_labels = extract_keywords(user_message)
    injected_data = vault.search_entries(fernet, db_path, relevant_labels)
    
    response_text = "[MOCK MODE] Hello! "
    if injected_data:
        response_text += "I've retrieved the following from your vault: "
        response_text += ", ".join([f"**{k}**" for k in injected_data.keys()])
        response_text += ". How can I help with this information?"
    else:
        response_text += "I'm ready to help. No specific vault data was triggered by your message."
        
    # Simulate streaming
    for word in response_text.split(" "):
        yield word + " "
        time.sleep(0.05)

def stream_chat(
    user_message: str, 
    fernet, 
    db_path: str, 
    model: str = "mistral", 
    conversation_history: list = None
) -> Generator[str, None, None]:
    """
    Streams a chat response from Ollama (or mock) with RAG injection.
    """
    # Check for mock mode
    if os.environ.get("MOCK_LLM", "false").lower() == "true":
        yield from mock_stream_chat(user_message, fernet, db_path, conversation_history)
        return

    if conversation_history is None:
        conversation_history = []
        
    relevant_labels = extract_keywords(user_message)
    injected_data = vault.search_entries(fernet, db_path, relevant_labels)
    system_prompt = build_system_prompt(injected_data)
    
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})
    
    stream = ollama.chat(
        model=model,
        messages=messages,
        stream=True
    )
    
    for chunk in stream:
        if 'message' in chunk and 'content' in chunk['message']:
            yield chunk['message']['content']
