import ollama

# Break 1: Define Eva's Personality Context
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are Eva, an elite, professional technical backend and frontend interviewer. "
        "Your responses must be highly conversational, encouraging, yet technically sharp. "
        "Keep your responses concise (1-3 sentences maximum per turn) so it feels like a real talk. "
        "Focus on asking one clear follow-up question at a time based on the candidate's response. "
        "Do not output code blocks unless explicitly requested."
    )
}

# Break 2: The Core Generation Engine
def generate_eva_response(conversation_history):
    """
    Sends the ongoing conversation history to Ollama (Qwen2.5)
    and yields tokens in real time.
    
    :param conversation_history: List of message dicts tracking the interview.
    :return: A generator yielding text chunks as they arrive from the model.
    """
    # Combine the underlying system persona with the actual chat logs
    full_messages = [SYSTEM_PROMPT] + conversation_history
    
    try:
        # Request a streaming response from the locally running Ollama engine
        stream = ollama.chat(
            model="qwen2.5:1.5b",
            messages=full_messages,
            stream=True
        )
        
        # Yield each piece of text as soon as the hardware generates it
        for chunk in stream:
            token = chunk.get("message", {}).get("content", "")
            if token:
                yield token
                
    except Exception as e:
        yield f"\n[Brain Error: Make sure Ollama is running and qwen2.5 is pulled. Details: {str(e)}]"

# Break 3: Local Test Execution 
if __name__ == "__main__":
    print("Testing Brain Module... (Ensure 'ollama run qwen2.5' is working in the background)")
    
    # Mocking a transcription response that would normally come from your listener.py
    mock_history = [
        {"role": "user", "content": "Hi Eva, I am a frontend developer working with React, Next.js, and Tailwind CSS."}
    ]
    
    print("\nEva is thinking... ", end="", flush=True)
    
    # Loop over the stream live in the terminal to verify it works
    full_collected_response = ""
    for token in generate_eva_response(mock_history):
        print(token, end="", flush=True)
        full_collected_response += token
    print("\n\nTest Stream Complete!")