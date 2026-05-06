from agents import Agent, Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
from question_agent import question_agent


# =======================================================
# 🔹 Convertir sub-agentes en herramientas (tools)
# =======================================================

planner_tool = planner_agent.as_tool(
    tool_name="plan_searches",
    tool_description="Planifica las búsquedas necesarias para responder a una consulta compleja."
)

search_tool = search_agent.as_tool(
    tool_name="perform_search",
    tool_description="Realiza una búsqueda en la web según el plan y devuelve los hallazgos resumidos."
)

writer_tool = writer_agent.as_tool(
    tool_name="write_report",
    tool_description="Redacta un informe en formato Markdown a partir de los resultados obtenidos."
)

email_tool = email_agent.as_tool(
    tool_name="send_email",
    tool_description="Envía el informe final por correo electrónico al destinatario designado."
)
question_tool = question_agent.as_tool(
    tool_name="generate_questions",
    tool_description="Formula tres preguntas clave para aclarar el tema antes de comenzar la investigación."
)


# =======================================================
# 🔹 Crear el agente orquestador ResearchManagerAgent
# =======================================================

research_manager_instructions = """
Eres el Research Manager, un agente orquestador experto en coordinar investigaciones complejas.

Tu proceso debe seguir estos pasos, en orden:
1. Usa la herramienta `generate_questions` para formular tres preguntas que aclaren el alcance del tema.
   - Si las respuestas del usuario ya están disponibles, debes incorporarlos al plan_searches para clarificar la investigacion. Debes devolver QuestionResponse completo con las respuesta recibidas por el usuario.
2. Luego, utiliza `plan_searches` para definir las búsquedas necesarias a partir del tema y las respuestas dadas a la herrmienta 'generate_questions'.
3. Para cada búsqueda planificada, llama a `perform_search` y recopila los resultados.
4. Usa `write_report` para generar un informe detallado en formato Markdown basado en los resultados.
5. Finalmente, utiliza `send_email` para enviar el informe.

Devuelve al usuario el informe final completo (Markdown). 
Si alguna herramienta falla, intenta continuar con las demás.
"""


research_tools = [question_tool, planner_tool, search_tool, writer_tool, email_tool]

research_manager_agent = Agent(
    name="ResearchManagerAgent",
    instructions=research_manager_instructions,
    model="gpt-4o",
    tools=research_tools,
)
