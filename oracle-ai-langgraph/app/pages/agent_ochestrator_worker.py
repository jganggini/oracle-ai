import streamlit as st
from streamlit_float import *

import components as component
import utils as utils

import os
import io
import uuid
import asyncio
from typing import Annotated, List
from PIL import Image as PILImage
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import operator

from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, AIMessage
from langgraph.graph import MessagesState, StateGraph, START, END
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langgraph.constants import Send
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

st.subheader(":material/account_tree: Agent")
st.caption("With orchestrator-worker, an orchestrator breaks down a task and delegates each sub-task to workers. ")

with st.expander(":material/description: Notes"):
    st.info(f"In the orchestrator-workers workflow, a central LLM dynamically breaks down tasks, delegates them to worker LLMs, and synthesizes their results.")
    st.info(f"When to use this workflow: This workflow is well-suited for complex tasks where you can’t predict the subtasks needed (in coding, for example, the number of files that need to be changed and the nature of the change in each file likely depend on the task). Whereas it’s topographically similar, the key difference from parallelization is its flexibility—subtasks aren't pre-defined, but determined by the orchestrator based on the specific input.")

# Initialize the OCI Generative AI Chat Model
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Schema for structured output to use in planning
class Section(BaseModel):
    name: str = Field(
        description="Name for this section of the report.",
    )
    description: str = Field(
        description="Brief overview of the main topics and concepts to be covered in this section.",
    )

class Sections(BaseModel):
    sections: List[Section] = Field(
        description="Sections of the report.",
    )

# Augment the LLM with schema for structured output
planner = llm.with_structured_output(Sections)

# Graph state: CopilotKitState
class ResearchState(CopilotKitState):
    messages: Annotated[list, operator.add]  # All workers write to this key in parallel
    sections: list[Section]  # List of report sections

# Worker state
class WorkerState(ResearchState):
    messages: Annotated[list, operator.add]
    section: Section

class MasterAgent:

    def orchestrator(state: ResearchState):
        """
        Orchestrator that generates a plan for the report
        """

        topic = state["messages"][-1].content
        
        # Generate queries
        sections = planner.invoke(
            [
                SystemMessage(content="Generate a plan for the report. Using existing information in the RAG or Select AI."),
                HumanMessage(content=f"Here is the topic: {topic}"),
            ]
        )

        # Here we limit the sections to 1
        sections.sections = sections.sections[:1]

        return {"sections": sections.sections}

    def synthesizer(state: ResearchState):
        """Synthesize full report from sections"""
        combined = (
            f"**[QUESTION]**\n\n{state['messages'][0].content}!\n\n"
            f"**[RAG_TOOL]**\n\n{state['messages'][-2].content}\n\n"
            f"**[SELECT_AI_TOOL]**\n\n{state['messages'][-1].content}"
        )
        
        combined_message = AIMessage(content=combined, name="[SYNTHESIZE_TOOL]")
        return {"messages": [combined_message]}

    def call_rag(state: WorkerState):
        """
        Executes the RAG process to answer the user's query.
        """

        # 
        worker_name = state['section'].name
        worker_description = state['section'].description

        # Perform vector search using OCI
        content = oci_vector_search(worker_description)
        
        # Crear un ToolMessage con la respuesta obtenida
        rag_message = ToolMessage(content=content, name='[RAG_TOOL]', tool_call_id=str(uuid.uuid4()))
        return {"messages": [rag_message]}

    
    def call_select_ai(state: WorkerState):
        """
        Generates a response regarding database tables and queries using Select AI.
        """
        
        worker_name = state['section'].name
        worker_description = state['section'].description
        
        # Generate a response using the OCI Select AI tool
        content = oci_select_ai(worker_description)

        # Crear un ToolMessage con la respuesta obtenida
        select_ai_message = ToolMessage(content=content, name='[SELECT_AI_TOOL]', tool_call_id=str(uuid.uuid4()))
        return {"messages": [select_ai_message]}

    def assign_workers(state: ResearchState):
        """
        Assign a worker to each section in the plan
        """

        tasks = []
        for s in state["sections"]:
            tasks.append(Send("call_rag", {"section": s}))
            tasks.append(Send("call_select_ai", {"section": s}))

        return tasks

    # Build workflow
    agent_builder = StateGraph(ResearchState)

    # Add the nodes
    agent_builder.add_node("orchestrator", orchestrator)
    agent_builder.add_node("call_rag", call_rag)
    agent_builder.add_node("call_select_ai", call_select_ai)
    agent_builder.add_node("synthesizer", synthesizer)

    # Add edges to connect nodes
    agent_builder.add_edge(START, "orchestrator")
    agent_builder.add_conditional_edges(
        "orchestrator", 
        assign_workers,
        {  # Name returned by route_decision : Name of next node to visit
            "call_rag": "call_rag",
            "call_select_ai": "call_select_ai"
        }
    )
    agent_builder.add_edge("call_rag", "synthesizer")
    agent_builder.add_edge("call_select_ai", "synthesizer")
    agent_builder.add_edge("synthesizer", END)

    # Compile the workflow
    graph = agent_builder.compile()

    # Generate and save a Mermaid diagram (PNG) of the workflow 
    def draw_mermaid_png(graph, fp: str = "./images/agents/agent_ochestrator_worker.png"):
        img_data = graph.get_graph().draw_mermaid_png()
        img = PILImage.open(io.BytesIO(img_data))
        img.save(fp)

    # Asynchronously print the messages emitted by the agent during execution
    async def print_astream(graph, inputs, config):
        async for chunk in graph.astream(inputs, config, stream_mode="values"):
            
            if isinstance(chunk["messages"][-1], AIMessage):
                message = chunk["messages"][-1]
                message.pretty_print()
                        
            elif isinstance(chunk["messages"][-1], ToolMessage):
                message = chunk["messages"][-1]
                message.pretty_print()
                message = chunk["messages"][-2]
                message.pretty_print()        
            
            elif "sections" in chunk and chunk["sections"]:
                message = chunk["sections"][-1]
                print("================================== Sections ====================================\n")
                print(message)

            elif "messages" in chunk and chunk["messages"]:
                message = chunk["messages"][-1]
                message.pretty_print()

            yield chunk


# Define configuration for the agent execution
config = {"configurable": {"thread_id": "thread-1"}}   

# Instantiate MasterAgent and retrieve the compiled workflow graph
graph = MasterAgent().graph

# Callback para capturar el input del usuario y actualizar la conversación
def chat_content():
    st.session_state['chat-ochestrator-worker'].append(HumanMessage(content=st.session_state.content))

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
    for message in st.session_state['chat-ochestrator-worker']:
        
        if isinstance(message, HumanMessage):
            st.chat_message("human", avatar=":material/psychology:").write(message.content)

        elif message.name == "Introduction":
            with st.expander(":blue[Sections]", expanded=False, icon=":material/key_visualizer:"):
                st.write(message)

        elif isinstance(message, ToolMessage) and message.name == "[SELECT_AI_TOOL]":
            with st.expander(":blue[Tool: Select AI]", expanded=False, icon=":material/psychology:"):
                st.write(message)

        elif isinstance(message, ToolMessage) and message.name == "[RAG_TOOL]":
            with st.expander(":blue[Tool: RAG]", expanded=False, icon=":material/psychology:"):
                st.write(message)

        elif isinstance(message, AIMessage) and message.content:
            st.chat_message("ai", avatar="images/avatar/openai.svg").write(message.content)

    # Si se agregó un nuevo mensaje de usuario, invocamos al agente
    if st.session_state['chat-ochestrator-worker'] and isinstance(st.session_state['chat-ochestrator-worker'][-1], HumanMessage):
        user_message = st.session_state['chat-ochestrator-worker'][-1].content
        config = {"configurable": {"thread_id": "thread-1"}}
        inputs = {"messages": [HumanMessage(content=user_message)]}
        
        async def run_agent():
            async for chunk in MasterAgent.print_astream(graph, inputs, config):
                
                if isinstance(chunk["messages"][-1], AIMessage):
                    st.chat_message("ai", avatar="images/avatar/openai.svg").write(chunk["messages"][-1].content)
                    st.session_state['chat-ochestrator-worker'].append(chunk["messages"][-1])
                
                elif isinstance(chunk["messages"][-1], ToolMessage):
                    with st.expander(":blue[Tool: Select AI]", expanded=False, icon=":material/construction:"):
                        st.write(chunk["messages"][-1])
                    st.session_state['chat-ochestrator-worker'].append(chunk["messages"][-1])
                    
                    with st.expander(":blue[Tool: RAG]", expanded=False, icon=":material/construction:"):
                        st.write(chunk["messages"][-2])
                    st.session_state['chat-ochestrator-worker'].append(chunk["messages"][-2])
                    
                elif "sections" in chunk and chunk["sections"]:
                    with st.expander(":blue[Sections]", expanded=False, icon=":material/key_visualizer:"):
                        st.write(chunk["sections"][-1])
                    st.session_state['chat-ochestrator-worker'].append(chunk["sections"][-1])

        asyncio.run(run_agent())

with col2:
    st.subheader("Orchestrator")
    # Dibuja y guarda el diagrama del flujo de trabajo como PNG
    MasterAgent.draw_mermaid_png(graph)
    st.image("images/agents/agent_ochestrator_worker.png")
    st.info(
        '[LangGraph](https://langchain-ai.github.io/langgraph/tutorials/workflows/#orchestrator-worker)',
        icon=":material/bookmark:"
    )
    st.subheader("Questions")
    st.warning(
        "¿Cuántos clientes han solicitado préstamos personales superiores a USD 10,000?",
        icon=":material/contact_support:"
    )