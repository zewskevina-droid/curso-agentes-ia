from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import os
import resend


class ResendEmailInput(BaseModel):
    to_email: str = Field(..., description="Correo destino")
    subject: str = Field(..., description="Asunto del correo")
    html_content: str = Field(..., description="Contenido HTML del correo")


class ResendEmailTool(BaseTool):
    name: str = "send_email_resend"
    description: str = "Envía un correo electrónico usando Resend"
    args_schema: Type[BaseModel] = ResendEmailInput

    def _run(self, to_email: str, subject: str, html_content: str) -> str:
        api_key = os.getenv("RESEND_APY")
        if not api_key:
            raise ValueError("La variable de entorno RESEND_APY no está definida")

        resend.api_key = api_key

        response = resend.Emails.send({
            "from": "onboarding@resend.dev",  # cámbialo por tu dominio verificado
            "to": "zews.kevina@gmail.com",
            "subject": subject,
            "html": html_content,
        })

        return f"Correo enviado correctamente. ID: {response.get('id')}"
