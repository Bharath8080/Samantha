import streamlit as st
from scripts.agent import agent, agent_config

# Suggestions for the user
SUGGESTIONS = [
    "Tell me about yourself",
    "What can you do?",
    "What was the current weather at Hyderabad?",
    "What is the stock price of Apple?",
    "What are the flights avilable from DEL to BOM from today to next 10 days?",
    "best hight rated hotels at rajahmundary for stay of 6 days from today",
    "Give Apple company information",
    "Suggest me best Nike Shoes to Shop",
]

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "processing" not in st.session_state:
    st.session_state.processing = False

# Layout for clear button
_, col2 = st.columns([6, 1])
with col2:
    if st.button("Restart↺", type="secondary", help="Clear chat history"):
        st.session_state.messages = []
        st.rerun()

# Display suggestions in sidebar if chat is empty
if not st.session_state.messages:
    with st.sidebar:
        st.markdown("### Suggested Questions")
        selected_suggestion = st.pills(
            "Suggestions",
            SUGGESTIONS,
            label_visibility="collapsed",
            key="suggestion_pills"
        )
else:
    selected_suggestion = None

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
prompt = st.chat_input("Ask me anything...", key="chat_input")

# Handle input from either source
user_input = prompt or selected_suggestion

if user_input:
    if not st.session_state.processing:
        st.session_state.processing = True
        
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Force a rerun to show the user message immediately before processing
        # This is a bit tricky with Streamlit's execution model, but we want the UI to update.
        # However, appending to state and then continuing execution works, but the UI for the new message 
        # won't render until the next script run unless we manually render it or rerun.
        # Let's try manually rendering the user message first for immediate feedback if we don't rerun immediately.
        with st.chat_message("user"):
            st.markdown(user_input)

        try:
            # Convert session state messages to LangChain format
            langchain_messages = [
                {"role": msg["role"], "content": msg["content"]} 
                for msg in st.session_state.messages
            ]
            
            with st.spinner("Thinking..."):
                # Invoke agent with full conversation history
                agent_reply = agent.invoke(
                    {"messages": langchain_messages},
                    config=agent_config,
                )
                
                # Extract only the final assistant response content
                final_message = agent_reply["messages"][-1]
                if hasattr(final_message, 'content'):
                    response = final_message.content
                else:
                    response = str(final_message)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            # Render assistant message immediately
            with st.chat_message("assistant"):
                st.markdown(response)
                
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            with st.chat_message("assistant"):
                st.markdown(error_msg)
        
        st.session_state.processing = False
        # Rerun to clear the input field (if it was text input) and update state properly
        st.rerun()
