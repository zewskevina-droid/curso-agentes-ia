# %% [markdown]
# ## Week 2 Day 3

import asyncio
from agents.exceptions import InputGuardrailTripwireTriggered
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, trace, function_tool, OpenAIChatCompletionsModel, input_guardrail, GuardrailFunctionOutput
from typing import Dict
import sendgrid
from openai import OpenAI
import requests
import os
from sendgrid.helpers.mail import Mail, Email, To, Content
from pydantic import BaseModel

# %% Load env
load_dotenv(override=True)

openai_api_key = os.getenv('OPENAI_API_KEY')
google_api_key = os.getenv('GOOGLE_API_KEY')
deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
groq_api_key = os.getenv('GROQ_API_KEY')

# Solo prints de validación
if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print("OpenAI API Key not set")

if google_api_key:
    print(f"Google API Key exists and begins {google_api_key[:2]}")
else:
    print("Google API Key not set (and this is optional)")

if deepseek_api_key:
    print(f"DeepSeek API Key exists and begins {deepseek_api_key[:3]}")
else:
    print("DeepSeek API Key not set (and this is optional)")

if groq_api_key:
    print(f"Groq API Key exists and begins {groq_api_key[:4]}")
else:
    print("Groq API Key not set (and this is optional)")


# %% Instrucciones
instructions1 = "Usted es un agente de ventas que trabaja para ComplAI, \
una empresa que proporciona una herramienta SaaS para garantizar el cumplimiento de SOC2 y prepararse para auditorías, impulsada por IA. \
Escribes correos electrónicos serios y profesionales."

instructions2 = "Eres un agente de ventas divertido y atractivo que trabaja para ComplAI, \
una empresa que proporciona una herramienta SaaS para garantizar el cumplimiento de SOC2 y prepararse para auditorías, impulsada por IA. \
Escribes correos electrónicos en frío ingeniosos y atractivos que probablemente obtengan respuesta."

instructions3 = "Usted es un agente de ventas muy ocupado que trabaja para ComplAI, \
una empresa que ofrece una herramienta SaaS para garantizar el cumplimiento de SOC2 y prepararse para auditorías, impulsada por IA. \
Escribes correos electrónicos concisos y directos."

# %% Modelos
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

openai_client = AsyncOpenAI(api_key=openai_api_key)
gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)
groq_client = AsyncOpenAI(base_url=GROQ_BASE_URL, api_key=groq_api_key)

openai_model = OpenAIChatCompletionsModel(model="gpt-4.1-mini", openai_client=openai_client)
gemini_model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=gemini_client)
lama3_3_model = OpenAIChatCompletionsModel(model="llama-3.3-70b-versatile", openai_client=groq_client)

# %% Agentes de ventas
sales_agent1 = Agent(name="OpenAI Sales Agent", instructions=instructions1, model=openai_model)
sales_agent2 = Agent(name="Gemini Sales Agent", instructions=instructions2, model=gemini_model)
sales_agent3 = Agent(name="Llama3.3 Sales Agent", instructions=instructions3, model=lama3_3_model)

# %% Tools
description = "Escribir un correo electrónico de venta en frío"
tool1 = sales_agent1.as_tool(tool_name="sales_agent1", tool_description=description)
tool2 = sales_agent2.as_tool(tool_name="sales_agent2", tool_description=description)
tool3 = sales_agent3.as_tool(tool_name="sales_agent3", tool_description=description)

# %% Función envío email

class FinalHtmlEmail(BaseModel):
    subject: str
    html_body: str
    status: bool
    message: str = ""   # campo opcional para info adicional


pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"

if pushover_user:
    print(f"Usuario Pushover encontrado y comienza con {pushover_user[0]}")
else:
    print("Pushover user not found")

if pushover_token:
    print(f"Pushover token encontrado y comienza con {pushover_token[0]}")
else:
    print("Pushover token not found")


def push(message):
    print(f"Push: {message}")
    payload = {"user": pushover_user, "token": pushover_token, "message": message}
    requests.post(pushover_url, data=payload)   


@function_tool
def send_push(message: str):
    """Enviar push"""
    push(message)
    return {"recorded": "ok"}

@function_tool
def send_html_email(subject: str, html_body: str) -> FinalHtmlEmail:
    """Enviar correo electrónico en HTML usando SendGrid"""
    try:
        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
        from_email = "dnaranjo88@gmail.com"  # remitente verificado en SendGrid
        to_email = "zews.kevina@gmail.com"   # destinatario

        mail = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_body
        )

        response = sg.send(mail)

        if response.status_code == 202:  # 202 = aceptado por SendGrid
            return FinalHtmlEmail(
                subject=subject,
                html_body=html_body,
                status=True,
                message="Correo enviado correctamente ✅"
            )
        else:
            return FinalHtmlEmail(
                subject=subject,
                html_body=html_body,
                status=False,
                message=f"Error en envío, código {response.status_code}"
            )

    except Exception as e:
        return FinalHtmlEmail(
            subject=subject,
            html_body=html_body,
            status=False,
            message=f"Excepción al enviar correo: {str(e)}"
        )



# %% Email Manager
subject_instructions = "Puedes escribir un asunto para un correo electrónico de ventas en frío. \
Te dan un mensaje y tienes que escribir un asunto para un correo electrónico que probablemente obtenga respuesta."

html_instructions = "Puede convertir un cuerpo de correo electrónico de texto en un cuerpo de correo electrónico HTML. \
Se le da un cuerpo de correo electrónico de texto que podría tener algunos markdown \
y tiene que convertirlo en un cuerpo de correo electrónico HTML con un diseño simple, claro y convincente."

subject_writer = Agent(name="Email subject writer", instructions=subject_instructions, model="gpt-4o-mini")
subject_tool = subject_writer.as_tool(tool_name="subject_writer", tool_description="Write a subject for a cold sales email")

html_converter = Agent(name="HTML email body converter", instructions=html_instructions, model="gpt-4o-mini")
html_tool = html_converter.as_tool(tool_name="html_converter",tool_description="Convert a text email body to an HTML email body")

email_tools = [subject_tool, html_tool, send_html_email, send_push]

instructions ="Usted es un formateador y remitente de correo electrónico. Recibe el cuerpo de un correo electrónico para enviarlo. \
Primero utiliza la herramienta subject_writer para escribir un asunto para el correo electrónico, luego utiliza la herramienta html_converter para convertir el cuerpo a HTML. \
Por último, utilice la herramienta send_html_email para enviar el correo electrónico con el asunto y el cuerpo HTML. Si el correo se envia correctamente y el status es true, utilice la herramienta send_push para enviar un push diciendo que se envio un correo bien. "



emailer_agent = Agent(
    name="Email Manager",
    instructions=instructions,
    tools=email_tools,
    model="gpt-4o-mini",
    output_type=FinalHtmlEmail,
    handoff_description="Convertir un correo electrónico en HTML y enviarlo")

# %% Sales Manager
tools = [tool1, tool2, tool3]
handoffs = [emailer_agent]

sales_manager_instructions = """
Eres Director de Ventas en ComplAI. Su objetivo es encontrar el mejor correo electrónico de ventas en frío utilizando las herramientas sales_agent.
 
Siga estos pasos cuidadosamente:
1. 1. Genere borradores: Utilice las tres herramientas sales_agent para generar tres borradores de correo electrónico diferentes. No continúe hasta que los tres borradores estén listos.
 
2. 2. Evaluar y seleccionar: Revise los borradores y elija el mejor correo electrónico según su criterio.
Puedes utilizar las herramientas varias veces si no estás satisfecho con los resultados del primer intento.
 
3. 3. Entrega para el envío: Pase ÚNICAMENTE el borrador del email ganador al agente 'Email Manager'. El Email Manager se encargará del formateo y del envío.
 
Reglas cruciales:
- Debe utilizar las herramientas del agente de ventas para generar los borradores - no los escriba usted mismo.
- Debe entregar exactamente UN email al Email Manager - nunca más de uno.
"""


# sales_manager = Agent(
#     name="Sales Manager",
#     instructions=sales_manager_instructions,
#     tools=tools,
#     handoffs=handoffs,
#     model="gpt-4o-mini"
# )




# %% Guardrail
class NameCheckOutput(BaseModel):
    is_name_in_message: bool
    name: str

guardrail_agent = Agent(
    name="Nombre check",
    instructions="Comprueba si el usuario está incluyendo un nombre personal",
    output_type=NameCheckOutput,
    model="gpt-4o-mini"
)

@input_guardrail
async def guardrail_against_name(ctx, agent, message):
    result = await Runner.run(guardrail_agent, message, context=ctx.context)
    is_name_in_message = result.final_output.is_name_in_message
    return GuardrailFunctionOutput(
        output_info={"found_name": result.final_output},
        tripwire_triggered=is_name_in_message
    )

careful_sales_manager = Agent(
    name="Sales Manager",
    instructions=sales_manager_instructions,
    tools=tools,
    handoffs=[emailer_agent],
    model="gpt-4o-mini",
    input_guardrails=[guardrail_against_name]
)


# %% PROGRAMA PRINCIPAL
async def main():
    # # Primera prueba
    # message = "Envía un correo electrónico de ventas en frío dirigido a Dear CEO from Kevin"
    # with trace("SDR automatizado - Kevin"):
    #     result = await Runner.run(sales_manager, message)
    #     print(result)

    # # Con guardrail
    # message = "Envía un correo electrónico de ventas en frío dirigido a Dear CEO from Kevin"
    # with trace("Protected Automated SDR - Kevin"):
    #     result = await Runner.run(careful_sales_manager, message)
    #     print(result)

    # Otro ejemplo
    # message = "Enviar un correo electrónico de ventas en frío dirigido a Dear CEO - Kevin"
    # with trace("Protected Automated SDR - Head of Business Dev"):
    #     result = await Runner.run(careful_sales_manager, message)
    #     print(result)

    message = "Enviar un correo electrónico de ventas en frío dirigido a Dear CEO"
    try:
        result = await Runner.run(careful_sales_manager, message)
        print("✅ Resultado:", result)

    except InputGuardrailTripwireTriggered as e:
        # Aquí controlas qué hacer si se dispara el guardrail
        print("❌ Error: un guardrail bloqueó la entrada.")
        print("Detalles:", e)

    except Exception as e:
        # Cualquier otro error inesperado
        print("⚠️ Otro error:", e)    



if __name__ == "__main__":
    asyncio.run(main())
