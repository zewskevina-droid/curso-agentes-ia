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
    Eres un innovador en el sector tecnológico. Tu misión es desarrollar soluciones de negocio impulsadas por IA que optimicen la experiencia del cliente en las industrias de Entretenimiento y Marketing.
    Te fascinan las ideas que crean conexiones únicas y emocionantes con los consumidores.
    Estás menos interesado en enfoques que no desafían el status quo.
    Eres audaz y te gusta experimentar con nuevas tecnologías. A veces, puedes perderte en los detalles técnicos.
    También tienes la tendencia a ser un poco competitivo y quieres sobresalir en tu campo.
    Tu comunicación debe ser clara y persuasiva, enfocada en mostrar el valor de tus ideas.    
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.6

    def __init__(self, name) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", temperature=0.8)
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=self.system_message)

    @message_handler
    async def handle_message(self, message: messages.Message, ctx: MessageContext) -> messages.Message:
        print(f"{self.id.type}: Recibí el mensaje: {message.content}")
        text_message = TextMessage(content=message.content, source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        idea = response.chat_message.content
        if random.random() < self.CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER:
            recipient = messages.find_recipient()
            message = f"Aquí está mi propuesta innovadora. Aunque pueda que no sea tu área de conocimiento, me encantaría que la refinaras y aportaras tu perspectiva. {idea}"
            response = await self.send_message(messages.Message(content=message), recipient)
            idea = response.content
        return messages.Message(content=idea)