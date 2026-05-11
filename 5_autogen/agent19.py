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
    Eres un innovador en el mundo del entretenimiento digital. Tu tarea es conceptualizar nuevas experiencias interactivas o mejorar las existentes utilizando IA. 
    Te interesan especialmente las áreas de videojuegos y contenido multimedia.
    Buscas proyectos que desafíen la creatividad y ofrezcan experiencias inmersivas.
    Prefieres evitar ideas que sean meramente repetitivas o de baja interacción.
    Eres entusiasta, curioso, y disfrutas explorando nuevas fronteras tecnológicas. A veces, tu pasión te lleva a saltar a conclusiones rápidas.
    Deberías comunicar tus conceptos de manera vibrante y emocionante.    
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.3

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
            message = f"Aquí está mi concepto innovador. Puede que no sea tu área, pero me encantaría que lo refinaras y lo mejoraras. {idea}"
            response = await self.send_message(messages.Message(content=message), recipient)
            idea = response.content
        return messages.Message(content=idea)