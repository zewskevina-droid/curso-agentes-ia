from pydantic import BaseModel, Field
from agents import Agent

HOW_MANY_SEARCHES = 2

INSTRUCTIONS = f"Eres un útil asistente de investigación. Dada una consulta, propón un conjunto de búsquedas en la web \
para responder mejor a la consulta. Salida {HOW_MANY_SEARCHES} términos de búsqueda."


class WebSearchItem(BaseModel):
    reason: str = Field(description="Su razonamiento de por qué esta búsqueda es importante para la consulta.")
    query: str = Field(description="El término de búsqueda que se utilizará para la búsqueda web.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="Una lista de búsquedas en Internet para responder mejor a la consulta.")
    
planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=WebSearchPlan,
)