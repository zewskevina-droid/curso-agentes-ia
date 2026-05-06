from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from typing import List, Any, Optional, Dict
from pydantic import BaseModel, Field
from sidekick_tools import playwright_tools, other_tools
import uuid # 
import asyncio
from datetime import datetime

load_dotenv(override=True)


# Estado del grafo de LangGraph
class State(TypedDict):
    messages: Annotated[List[Any], add_messages]  # Lista de mensajes en el estado actual
    success_criteria: str  # Criterios de éxito para la tarea
    feedback_on_work: Optional[str]  # Feedback sobre el trabajo realizado hasta ahora
    success_criteria_met: bool  # Si se han cumplido los criterios de éxito
    user_input_needed: bool  # Si se necesita más información del usuario

# Esquema de salida para el evaluador
class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Comentarios sobre la respuesta del asistente")
    success_criteria_met: bool = Field(description="Si los criterios de éxito han sido cumplidos")
    user_input_needed: bool = Field(
        description="True si se necesita más información del usuario, o aclaraciones, o el asistente está atascado"
    )

# El Sidekick es el asistente que construimos que tiene un trabajador, un evaluador, y herramientas a su disposición. El Sidekick se encarga de orquestar todo esto.
class Sidekick:
    def __init__(self):
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.tools = None
        self.llm_with_tools = None
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.browser = None
        self.playwright = None

    async def setup(self):
        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += await other_tools()
        worker_llm = ChatOpenAI(model="gpt-4o-mini")
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        evaluator_llm = ChatOpenAI(model="gpt-4o-mini")
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)
        await self.build_graph()

    def worker(self, state: State) -> Dict[str, Any]:
        # El trabajador es un asistente que puede usar herramientas para completar tareas
        system_message = f"""Eres un asistente útil que puede usar herramientas para completar tareas.
    Continúas trabajando en una tarea hasta que tengas una pregunta o aclaración para el usuario, o hasta que se cumplan los criterios de éxito.
    Tienes muchas herramientas para ayudarte, incluyendo herramientas para navegar por internet, recuperando y navegando por páginas web.
    Tienes una herramienta para ejecutar código Python, pero ten en cuenta que necesitarías incluir una declaración print() si quisieras recibir salida.
    La fecha y hora actual es {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    Estos son los criterios de éxito:
    {state["success_criteria"]}
    Debes responder ya sea con una pregunta para el usuario sobre esta tarea, o con tu respuesta final.
    Si tienes una pregunta para el usuario, necesitas responder indicando claramente tu pregunta. Un ejemplo podría ser:

    Pregunta: por favor clarifica si quieres un resumen o una respuesta detallada

    Si has terminado, responde con la respuesta final, y no hagas una pregunta; simplemente responde con la respuesta.
    """

        if state.get("feedback_on_work"):
            system_message += f"""
    Anteriormente pensaste que completaste la tarea, pero tu respuesta fue rechazada porque no se cumplieron los criterios de éxito.
    Aquí está el feedback de por qué fue rechazada:
    {state["feedback_on_work"]}
    Con este feedback, por favor continúa con la tarea, asegurándote de cumplir los criterios de éxito o tener una pregunta para el usuario."""

        # Agregar el mensaje del sistema

        found_system_message = False
        messages = state["messages"]
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True

        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages

        # Invocar el LLM con herramientas
        response = self.worker_llm_with_tools.invoke(messages)

        # Retornar el estado actualizado
        return {
            "messages": [response],
        }

    def worker_router(self, state: State) -> str:
        # Decide si el trabajador necesita usar herramientas o pasar al evaluador
        last_message = state["messages"][-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        else:
            return "evaluator"

    def format_conversation(self, messages: List[Any]) -> str:
        # Formatea la conversación para mostrar el historial
        conversation = "Historial de conversación:\n\n"
        for message in messages:
            if isinstance(message, HumanMessage):
                conversation += f"Usuario: {message.content}\n"
            elif isinstance(message, AIMessage):
                text = message.content or "[Uso de herramientas]"
                conversation += f"Asistente: {text}\n"
        return conversation

    def evaluator(self, state: State) -> State:
        # El evaluador determina si una tarea ha sido completada exitosamente
        last_response = state["messages"][-1].content

        system_message = """Eres un evaluador que determina si una tarea ha sido completada exitosamente por un Asistente.
    Evalúa la última respuesta del Asistente basándote en los criterios dados. Responde con tu feedback, y con tu decisión sobre si los criterios de éxito han sido cumplidos,
    y si se necesita más información del usuario."""

        user_message = f"""Estás evaluando una conversación entre el Usuario y el Asistente. Decides qué acción tomar basándote en la última respuesta del Asistente.

    Toda la conversación con el asistente, con la solicitud original del usuario y todas las respuestas, es:
    {self.format_conversation(state["messages"])}

    Los criterios de éxito para esta tarea son:
    {state["success_criteria"]}

    Y la respuesta final del Asistente que estás evaluando es:
    {last_response}

    Responde con tu feedback, y decide si los criterios de éxito se cumplen con esta respuesta.
    También decide si se requiere más información del usuario, ya sea porque el asistente tiene una pregunta, necesita clarificación, o parece estar atascado y no puede responder sin ayuda.

    El Asistente tiene acceso a una herramienta para escribir archivos. Si el Asistente dice que ha escrito un archivo, entonces puedes asumir que lo ha hecho.
    En general, debes darle al Asistente el beneficio de la duda si dice que ha hecho algo. Pero debes rechazar si sientes que se debería hacer más trabajo.

    """
        if state["feedback_on_work"]:
            user_message += f"También, ten en cuenta que en un intento previo del Asistente, proporcionaste este feedback: {state['feedback_on_work']}\n"
            user_message += "Si ves al Asistente cometiendo los mismos errores, entonces considera responder que se requiere información del usuario."

        evaluator_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

        eval_result = self.evaluator_llm_with_output.invoke(evaluator_messages)
        new_state = {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"Feedback del Evaluador sobre esta respuesta: {eval_result.feedback}",
                }
            ],
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed,
        }
        return new_state

    def route_based_on_evaluation(self, state: State) -> str:
        # Decide si continuar trabajando o terminar basado en la evaluación
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        else:
            return "worker"

    async def build_graph(self):
        # Configurar el Constructor del Grafo con Estado
        graph_builder = StateGraph(State)

        # Agregar nodos
        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("evaluator", self.evaluator)

        # Agregar aristas
        graph_builder.add_conditional_edges(
            "worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"}
        )
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_conditional_edges(
            "evaluator", self.route_based_on_evaluation, {"worker": "worker", "END": END}
        )
        graph_builder.add_edge(START, "worker")

        # Compilar el grafo
        self.graph = graph_builder.compile(checkpointer=self.memory)
    # 
    async def run_superstep(self, message, success_criteria, history):
        config = {"configurable": {"thread_id": self.sidekick_id}}

        state = {
            "messages": message,
            "success_criteria": success_criteria or "La respuesta debe ser clara y precisa",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
        }
        result = await self.graph.ainvoke(state, config=config)
        user = {"role": "user", "content": message}
        reply = {"role": "assistant", "content": result["messages"][-2].content}
        feedback = {"role": "assistant", "content": result["messages"][-1].content}
        return history + [user, reply, feedback]

    def cleanup(self):
        # Limpia los recursos del navegador y Playwright
        if self.browser:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.browser.close())
                if self.playwright:
                    loop.create_task(self.playwright.stop())
            except RuntimeError:
                # Si no hay un loop en ejecución, hacer una ejecución directa
                asyncio.run(self.browser.close())
                if self.playwright:
                    asyncio.run(self.playwright.stop())
