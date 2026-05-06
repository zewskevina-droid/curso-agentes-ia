from agents import Agent, WebSearchTool, ModelSettings

INSTRUCTIONS = (
    "Usted es un asistente de investigación. Dado un término de búsqueda, busca ese término en la web y "
    "un resumen conciso de los resultados. El resumen debe tener de 2 a 3 párrafos y menos de 300 "
    "palabras. Capta los puntos principales. Escriba sucintamente, no es necesario que tenga oraciones completas o buena "
    "gramática. Esto lo leerá alguien que sintetice un informe, así que es vital que captes la "
    "esencia e ignorar cualquier palabrería. No incluyas más comentarios que el propio resumen"


)

search_agent = Agent(
    name="Search agent",
    instructions=INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)