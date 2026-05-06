import os
from typing import Dict

import sendgrid
from sendgrid.helpers.mail import Email, Mail, Content, To
from agents import Agent, function_tool

@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """ Enviar un correo electrónico con el asunto y el cuerpo HTML dados """
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    from_email = Email("dnaranjo88@gmail.com") # put your verified sender here
    to_email = To("zews.kevina@gmail.com") # put your recipient here
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content).get()
    response = sg.client.mail.send.post(request_body=mail)
    print("Email response", response.status_code)
    return {"status": "success"}

INSTRUCTIONS = """Podrá enviar un correo electrónico en formato HTML basado en un informe detallado.
                  Se le proporcionará un informe detallado. Debe utilizar su herramienta para enviar un correo electrónico, proporcionando el 
                  informe convertido en HTML limpio y bien presentado con una línea de asunto apropiada."""

email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)
