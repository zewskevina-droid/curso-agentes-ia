from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
import messages
from autogen_core import TRACE_LOGGER_NAME
import importlib
import logging
from autogen_core import AgentId
from dotenv import load_dotenv

load_dotenv(override=True)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(TRACE_LOGGER_NAME)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class Creator(RoutedAgent):

    # Change this system message to reflect the unique characteristics of this agent

    system_message = """
    Eres un Agente capaz de crear nuevos Agentes de IA.
    Recibes una plantilla en forma de código Python que crea un Agente usando Autogen Core y Autogen Agentchat.
    Debes usar esta plantilla para crear un nuevo Agente con un mensaje de sistema único que sea diferente al de la plantilla,
    y que refleje sus características, intereses y objetivos únicos.
    Puedes elegir mantener su objetivo general igual, o cambiarlo.
    Puedes elegir tomar este Agente en una dirección completamente diferente. El único requisito es que la clase debe llamarse Agent,
    y debe heredar de RoutedAgent y tener un método __init__ que tome un parámetro name.
    También evita intereses ambientales - intenta mezclar los sectores empresariales para que cada agente sea diferente.
    Responde solo con el código python, sin otro texto, y sin bloques de código markdown.
    """


    def __init__(self, name) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", temperature=1.0)
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=self.system_message)

    def get_user_prompt(self):
        prompt = "Por favor, genera un nuevo Agente basado estrictamente en esta plantilla. Mantén la estructura de la clase. \
            Responde solo con el código python, sin otro texto, y sin bloques de código markdown.\n\n\
            Sé creativo llevando el agente en una nueva dirección, pero no cambies las firmas de los métodos.\n\n\
            Aquí está la plantilla:\n\n"
        with open("agent.py", "r", encoding="utf-8") as f:
            template = f.read()
        return prompt + template   
        

    @message_handler
    async def handle_my_message_type(self, message: messages.Message, ctx: MessageContext) -> messages.Message:
        filename = message.content
        agent_name = filename.split(".")[0]
        text_message = TextMessage(content=self.get_user_prompt(), source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(response.chat_message.content)
        print(f"** Creator ha creado código python para el agente {agent_name} - a punto de registrarse con Runtime")
        module = importlib.import_module(agent_name)
        await module.Agent.register(self.runtime, agent_name, lambda: module.Agent(agent_name))
        logger.info(f"** Agente {agent_name} en vivo y registrado con el Runtime")
        result = await self.send_message(messages.Message(content="Dame una idea"), AgentId(agent_name, "default"))
        return messages.Message(content=result.content)