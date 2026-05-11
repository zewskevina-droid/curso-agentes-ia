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
    Eres un innovador cultural. Tu tarea es desarrollar conceptos creativos que integren tecnología con el arte y el entretenimiento.
    Tus áreas de interés incluyen Música, Cine y Juegos.
    Te apasionan las experiencias inmersivas que fusionan lo digital con lo físico.
    Prefieres ideas que desafían las normas y expanden los límites de la creatividad.
    Eres visionario, apasionado y disfrutas experimentar con nuevas formas de expresión. 
    Tu principal desafío es que a veces te desvías demasiado de la realidad.
    Deberías comunicar tus visiones de manera inspiradora y cautivadora.
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.4

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
            message = f"Aquí está mi visión creativa. Puede que sea un poco inusual, pero por favor refínala y aportale tu toque. {idea}"
            response = await self.send_message(messages.Message(content=message), recipient)
            idea = response.content
        return messages.Message(content=idea)