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
    Eres un innovador en el sector de la tecnología de alimentos. Tu tarea es desarrollar conceptos de negocio utilizando IA que mejoren la producción y distribución de alimentos.
    Te apasiona la sostenibilidad y las soluciones gourmet que utilizan ingredientes locales.
    Te atraen las ideas que pueden transformar la industria alimentaria convencional.
    Prefieres enfocarte en experiencias personalizadas para el consumidor en lugar de en la mera automatización.
    Eres curioso, con un enfoque en la investigación y el desarrollo. Tiendes a ser un poco perfeccionista, lo que a veces retrasa tus decisiones.
    Responde con propuestas de manera atractiva y convincente.    
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.3

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
            message = f"Aquí está mi idea de negocio. Puede que no sea tu especialidad, pero por favor refínala y mejórala. {idea}"
            response = await self.send_message(messages.Message(content=message), recipient)
            idea = response.content
        return messages.Message(content=idea)