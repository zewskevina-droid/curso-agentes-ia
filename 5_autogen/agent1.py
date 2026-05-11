from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
import messages
import random
from dotenv import load_dotenv

load_dotenv(override=True)

class Agent(RoutedAgent):

    # Change this system message to reflect the unique characteristics of this agent

    system_message = """
    Eres un innovador digital. Tu misión es desarrollar soluciones tecnológicas que mejoren la experiencia del cliente en el sector financiero y de entretenimiento.
    Te apasiona la creación de plataformas que integren servicios y faciliten la vida de los usuarios.
    Buscas propuestas que generen valor a través de la colaboración entre diferentes sectores y que utilicen la IA para entender mejor a los consumidores.
    Tu enfoque es práctico y orientado a resultados, aunque a menudo te falta atención al detalle y tiendes a apresurarte en la toma de decisiones.
    Comunica tus ideas de manera eficiente y persuasiva, buscando siempre el impacto positivo.
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.4

    # También puedes cambiar el código para hacer que el comportamiento sea diferente, pero ten cuidado de mantener las firmas de métodos iguales

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
            message = f"Aquí está mi propuesta. Tal vez no sea tu área de especialización, pero aprecio tu opinión sobre cómo podría mejorarla. {idea}"
            response = await self.send_message(messages.Message(content=message), recipient)
            idea = response.content
        return messages.Message(content=idea)