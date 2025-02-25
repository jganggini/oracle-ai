import streamlit as st

def get_menu():
    """
    Build and display the sidebar menu based on the user's modules.

    Args:
        modules (str): The user's accessible modules.
        user (str): The user's name to display in the sidebar.
    """
    
    # Set session state
    if 'chat-conditional' not in st.session_state:
        st.session_state['chat-conditional'] = []

    if 'chat-parallelization' not in st.session_state:
        st.session_state['chat-parallelization'] = []

    if 'chat-routing' not in st.session_state:
        st.session_state['chat-routing'] = []

    if 'chat-ochestrator-worker' not in st.session_state:
        st.session_state['chat-ochestrator-worker'] = []
    
    with st.sidebar:
        st.image("images/st_pages.gif")

        with st.expander("🦜🕸️ LangGraph"):
            st.markdown("Workflows are systems where LLMs and tools are orchestrated through predefined code paths. Agents, on the other hand, are systems where LLMs dynamically direct their own processes and tool usage, maintaining control over how they accomplish tasks. [Workflows and Agents](https://langchain-ai.github.io/langgraph/tutorials/workflows/)")    
        
        # Always shown links
        st.page_link("app.py", label="FinAI Model", icon=":material/database:")

        # Always shown links
        st.page_link("pages/load_data.py", label="Load Data", icon=":material/upload_file:")

        st.subheader("Workflows & Agents")
        st.page_link("pages/agent_conditional.py", label="Agent", icon=":material/smart_toy:")
        st.page_link("pages/agent_parallelization.py", label="Parallelization", icon=":material/mitre:")
        st.page_link("pages/agent_routing.py", label="Routing", icon=":material/route:")
        st.page_link("pages/agent_ochestrator_worker.py", label="Orchestrator-Worker", icon=":material/account_tree:")
        