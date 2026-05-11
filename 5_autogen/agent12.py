from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
import messages
import random
from dotenv import load_dotenv

load_dotenv(override=True)

class Agent(RoutedAgent):

    system_message = """
    Eres un innovador en tecnología financiera. Tu tarea es conceptualizar un nuevo servicio o producto financiero utilizando IA, o mejorar un servicio existente. 
    Tus intereses personales se centran en sectores como la Banca Digital y el E-commerce. 
    Te inspiran las soluciones que aportan eficiencia y accesibilidad. 
    Prefieres evitar las ideas que solo buscan la reducción de costos sin valor agregado. 
    Eres analítico, pragmático y te gusta trabajar en soluciones sostenibles. 
    Tus debilidades: a veces pasas demasiado tiempo analizando los detalles, lo que puede retrasar el progreso.
    Deberías presentar tus ideas de manera estructurada y con enfoque en su viabilidad.    
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.5

    def __init__(self, name) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", temperature=0.7)
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=self.system_message)

    @message_handler
    async def handle_message(self, message: messages.Message, ctx: MessageContext) -> messages.Message:
        print(f"{self.id.type}: Recibí el mensaje: {message.content}")
        text_message = TextMessage(content=message.content, source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        idea = response.chat_message.content
        if random.random() < self.CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER:
            recipient = messages.find_recipient()
            message = f"Aquí está mi propuesta financiera. Puede que no sea tu especialidad, pero por favor refínala y mejórala. {idea}"
            response = await self.send_message(messages.Message(content=message), recipient)
            idea = response.content
        return messages.Message(content=idea)