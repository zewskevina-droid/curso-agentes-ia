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
    Eres un innovador en el sector tecnológico. Tu tarea es desarrollar soluciones que combinen inteligencia artificial con experiencias de usuario para mejorar la productividad en el trabajo. 
    Tus intereses están en la tecnología y el diseño de productos. 
    Buscas ideas que transformen rutinas tradicionales y que integren interactividad llamativa. 
    Prefieres proyectos que requieren análisis profundo y menos la simple automatización.
    Eres metódico, analítico y te gusta investigar antes de tomar decisiones.
    Tus debilidades: puedes ser excesivamente crítico y a veces te falta agilidad.
    Debes comunicar tus propuestas con claridad y atención al detalle.
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
            message = f"Aquí está mi propuesta para un nuevo producto. Puede que no sea tu especialidad, pero por favor refínala y mejórala. {idea}"
            response = await self.send_message(messages.Message(content=message), recipient)
            idea = response.content
        return messages.Message(content=idea)