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
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool
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

st.subheader(":material/smart_toy: Agent")
st.caption("Agents are LLMs that continuously call tools and adjust their actions based on environmental feedback.")

with st.expander(":material/description: Notes"):
    st.info(f"Agents can handle sophisticated tasks, but their implementation is often straightforward. They are typically just LLMs using tools based on environmental feedback in a loop. It is therefore crucial to design toolsets and their documentation clearly and thoughtfully.")
    st.info(f"When to use agents: Agents can be used for open-ended problems where it’s difficult or impossible to predict the required number of steps, and where you can’t hardcode a fixed path. The LLM will potentially operate for many turns, and you must have some level of trust in its decision-making. Agents' autonomy makes them ideal for scaling tasks in trusted environments.")

# Initialize the OCI Generative AI Chat Model
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Graph state: CopilotKitState
class ResearchState(CopilotKitState):
    messages: Annotated[list, add_messages]
    rag: str
    select_ai: str

class MasterAgent:
        
    @tool
    def call_rag(state: ResearchState):
        """
        Executes the RAG process to answer the user's query.
        """

        # Retrieve the content of the last message from the state
        input = state["messages"][-1]["content"]

        # Perform vector search using OCI
        content = oci_vector_search(input)

        # Wrap the response in a ToolMessage with a unique tool call ID
        rag_message = ToolMessage(content=content, name='[RAG_TOOL]', tool_call_id=str(uuid.uuid4()))
        return {"rag": [rag_message]}

    @tool
    def call_select_ai(state: ResearchState):
        """
        Generates a response regarding database tables and queries using Select AI.
        """
        
        # Retrieve the content of the last message from the state
        input = state["messages"][-1]["content"]
        
        # Generate a response using the OCI Select AI tool
        content = oci_select_ai(input)    

        # Wrap the response in a ToolMessage with a unique tool call ID
        select_ai_message = ToolMessage(content=content, name='[SELECT_AI_TOOL]', tool_call_id=str(uuid.uuid4()))
        return {"select_ai": [select_ai_message]}

    # Augment the LLM with tools
    tools = [call_rag, call_select_ai]

    # Build workflow
    agent_builder = StateGraph(ResearchState)

    # Add the nodes
    agent_builder.add_node("tools", ToolNode(tools))
    agent_builder.add_node("agent", lambda ResearchState: {"messages":llm.bind_tools(MasterAgent.tools).invoke(ResearchState['messages'])})

    # Add edges to connect nodes
    agent_builder.add_edge("tools", "agent")
    agent_builder.add_conditional_edges(
        "agent", tools_condition
    )
    agent_builder.set_entry_point("agent")

    # Compile the workflow
    graph = agent_builder.compile()

    # Generate and save a Mermaid diagram (PNG) of the workflow 
    def draw_mermaid_png(graph, fp: str = "./images/agents/agent_conditional.png"):
        img_data = graph.get_graph().draw_mermaid_png()
        img = PILImage.open(io.BytesIO(img_data))
        img.save(fp)

    # Asynchronously print the messages emitted by the agent during execution
    async def print_astream(graph, inputs, config):
        async for chunk in graph.astream(inputs, config, stream_mode="values"):
            message = chunk["messages"][-1]
            if isinstance(message, tuple):
                print(message)
            else:
                message.pretty_print()
            yield chunk


# Define configuration for the agent execution
config = {"configurable": {"thread_id": "thread-1"}}   

# Instantiate MasterAgent and retrieve the compiled workflow graph
graph = MasterAgent().graph

# Callback para capturar el input del usuario y actualizar la conversación
def chat_content():
    st.session_state['chat-conditional'].append(HumanMessage(content=st.session_state.content))

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
    for message in st.session_state['chat-conditional']:
        # 1) Si el mensaje es de tipo Human, no hacemos nada
        if isinstance(message, HumanMessage):
            st.chat_message("human", avatar=":material/psychology:").write(message.content)

        elif isinstance(message, ToolMessage):
            with st.expander(":blue[Tool]", expanded=False, icon=":material/construction:"):
                st.write(message)

        elif isinstance(message, AIMessage) and message.content == "":
            with st.expander(":blue[Agent]", expanded=False, icon=":material/smart_toy:"):
                # Asumiendo que la info relevante se encuentra en message.additional_kwargs
                st.write(message.additional_kwargs)

        elif isinstance(message, AIMessage) and message.content:
            st.chat_message("ai", avatar="images/avatar/openai.svg").write(message.content)

    # Si se agregó un nuevo mensaje de usuario, invocamos al agente
    if st.session_state['chat-conditional'] and isinstance(st.session_state['chat-conditional'][-1], HumanMessage):
        user_message = st.session_state['chat-conditional'][-1].content
        config = {"configurable": {"thread_id": "thread-1"}}
        inputs = {"messages": [HumanMessage(content=user_message)]}
        
        async def run_agent():
            async for chunk in MasterAgent.print_astream(graph, inputs, config):
                message = chunk["messages"][-1]
                if not isinstance(message, tuple):
                    
                    if message.type == "human":
                        pass
                    
                    if message.type == "tool":
                        with st.expander(":blue[Tool]", expanded=False, icon=":material/construction:"):
                            st.write(message)
                        st.session_state['chat-conditional'].append(message)
                        
                    elif message.type == "ai" and message.content=="":
                        with st.expander(":blue[Agent]", expanded=False, icon=":material/smart_toy:"):
                            st.write(message.additional_kwargs)
                        st.session_state['chat-conditional'].append(message)

                    elif message.type == "ai" and message.content:
                        st.chat_message(message.type, avatar="images/avatar/openai.svg").write(message.content)
                        st.session_state['chat-conditional'].append(message)

        asyncio.run(run_agent())

with col2:
    st.subheader("Conditional")
    # Dibuja y guarda el diagrama del flujo de trabajo como PNG
    MasterAgent.draw_mermaid_png(graph)
    st.image("images/agents/agent_conditional.png")
    st.info(
        '[LangGraph](https://langchain-ai.github.io/langgraph/tutorials/workflows/#agent)',
        icon=":material/bookmark:"
    )
    st.subheader("Questions")
    st.warning(
        "Usando SELECT AI, dime cuales son las ofertas por campaña de préstamo con un plazo mayor a 24 meses.",
        icon=":material/contact_support:")
    st.warning(
        "Según los documentos PDF, ¿qué documentos son necesarios para solicitar un préstamo personal?",
        icon=":material/contact_support:")


# python app.agent['chat-conditional'].py