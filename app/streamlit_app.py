"""
Streamlit UI for the Documentation Q&A Agent

Run with: streamlit run app/streamlit_app.py
"""

import streamlit as st
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ingest import index_data
from app.search_tools import setup_vector_search
from app.search_agent import init_agent
from app.logs import ConversationLogger


# Page configuration
st.set_page_config(
    page_title="Documentation Q&A Agent",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    st.session_state.agent = None
    st.session_state.search_tool = None
    st.session_state.logger = None
    st.session_state.messages = []
    st.session_state.repo_owner = "ilhamksyuriadi"
    st.session_state.repo_name = "workout-recommendation"


def initialize_agent(repo_owner: str, repo_name: str, use_openrouter: bool = True):
    """Initialize the agent with the specified repository."""
    
    with st.spinner("🔄 Setting up indexes... This may take a few minutes on first run."):
        # Create indexes
        progress_text = st.empty()
        
        progress_text.text("📥 Downloading repository...")
        text_index, docs = index_data(
            repo_owner=repo_owner,
            repo_name=repo_name,
            filter=None,
            chunk_method='sections',
            chunking_params={'level': 2}
        )
        
        progress_text.text(f"✅ Indexed {len(docs)} document chunks")
        
        progress_text.text("🧠 Creating vector embeddings...")
        vector_index, embedding_model = setup_vector_search(
            chunks=docs,
            model_name='multi-qa-distilbert-cos-v1'
        )
        
        progress_text.text("✅ Vector index created")
        
        progress_text.text("🤖 Initializing AI agent...")
        
        # Check API key
        api_key = os.getenv("OPENROUTER_API_KEY") if use_openrouter else os.getenv("OPENAI_API_KEY")
        if not api_key:
            st.error(f"❌ {'OPENROUTER_API_KEY' if use_openrouter else 'OPENAI_API_KEY'} not found in environment variables")
            st.info("💡 Please add your API key to the .env file")
            return None, None, None
        
        # Initialize agent
        agent, search_tool = init_agent(
            index=text_index,
            repo_owner=repo_owner,
            repo_name=repo_name,
            vector_index=vector_index,
            embedding_model=embedding_model,
            use_openrouter=use_openrouter,
            openrouter_api_key=api_key if use_openrouter else None
        )
        
        # Initialize logger
        logger = ConversationLogger()
        
        progress_text.text("✅ Agent initialized successfully!")
        
    return agent, search_tool, logger


async def ask_question_async(agent, question: str, logger):
    """Ask a question to the agent asynchronously."""
    result = await agent.run(user_prompt=question)
    
    # Log the interaction
    if logger:
        logger.log_interaction(
            agent=agent,
            messages=result.new_messages(),
            query=question,
            response=result.output,
            source="streamlit"
        )
    
    return result.output


def ask_question(agent, question: str, logger):
    """Synchronous wrapper for asking questions."""
    return asyncio.run(ask_question_async(agent, question, logger))


# Sidebar
with st.sidebar:
    st.title("⚙️ Configuration")
    
    # Repository settings
    st.subheader("📦 Repository")
    repo_owner = st.text_input(
        "Repository Owner",
        value=st.session_state.repo_owner,
        help="GitHub username or organization"
    )
    repo_name = st.text_input(
        "Repository Name",
        value=st.session_state.repo_name,
        help="Name of the repository"
    )
    
    # Model settings
    st.subheader("🤖 Model")
    use_openrouter = st.radio(
        "AI Provider",
        options=[True, False],
        format_func=lambda x: "OpenRouter (Free)" if x else "OpenAI (Paid)",
        index=0,
        help="Choose between OpenRouter (free) or OpenAI (paid)"
    )
    
    # Initialize button
    if st.button("🚀 Initialize Agent", type="primary", use_container_width=True):
        st.session_state.repo_owner = repo_owner
        st.session_state.repo_name = repo_name
        
        agent, search_tool, logger = initialize_agent(repo_owner, repo_name, use_openrouter)
        
        if agent:
            st.session_state.agent = agent
            st.session_state.search_tool = search_tool
            st.session_state.logger = logger
            st.session_state.initialized = True
            st.session_state.messages = []
            st.success("✅ Agent initialized successfully!")
            st.rerun()
    
    # Status
    st.divider()
    st.subheader("📊 Status")
    if st.session_state.initialized:
        st.success("✅ Agent Ready")
        st.info(f"📚 Repository: {st.session_state.repo_owner}/{st.session_state.repo_name}")
    else:
        st.warning("⚠️ Agent Not Initialized")
        st.info("👆 Click 'Initialize Agent' to start")
    
    # Clear conversation
    if st.session_state.initialized:
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()


# Main content
st.title("📚 Documentation Q&A Agent")
st.markdown("""
Ask questions about the documentation and get AI-powered answers with citations!
""")

# Check if agent is initialized
if not st.session_state.initialized:
    st.info("👈 Please initialize the agent using the sidebar to get started.")
    
    # Show example questions
    st.subheader("💡 Example Questions")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        - How do I install this project?
        - What are the main features?
        - How do I configure the application?
        """)
    
    with col2:
        st.markdown("""
        - What dataset does this use?
        - How do I run the API?
        - How do I deploy this?
        """)
    
    st.stop()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about the documentation..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            response = ask_question(
                st.session_state.agent,
                prompt,
                st.session_state.logger
            )
        st.markdown(response)
    
    # Add assistant response to chat
    st.session_state.messages.append({"role": "assistant", "content": response})

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.8em;'>
    Built with Streamlit • Powered by PydanticAI • Using RAG (Retrieval-Augmented Generation)
</div>
""", unsafe_allow_html=True)
