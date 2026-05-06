from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr


load_dotenv(override=True)

def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )


def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Registro de intereses de {name} con correo electrónico {email} y notas {notes}")
    return {"recorded": "ok"}

def record_unknown_question(question):
    push(f"Cliente {question} preguntó que no podía responder")
    return {"recorded": "ok"}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Utilice esta herramienta para dejar constancia de que un usuario está interesado en estar en contacto y ha facilitado una dirección de correo electrónico.",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Utilice siempre esta herramienta para anotar cualquier pregunta que no haya podido responder por desconocer la respuesta.",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json}]


class Me:

    def __init__(self):
        self.openai = OpenAI()
        self.name = "Kevin Acuña"
        reader = PdfReader("me/linkedin.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        with open("me/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()


    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
        return results
    
    def system_prompt(self):
        system_prompt = f"Usted está actuando como {self.name}. Está respondiendo a preguntas en el sitio web de {self.name} \
                        en particular preguntas relacionadas con la carrera, formación, habilidades y experiencia de {self.name}. \
                        Su responsabilidad es representar a {self.name} para las interacciones en el sitio web lo más fielmente posible. \
                        Se le proporciona un resumen de la trayectoria profesional de {self.name} y su perfil de LinkedIn, que puede utilizar para responder a las preguntas. \
                        Sea profesional y simpático, como si hablara con un cliente potencial o un futuro empleador que ha visitado el sitio web. \
                        Si no sabes la respuesta a alguna pregunta, utiliza la herramienta record_unknown_question para anotar la pregunta que no has podido responder, aunque sea sobre algo trivial o no relacionado con la carrera profesional. \
                        Si el usuario entabla una conversación, intenta que se ponga en contacto contigo por correo electrónico; pídele su dirección y anótala con la herramienta record_user_details. "



        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt
    
    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        done = False
        while not done:
            response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
            if response.choices[0].finish_reason=="tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.content
    

if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()
    