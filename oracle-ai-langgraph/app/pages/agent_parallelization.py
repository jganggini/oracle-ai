import streamlit as st
from streamlit_float import *

import components as component
import utils as utils

import os
import io
import uuid
import asyncio
from typing import Annotated
from PIL import Image as PILImage
from dotenv import load_dotenv

from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_openai import ChatOpenAI

from copilotkit import CopilotKitState

from tools.oci_vector_search import oci_vector_search
from tools.oci_select_ai import oci_select_ai

# Load environment variables from the .env file
load_dotenv()

component.get_menu()
component.get_footer()

# Initialize streamlit_float para estilos flotantes
float_init()

st.subheader(":material/mitre: Agent")
st.caption("With parallelization, LLMs work simultaneously on a task:")

with st.expander(":material/description: Notes"):
    st.info(f"LLMs can sometimes work simultaneously on a task and have their outputs aggregated programmatically. This workflow, parallelization, manifests in two key variations: Sectioning: Breaking a task into independent subtasks run in parallel. Voting: Running the same task multiple times to get diverse outputs.")
    st.info(f"When to use this workflow: Parallelization is effective when the divided subtasks can be parallelized for speed, or when multiple perspectives or attempts are needed for higher confidence results. For complex tasks with multiple considerations, LLMs generally perform better when each consideration is handled by a separate LLM call, allowing focused attention on each specific aspect.")

# Initialize the OCI Generative AI Chat Model
llm = ChatOCIGenAI(
    model_id         = "cohere.command-r-08-2024",
    service_endpoint = os.getenv("CON_GEN_AI_SERVICE_ENDPOINT"),
    compartment_id   = os.getenv("CON_COMPARTMENT_ID"),
    provider         = "cohere",
    is_stream        = True,
    auth_type        = os.getenv("CON_GEN_AI_AUTH_TYPE"),
    model_kwargs     = {
        "temperature" : 0,
    }
)

# Graph state: CopilotKitState
class ResearchState(CopilotKitState):
    messages: Annotated[list, add_messages]
    rag: str
    select_ai: str
    aggregator: str

class MasterAgent:
        
    def call_rag(state: ResearchState):
        """
        Executes the RAG process to answer the user's query.
        """

        # Retrieve the content of the last message from the state
        input = state["messages"][-1].content

        # Perform vector search using OCI
        content = oci_vector_search(input)

        # Wrap the response in a ToolMessage with a unique tool call ID
        rag_message = ToolMessage(content=content, name='[RAG_TOOL]', tool_call_id=str(uuid.uuid4()))
        return {"rag": [rag_message]}

    def call_select_ai(state: ResearchState):
        """
        Generates a response regarding database tables and queries using Select AI.
        """

        # Retrieve the content of the last message from the state
        input = state["messages"][-1].content

        # Generate a response using the OCI Select AI tool
        content = oci_select_ai(input)  

        # Wrap the response in a ToolMessage with a unique tool call ID
        select_ai_message = ToolMessage(content=content, name='[SELECT_AI_TOOL]', tool_call_id=str(uuid.uuid4()))
        return {"select_ai": [select_ai_message]}

    def call_aggregator(state: ResearchState):
        """
        Combines responses from RAG and Select AI tools into a single message.
        """
        combined = (
            f"**[QUESTION]**\n\n{state['messages'][-1].content}!\n\n"
            f"**[RAG_TOOL]**\n\n{state['rag'][-1].content}\n\n"
            f"**[SELECT_AI_TOOL]**\n\n{state['select_ai'][-1].content}"
        )
        
        combined_message = AIMessage(content=combined, name="[AGGREGATOR_TOOL]")
        return {"aggregator": combined_message}

    # Build workflow
    agent_builder = StateGraph(ResearchState)

    # Add the nodes
    agent_builder.add_node("call_rag", call_rag)
    agent_builder.add_node("call_select_ai", call_select_ai)
    agent_builder.add_node("call_aggregator", call_aggregator)

    # Add edges to connect nodes
    agent_builder.add_edge(START, "call_rag")
    agent_builder.add_edge(START, "call_select_ai")
    agent_builder.add_edge("call_rag", "call_aggregator")
    agent_builder.add_edge("call_select_ai", "call_aggregator")
    agent_builder.add_edge("call_aggregator", END)

    # Compile the workflow
    graph = agent_builder.compile()

    # Generate and save a Mermaid diagram (PNG) of the workflow 
    def draw_mermaid_png(graph, fp: str = "./images/agents/agent_parallelization.png"):
        img_data = graph.get_graph().draw_mermaid_png()
        img = PILImage.open(io.BytesIO(img_data))
        img.save(fp)

    # Asynchronously print the messages emitted by the agent during execution
    async def print_astream(graph, inputs, config):
        async for chunk in graph.astream(inputs, config, stream_mode="values"):
            
            if "aggregator" in chunk:
                chunk["aggregator"].pretty_print()
            
            elif "rag" in chunk or "select_ai" in chunk:
                if "rag" in chunk:
                    chunk["rag"][-1].pretty_print()
                if "select_ai" in chunk:
                    chunk["select_ai"][-1].pretty_print()
            
            elif "messages" in chunk:
                for msg in chunk["messages"]:
                    msg.pretty_print()

            yield chunk


# Define configuration for the agent execution
config = {"configurable": {"thread_id": "thread-1"}}   

# Instantiate MasterAgent and retrieve the compiled workflow graph
graph = MasterAgent().graph

# Callback para capturar el input del usuario y actualizar la conversación
def chat_content():
    # Ya se inicializó 'conversation' al inicio, por lo que no es necesario volver a comprobarlo.
    st.session_state['chat-parallelization'].append(HumanMessage(content=st.session_state.content))

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Chat")
    with st.container():
        
        st.chat_input(key='content', on_submit=chat_content)
        # Estilo para un botón flotante (o similar) usando streamlit_float
        button_b_pos = "3.2rem"
        button_css = float_css_helper(width="2.2rem", bottom=button_b_pos, transition=0)
        float_parent(css=button_css)
        
    # Mostrar la conversación actual
    for message in st.session_state['chat-parallelization']:
        # Si el mensaje es de tipo HumanMessage, se renderiza con st.chat_message
        
        if isinstance(message, HumanMessage):
            st.chat_message("human", avatar=":material/psychology:").write(message.content)

        # Si es de tipo ToolMessage, se muestra en un expander
        elif isinstance(message, ToolMessage) and message.name == "[SELECT_AI_TOOL]":
            with st.expander(":blue[Tool: Select AI]", expanded=False, icon=":material/construction:"):
                st.write(message)
        
        # Si es de tipo ToolMessage, se muestra en un expander
        elif isinstance(message, ToolMessage) and message.name == "[RAG_TOOL]":
            with st.expander(":blue[Tool: RAG]", expanded=False, icon=":material/construction:"):
                st.write(message)

        # Si es un mensaje AI con contenido
        elif isinstance(message, AIMessage) and message.content:
            st.chat_message("ai", avatar="images/avatar/cohere.svg").write(message.content)

    
        # Si se agregó un nuevo mensaje de usuario, invocamos al agente
        if st.session_state['chat-parallelization'] and isinstance(st.session_state['chat-parallelization'][-1], HumanMessage):
            user_message = st.session_state['chat-parallelization'][-1].content
            config = {"configurable": {"thread_id": "thread-1"}}
            inputs = {"messages": [HumanMessage(content=user_message)]}
            
            async def run_agent():
                async for chunk in MasterAgent.print_astream(graph, inputs, config):
                    # Caso: Existe la clave "aggregator"
                    if "aggregator" in chunk:
                        aggregator = chunk["aggregator"]
                        st.chat_message(message.type, avatar="images/avatar/cohere.svg").write(aggregator.content)
                        st.session_state['chat-parallelization'].append(aggregator)
                    
                    # Caso: Existe "rag" o "select_ai"
                    elif "rag" in chunk or "select_ai" in chunk:
                        if "rag" in chunk:
                            rag_message = chunk["rag"][-1]
                            with st.expander(":blue[Tool: RAG]", expanded=False, icon=":material/construction:"):
                                st.write(rag_message)
                            st.session_state['chat-parallelization'].append(rag_message)
                        if "select_ai" in chunk:
                            select_ai_message = chunk["select_ai"][-1]
                            with st.expander(":blue[Tool: Select AI]", expanded=False, icon=":material/construction:"):
                                st.write(select_ai_message)
                            st.session_state['chat-parallelization'].append(select_ai_message)

            asyncio.run(run_agent())

with col2:
    st.subheader("Parallelization")
    # Dibuja y guarda el diagrama del flujo de trabajo como PNG
    MasterAgent.draw_mermaid_png(graph)
    st.image("images/agents/agent_parallelization.png")
    st.info(
        '[LangGraph](https://langchain-ai.github.io/langgraph/tutorials/workflows/#parallelization)',
        icon=":material/bookmark:"
    )
    st.subheader("Questions")
    st.warning(
        "¿Cuántos clientes han solicitado préstamos personales superiores a USD 10,000?",
        icon=":material/contact_support:"
    )