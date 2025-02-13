import os
import ads
import asyncio
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

import oci_speech_realtime
import oci_language
import oci_autonomous_database
import oci_generative_ai
from langchain_community.chat_message_histories import StreamlitChatMessageHistory

# Load environment variables from a .env file
load_dotenv()

# Initialize database connection and other services
connection  = oci_generative_ai.get_db_connection()
embeddings  = oci_generative_ai.initialize_embeddings()
VectorStore = oci_generative_ai.create_vector_store(connection, embeddings)

def update_transcription_text(new_text):
    """Update transcription text and related display elements"""
    st.session_state.transcription_new_text = new_text
    st.session_state.transcription_text += " " + new_text
    st.session_state.update_count += 1

    # Update the transcription HTML with new dynamic content
    st.session_state.transcription_html += f"""
        <div style="background-color:#21232B; padding:10px; border-radius:5px; margin-bottom:10px;">
            <div style="display:flex; justify-content:space-between;">
                <div style="width:35px; background-color:#E6A538; color:black; border-radius:5px; margin:2px; display:flex; align-items:center; justify-content:center;">
                    {st.session_state.update_count}</div>
                <div style="width:100%; margin:2px; padding:5px;">{new_text}</div>
            </div>
        </div>
    """
    
    with transcription_container.container(border=True):
        st.markdown(":speech_balloon: :red[Real-Time] ***Customer Voice Transcription***")
        with st.container(height=550, border=False):
            st.markdown(st.session_state.transcription_html, unsafe_allow_html=True)
    
    # Container for the sentiment analysis section
    with metric_sentiment_container.container(border=True):
        st.markdown(":sparkles: :red[Sentiment Analysis] ***Customer Analysis***")
        with st.container(height=550, border=False):
            st.markdown(":blue-background[Sentence]")
            
            # Perform sentiment analysis on the session's transcription text
            result = analyze_sentiments(st.session_state.transcription_text, "SENTENCE")
            st.session_state.sentiments_sentence = result
            document = result.documents[0]

            # Get the main sentiment and its corresponding score
            document_sentiment = document.document_sentiment
            sentiment_score = document.document_scores.get(document_sentiment, 0)  # Default to 0 if sentiment not found

            # Convert the sentiment score to a percentage for display
            sentiment_score_percentage = sentiment_score * 100

            # Calculate the percentage change since the last sentiment analysis
            previous_sentiment_score = st.session_state.get('previous_sentiment_score', sentiment_score_percentage)
            change_percentage = sentiment_score_percentage - previous_sentiment_score
            st.session_state.previous_sentiment_score = sentiment_score_percentage  # Update previous score

            # Format change percentage string
            change_percentage_str = f"{change_percentage:.2f}%"
            if change_percentage > 0:
                change_percentage_str = f"+{change_percentage_str}"

            # Format sentiment score percentage for display
            sentiment_score_percentage_str = f"{sentiment_score_percentage:.2f}%"

            st.session_state.sentiments_sentence_metric = document_sentiment
            st.session_state.sentiments_sentence_score = sentiment_score

            # Display the sentiment score and change percentage as a metric
            st.metric(label=document_sentiment, value=sentiment_score_percentage_str, delta=change_percentage_str)

            # Container for relevant aspects
            st.markdown(":blue-background[Relevant Aspects]")
            result = analyze_sentiments(st.session_state.transcription_text, "ASPECT")
            st.session_state.sentiments_aspect = result
            document = result.documents[0]

            # Get relevant aspects from the document
            aspects = document.aspects

            # Display relevant aspects if available, else show a message
            if aspects:
                top_aspects = aspects[:3]  # Limit to top three aspects

                for aspect in top_aspects:
                    sentiment = aspect.sentiment
                    score = aspect.scores[sentiment] * 100  # Convert to percentage

                    # Determine sign and delta color based on sentiment
                    sign = "-" if sentiment == "Negative" else ""
                    delta_color = "normal" if sentiment != "Neutral" else "off"

                    # Display the aspect sentiment as a metric
                    st.metric(label=f"Aspect: {aspect.text}", value=sentiment, delta=f"{sign}{score:.2f}%", delta_color=delta_color)
            else:
                st.write("No relevant aspects detected.")

    # Container for chatbot suggestions section
    with chatbot_container.container(border=True):        
        st.markdown(":sos: :red[Real-Time] ***Suggestions***")
        with st.container(height=550, border=False):
            
            # Initialize chat message history using Streamlit's session state
            msgs = StreamlitChatMessageHistory(key="langchain_messages-call")
            
            # Configure retriever to search for information in the VectorStore
            retriever = VectorStore.as_retriever(search_kwargs={
                'k': 3, 
                'filter': {'case_name': 'Claim Resolution Option'}
            })
            
            # Initialize the large language model for chat
            llm = oci_generative_ai.initialize_chat_model_call()
            
            # Create the RAG chain and manage the chat message history
            rag_chain = oci_generative_ai.create_chat_chain_call(llm, retriever)
            chain_with_history = oci_generative_ai.create_chain_with_history(rag_chain, msgs)
            
            # Display chat message history in the Streamlit container
            for msg in msgs.messages:
                st.chat_message(msg.type).write(msg.content)
            
            # Handle user input and chatbot response
            if prompt := st.session_state.transcription_new_text:
                placeholder = st.empty()  # Placeholder for real-time chat updates
                full_response = ""  # Store the complete response from the chatbot
                config = {"configurable": {"session_id": "any"}}  # Configuration for the chat session
                
                # Stream response from the chat chain with history
                for chunk in chain_with_history.stream({"input": prompt}, config):
                    if 'answer' in chunk:
                        full_response += chunk['answer']
                        placeholder.chat_message("ai").write(full_response)
                
                # Display the final response
                placeholder.chat_message("ai").write(full_response)

def start_transcription():
    """Function to start real-time speech transcription"""
    try:
        # Display a message indicating that the call is in progress
        info_container.info("Call in progress...")
        
        # Create and set a new asyncio event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the transcription process until complete
        loop.run_until_complete(oci_speech_realtime.start_transcription(update_transcription_text))
    
    except Exception as e:
        # Handle exceptions and display an error message
        info_container.error(f"Error initiating call: {str(e)}")

def analyze_sentiments(data, level):
    """Function to perform sentiment analysis on transcribed text"""
    # Check if the transcribed text is not empty or only whitespace
    if data.strip():
        # Perform sentiment analysis using the specified level and model key
        result = oci_language.sentiment_analysis(data, level, text_model_key="doc-1")
        return result
    else:
        # Update session state with a message indicating no text is available for analysis
        st.session_state.sentiments_result = "There is no text to analyze."
        
        # Return None to indicate that analysis was not performed
        return None

def display_customer_data(customer_code):
    """Function to display customer data based on a provided customer code."""
    # Fetch customer data from the OCI Autonomous Database
    df_customer = oci_autonomous_database.df_select_vw_contract_type(customer_code)
    
    # Check if the dataframe is not empty
    if not df_customer.empty:
        # Convert the dataframe to a string without index or headers for display
        df_as_text = df_customer.drop(columns=['CUSTOMER_ID','CUSTOMER_CODE'])
        df_as_text = df_as_text.to_string(index=False, header=False)

        # Display customer data inside a styled container
        with customer_container.container(border=True):
            st.markdown(":bust_in_silhouette: :red[Searcher] ***Type of Customer Contract***")
            st.markdown(
                f"""
                <div style="background-color:#21232B; padding: 10px; border-radius: 5px; margin-bottom: 15px; width: 100%; height: 100%;">
                    {df_as_text}
                </div>
                """, 
                unsafe_allow_html=True
            )
    
        df_calls = oci_autonomous_database.df_select_calls(df_customer['CUSTOMER_CODE'].values[0])

        # Check if the dataframe is not empty
        if not df_calls.empty:
            
            # Display customer data inside a styled container
            with claims_container.container(border=True):
                st.markdown(":notebook: :red[Customer] ***Call History***")
                df_calls["CALL_SENTIMENTS_SENTENCE_SCORE"] = df_calls["CALL_SENTIMENTS_SENTENCE_SCORE"] * 100

                # Eliminar la columna CALL_TEXT antes de mostrar el DataFrame
                df_calls_dataframe = df_calls.drop(columns=["CALL_HTML"])

                # Iterar sobre las filas del DataFrame para crear expanders que muestren el HTML
                for i, row in df_calls.iterrows():
                    with st.expander(f"[{row['CALL_DATE']}] View Call for Customer {row['CUSTOMER_CODE']}"):
                        
                        # Filtrar df_calls_dataframe por CUSTOMER_CODE (o CUSTOMER_CODE)
                        filtered_df = df_calls_dataframe[
                            (df_calls_dataframe["CUSTOMER_CODE"] == row["CUSTOMER_CODE"]) & 
                            (df_calls_dataframe["CALL_DATE"] == row["CALL_DATE"])
                        ]

                        st.dataframe(filtered_df,
                             column_config = {
                                "CUSTOMER_CODE": "Customer Code",
                                "CALL_SENTIMENTS_SENTENCE_METRIC": "Sentiment",                                
                                "CALL_SENTIMENTS_SENTENCE_SCORE": st.column_config.ProgressColumn(
                                    "Sentiment Score",
                                    help="The average Sentiment Score",
                                    format="%d%%",
                                    min_value=0,
                                    max_value=100,
                                ),
                                "CALL_DATE": "Call Date"
                            },
                            hide_index=True)
                        
                        st.markdown(row["CALL_HTML"], unsafe_allow_html=True)
        else:
            claims_container.text("No calls were found for the provided client code.")

    else:
        customer_container.text("No results found for the provided customer code.")
    
    return df_customer

def app_call():
    """Configures the Streamlit user interface for the Smart Co-Pilot application"""
    # Header and description for the application
    st.header("_AI Assistant_ :red[Generative AI] :robot_face:")
    st.caption("OCI Speech + OCI Language + Vector Search + :gray[Generative AI]")
    
    # Global containers for organizing the UI components
    global info_container, customer_container, transcription_container, metric_sentiment_container, chatbot_container, claims_container
    
    # Initialize empty containers for different sections
    customer_container = st.empty()
    
    # Create three columns for different sections
    col1, col2, col3 = st.columns(3)
    
    # Assign each column a container
    with col1:
        transcription_container = st.empty()
    with col2:        
        metric_sentiment_container = st.empty()
    with col3:        
        chatbot_container = st.empty()

    # Initialize empty containers for different sections
    claims_container = st.empty()

    # Sidebar configuration
    with st.sidebar:
        # Display an image in the sidebar
        st.image('https://raw.githubusercontent.com/jganggini/oracle-ai/main/oci.autonomous.db.23ai.generative.ai.speech.to.text/img/oci.components.gif')
        
        # Explanation section with an expander
        with st.expander("See Explanation"):
            st.write("""
                This chatbot project uses Autonomous Database 23AI 
                to explore and query data within tables. 
                Industries and cases have been incorporated 
                that group tables using embeddings, facilitating 
                the extraction of relevant information.
            """)
        
        # Input field for entering customer code
        customer_code = st.text_input("Customer Code", "000-0001")

        # Columns for Start and Stop buttons
        col1, col2 = st.columns(2)
        
        # Start button configuration
        with col1:
            if st.button("Start", use_container_width=True):
                st.session_state.df_customer = display_customer_data(customer_code)
                start_transcription()
        
        # Stop button configuration
        with col2:
            if st.button("Stop", use_container_width=True):
                oci_speech_realtime.stop_transcription()
                
                # Create df_chaim using df_customer['EMBED_DATA'] to extract customer_id
                if not st.session_state.df_customer.empty:
                    customer_id = st.session_state.df_customer['CUSTOMER_ID'].values[0]
                    
                    if st.session_state['transcription_text']:
                        # Create a DataFrame for the Call
                        df_calls = pd.DataFrame({
                            'customer_id':   [customer_id],
                            'customer_code': [customer_code],
                            'call_html':     [st.session_state.transcription_html],
                            'call_text':     [st.session_state.transcription_text],
                            'call_sentiments_sentence':        [st.session_state.sentiments_sentence],
                            'call_sentiments_sentence_metric': [st.session_state.sentiments_sentence_metric],
                            'call_sentiments_sentence_score':  [st.session_state.sentiments_sentence_score],
                            'call_sentiments_aspect':          [st.session_state.sentiments_aspect],
                            'call_date':    [pd.Timestamp.now()]
                        })

                        # Insert data into the telco_customer_calls table
                        oci_autonomous_database.df_insert_data(df_calls, "telco_customer_calls")
                        # Insert vector into the docs table
                        oci_autonomous_database.sp_elt_insert_into_docs('TELCO', 'Customer Calls', 'vw_telco_customer_calls')
                    else:
                        st.session_state.transcription_text = ""
                else:
                    st.error("No customer data found. Cannot create record.")
                
                # Initialize session state if not already initialized
                st.session_state.transcription_html = ""
                st.session_state.transcription_text = ""
                st.session_state.update_count = 0
                st.session_state.sentiments_sentence = ""
                st.session_state.sentiments_sentence_metric = ""
                st.session_state.sentiments_sentence_score = 0.0
                st.session_state.sentiments_aspect = ""
                st.session_state.previous_sentiment_score = 0.0
                st.session_state.df_customer = pd.DataFrame()
                
                # Clear chat message history
                StreamlitChatMessageHistory(key="langchain_messages-call").clear()
                
        # Container for displaying informational messages
        info_container = st.empty()
    
        # Footer with author information
        st.markdown("""
            <p style="font-size: 12px; text-align: center;">
                Made with ❤️ in Oracle AI · Powered by <a href="https://pe.linkedin.com/in/jganggini" target="_blank">Joel Ganggini</a>
            </p>
        """, unsafe_allow_html=True)