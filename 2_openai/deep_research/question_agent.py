from pydantic import BaseModel, Field
from agents import Agent

class Question(BaseModel):
    question: str = Field(
        description="Preguntara realizada con por la IA para clarificar la investigacion"
    )
    response: str = Field(
        description="Respuesta del usuario, que se utilizara para clarificar la investigacion"
    )

class QuestionResponse(BaseModel):
    questions: list[Question] = Field(
        description="Tres preguntas clave para aclarar el alcance de la investigación, con sus respuestas."
    )

INSTRUCTIONS = """
Eres un asistente experto en clarificar investigaciones.
Tu tarea es formular tres preguntas relevantes y específicas que ayuden a entender mejor el contexto,
el alcance y el propósito del tema proporcionado por el usuario.
"""

question_agent = Agent(
    name="QuestionAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=QuestionResponse,
)
