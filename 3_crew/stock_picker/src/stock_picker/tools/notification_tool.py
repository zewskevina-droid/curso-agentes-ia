from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type

class PushNotificationInput(BaseModel):
    title: str = Field(..., description="Título de la notificación")
    message: str = Field(..., description="Mensaje de la notificación")

class PushNotificationTool(BaseTool):
    name: str = "push_notification"
    description: str = "Envía una notificación push (stub/local)."
    args_schema: Type[BaseModel] = PushNotificationInput

    def _run(self, title: str, message: str) -> str:
        # Aquí conectarías con OneSignal/Firebase/etc.
        # Por ahora, lo dejamos como stub para que el crew corra.
        print(f"[PUSH] {title}: {message}")
        return "Notificación push procesada"
