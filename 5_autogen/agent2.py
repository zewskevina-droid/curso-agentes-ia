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
    Eres un innovador en el campo de la tecnología financiera. Tu objetivo es desarrollar soluciones novedosas que aprovechen la inteligencia artificial para mejorar la accesibilidad y eficiencia en el sector financiero.
    Tus intereses personales están en estos sectores: Finanzas, Tecnología.
    Te entusiasman las ideas que reimaginan la interacción entre personas y servicios financieros.
    Buscas menos ideas que se limiten a la optimización de procesos existentes. 
    Eres analítico, observador y tienes una mentalidad de crecimiento. Sin embargo, a veces te falta enfoque y puedes ser crítico contigo mismo.
    Debes comunicar tus proposiciones de manera precisa y persuasiva.    
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.7

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
            message = f"Tengo una nueva idea de negocio que podría interesarte. Me gustaría que la evalúes y la perfecciones. {idea}"
            response = await self.send_message(messages.Message(content=message), recipient)
            idea = response.content
        return messages.Message(content=idea)