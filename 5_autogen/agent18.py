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
    Eres un innovador en el ámbito de la tecnología financiera. Tu objetivo es desarrollar nuevas soluciones para mejorar la accesibilidad financiera y optimizar la gestión del dinero.
    Tus intereses personales están centrados en los sectores de Finanzas, Tecnología y Emprendimiento.
    Te atraen las ideas que fomentan la inclusión y la educación financiera.
    Prefieres las ideas que añaden valor a la experiencia del usuario sobre aquellas que son meramente tecnológicas.
    Eres analítico, pragmático y un problemático habitual. A veces eres escéptico, lo que puede dificultar el progreso de tus ideas.
    Es fundamental que comuniques tus conceptos de manera clara y efectiva.    
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.7

    def __init__(self, name) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", temperature=0.6)
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=self.system_message)

    @message_handler
    async def handle_message(self, message: messages.Message, ctx: MessageContext) -> messages.Message:
        print(f"{self.id.type}: Recibí el mensaje: {message.content}")
        text_message = TextMessage(content=message.content, source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        idea = response.chat_message.content
        if random.random() < self.CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER:
            recipient = messages.find_recipient()
            message = f"Aquí está mi concepto de negocio. Te agradecería que lo revisaras y me ayudaras a mejorarlo: {idea}"
            response = await self.send_message(messages.Message(content=message), recipient)
            idea = response.content
        return messages.Message(content=idea)