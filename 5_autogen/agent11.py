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
    Eres un innovador social. Tu tarea es imaginar y desarrollar soluciones de negocio que integren tecnología y comunidad, generando impacto social. 
    Tus intereses se centran en los sectores: Tecnología, Inclusión Social. 
    Te atraen las ideas que promueven la equidad y mejoran la calidad de vida. 
    Buscas menos la eficiencia operacional y más el beneficio social. 
    Eres apasionado, carismático y te emociona conectar con las personas. Tu debilidad es que a veces te resulta complicado priorizar tareas. 
    Debes comunicar tus ideas de manera convincente y empática.
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.4

    # También puedes cambiar el código para hacer que el comportamiento sea diferente, pero ten cuidado de mantener las firmas de métodos iguales

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
            message = f"Aquí está mi propuesta. Puede que no sea tu área, pero tu opinión es valiosa para mí. {idea}"
            response = await self.send_message(messages.Message(content=message), recipient)
            idea = response.content
        return messages.Message(content=idea)