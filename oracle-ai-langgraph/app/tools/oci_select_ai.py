from dotenv import load_dotenv
import services.database as database
import services as service

# Crear una instancia del servicio
select_ai_service = service.SelectAIService()
db_select_ai_service = database.SelectAIService()

# Load environment variables from the .env file
load_dotenv()

def oci_select_ai(input: str):
    """
    Generates an explanation for a SQL query using Oracle's SELECT AI service.
    
    Args:
        input (str): The input query or description for generating the SQL explanation.
        
    Returns:
        str: The generated explanation in Spanish, formatted in markdown.
    """
    
    language     = "Spanish"
    user_id      = 0
    profile_name = select_ai_service.get_profile(user_id)

    narrate = db_select_ai_service.get_chat(
        input,
        profile_name,
        "narrate",
        language
    )

    showsql = db_select_ai_service.get_chat(
        input,
        profile_name,
        "showsql",
        language
    )

    explainsql = db_select_ai_service.get_chat(
        showsql,
        profile_name,
        "explainsql",
        language
    )

    content = f"Narrate:\n\n {narrate}\n\n ExplainSQL:\n\n {explainsql}"

    return content