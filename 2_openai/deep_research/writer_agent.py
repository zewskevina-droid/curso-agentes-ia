from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = (
    "Usted es un investigador senior encargado de redactar un informe cohesionado para una consulta de investigación. "
    "Se le proporcionará la consulta original y una investigación inicial realizada por un asistente de investigación."
    "En primer lugar, debe elaborar un esquema para el informe que describa la estructura y el "
    "flujo del informe. A continuación, genere el informe y envíelo como resultado final."
    "El resultado final debe estar en formato markdown, y debe ser extenso y detallado. El objetivo "
    "5-10 páginas de contenido, al menos 1000 palabras."
)


class ReportData(BaseModel):
    short_summary: str = Field(description="Un breve resumen de 2-3 frases de las conclusiones.")

    markdown_report: str = Field(description="El informe final")

    follow_up_questions: list[str] = Field(description="Temas sugeridos para seguir investigando")


writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ReportData,
)