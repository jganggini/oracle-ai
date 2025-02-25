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
from typing_extensions import Literal
from pydantic import BaseModel, Field

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

st.subheader(":material/route: Agent")
st.caption("Routing classifies an input and directs it to a followup task.")

with st.expander(":material/description: Notes"):
    st.info(f"Routing classifies an input and directs it to a specialized followup task. This workflow allows for separation of concerns, and building more specialized prompts. Without this workflow, optimizing for one kind of input can hurt performance on other inputs.")
    st.info(f"When to use this workflow: Routing works well for complex tasks where there are distinct categories that are better handled separately, and where classification can be handled accurately, either by an LLM or a more traditional classification model/algorithm.")

# Initialize the OCI Generative AI Chat Model
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Graph state: CopilotKitState
class ResearchState(CopilotKitState):
    messages: Annotated[list, add_messages]
    decision: str

# Schema for structured output to use as routing logic
class Route(BaseModel):
    step: Literal["rag", "select_ai"] = Field(
        None, description="The next step in the routing process"
    )

# Augment the LLM with schema for structured output
router = llm.with_structured_output(Route)

class MasterAgent:

    def call_rag(state: ResearchState):
        """
        Executes the RAG process to answer the user's query.
        """

        # Retrieve the content of the last message from the state
        input = state["messages"][0].content

        # Perform vector search using OCI
        content = oci_vector_search(input)
        
        # Crear un ToolMessage con la respuesta obtenida
        rag_message = ToolMessage(content=content, name='[RAG_TOOL]', tool_call_id=str(uuid.uuid4()))
        return {"messages": [rag_message]}

    def call_select_ai(state: ResearchState):
        """
        Generates a response regarding database tables and queries using Select AI.
        """

        # Retrieve the content of the last message from the state
        input = state["messages"][0].content

        # Generate a response using the OCI Select AI tool
        content = oci_select_ai(input)

        # Crear un ToolMessage con la respuesta obtenida
        select_ai_message = ToolMessage(content=content, name='[SELECT_AI_TOOL]', tool_call_id=str(uuid.uuid4()))
        return {"messages": [select_ai_message]}

    def call_router(state: ResearchState):
        """
        Route the input to the appropriate node
        """

        # Retrieve the content of the last message from the state
        input = state["messages"][0].content
        
        # Run the augmented LLM with structured output to serve as routing logic
        decision = router.invoke(
            [
                SystemMessage(
                    content="Route the input to rag or select ai based on the user's request."
                ),
                HumanMessage(content=input),
            ]
        )

        # Wrap the response in a ToolMessage with a unique tool call ID
        router_message = ToolMessage(content=decision.step, name='[ROUTER_TOOL]', tool_call_id=str(uuid.uuid4()))
        return {"messages": [router_message]}

    # Conditional edge function to route to the appropriate node
    def route_decision(state: ResearchState):
        # Return the node name you want to visit next
        if state["messages"][-1].content == "rag":
            return "call_rag"
        elif state["messages"][-1].content == "select_ai":
            return "call_select_ai"

    # Build workflow
    agent_builder = StateGraph(ResearchState)

    # Add the nodes
    agent_builder.add_node("call_rag", call_rag)
    agent_builder.add_node("call_select_ai", call_select_ai)
    agent_builder.add_node("call_router", call_router)

    # Add edges to connect nodes
    agent_builder.add_edge(START, "call_router")
    agent_builder.add_conditional_edges(
        "call_router",
        route_decision,
        {  # Name returned by route_decision : Name of next node to visit
            "call_rag": "call_rag",
            "call_select_ai": "call_select_ai"
        }
    )
    agent_builder.add_edge("call_rag", END)
    agent_builder.add_edge("call_select_ai", END)

    # Compile the workflow
    graph = agent_builder.compile()

    # Generate and save a Mermaid diagram (PNG) of the workflow 
    def draw_mermaid_png(graph, fp: str = "./images/agents/agent_routing.png"):
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
    st.session_state['chat-routing'].append(HumanMessage(content=st.session_state.content))

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
    for message in st.session_state['chat-routing']:
        # 1) Si el mensaje es de tipo Human, no hacemos nada
        if isinstance(message, HumanMessage):
            st.chat_message("human", avatar=":material/psychology:").write(message.content)

        elif isinstance(message, ToolMessage) and message.name == "[ROUTER_TOOL]":
            with st.expander(":blue[Router]", expanded=False, icon=":material/psychology:"):
                st.write(message)

        elif isinstance(message, ToolMessage) and message.name == "[SELECT_AI_TOOL]":
            st.chat_message("ai", avatar="images/avatar/openai.svg").write(message.content)

        elif isinstance(message, ToolMessage) and message.name == "[RAG_TOOL]":
            st.chat_message("ai", avatar="images/avatar/openai.svg").write(message.content)


    # Si se agregó un nuevo mensaje de usuario, invocamos al agente
    if st.session_state['chat-routing'] and isinstance(st.session_state['chat-routing'][-1], HumanMessage):
        user_message = st.session_state['chat-routing'][-1].content
        config = {"configurable": {"thread_id": "thread-1"}}
        inputs = {"messages": [HumanMessage(content=user_message)]}
        
        async def run_agent():
            async for chunk in MasterAgent.print_astream(graph, inputs, config):
                message = chunk["messages"][-1]
                if not isinstance(message, tuple):
                    
                    if message.type == "tool" and message.name == "[ROUTER_TOOL]":
                        with st.expander(":blue[Router]", expanded=False, icon=":material/route:"):
                            st.write(message)
                        st.session_state['chat-routing'].append(message)
                    
                    elif message.type == "tool" and message.name == "[SELECT_AI_TOOL]":
                        st.chat_message("ai", avatar="images/avatar/openai.svg").write(message.content)
                        st.session_state['chat-routing'].append(message)

                    elif message.type == "tool" and message.name == "[RAG_TOOL]":
                        st.chat_message("ai", avatar="images/avatar/openai.svg").write(message.content)
                        st.session_state['chat-routing'].append(message)

        asyncio.run(run_agent())

with col2:
    st.subheader("Routing")
    # Dibuja y guarda el diagrama del flujo de trabajo como PNG
    MasterAgent.draw_mermaid_png(graph)
    st.image("images/agents/agent_routing.png")
    st.info(
        '[LangGraph](https://langchain-ai.github.io/langgraph/tutorials/workflows/#routing)',
        icon=":material/bookmark:"
    )
    st.subheader("Questions")
    st.warning(
        "¿Cuántos clientes han solicitado préstamos personales superiores a USD 10,000?",
        icon=":material/contact_support:"
    )
    st.warning(
        "¿Cuáles son los destinos más comunes para los préstamos personales según la información en los documentos PDF?",
        icon=":material/contact_support:"
    )

    

# python app.agent.route.py