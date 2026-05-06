import os, asyncio, gradio as gr
from dotenv import load_dotenv
from agents import Runner, gen_trace_id, trace
from research_manager_agent import research_manager_agent

load_dotenv(override=True)

# ======================================================
# 🔹 Estado inicial del flujo
# ======================================================
INITIAL_STATE = {
    "fase": "inicio",
    "tema": None,
    "preguntas": [],
    "respuestas": [],
    "trace_id": None
}

# ======================================================
# 🔹 Flujo conversacional principal
# ======================================================
async def chat_flujo(mensaje_usuario: str, state: dict):
    mensajes_chat = []
    fase = state["fase"]
    trace_id = state.get("trace_id") or gen_trace_id()
    state["trace_id"] = trace_id

    # === FASE 1: Usuario indica tema ===
    if fase == "inicio":
        state["tema"] = mensaje_usuario.strip()
        state["fase"] = "preguntando"

        with trace("Generar preguntas", trace_id=trace_id):
            mensajes_chat.append(("assistant", f"Tema recibido: **{state['tema']}**"))
            mensajes_chat.append(("assistant", "Generando preguntas iniciales para precisar la investigación..."))

            result = await Runner.run(
                research_manager_agent,
                f"Tema a investigar: {state['tema']}. Solo genera las preguntas iniciales, sin realizar búsquedas todavía."
            )

            text = result.final_output.strip()
            state["preguntas"] = [
                p.strip() for p in text.split("\n") if p.strip().startswith(("1", "2", "3"))
            ]

            if state["preguntas"]:
                preguntas_texto = "\n".join(state["preguntas"])
                mensajes_chat.append((
                    "assistant",
                    f"Para poder enfocar la investigación sobre **{state['tema']}**, necesito aclarar algunas preguntas:\n\n{preguntas_texto}\n\nPor favor responde todas en un solo mensaje."
                ))
                state["fase"] = "respondiendo"
            else:
                mensajes_chat.append(("assistant", "⚠️ No se pudieron generar preguntas automáticamente. Intenta con otro tema."))

        yield mensajes_chat, state
        return  # <-- vacío, no con valor

    # === FASE 2: Usuario responde las preguntas ===
    elif fase == "respondiendo":
        state["respuestas"].append(mensaje_usuario.strip())
        state["fase"] = "investigando"
        mensajes_chat.append(("user", mensaje_usuario))
        mensajes_chat.append(("assistant", "Gracias. Iniciando investigación completa..."))

        contexto = (
            f"Tema: {state['tema']}\n\n"
            + "\n".join([
                f"Pregunta {i+1}: {state['preguntas'][i]}\nRespuesta: {r}"
                for i, r in enumerate(state['respuestas'])
            ])
        )

        # Ejecución normal (sin streaming)
        with trace("Investigación completa", trace_id=trace_id):
            try:
                result = await Runner.run(research_manager_agent, contexto)
                stream_text = result.final_output or ""
                if stream_text.strip():
                    mensajes_chat.append(("assistant", "✅ Investigación completada con éxito."))
                    mensajes_chat.append(("assistant", stream_text))
                else:
                    mensajes_chat.append(("assistant", "⚠️ No se generó un informe final válido."))
            except Exception as e:
                mensajes_chat.append(("assistant", f"❌ Error durante la investigación: {str(e)}"))

        yield mensajes_chat, state

        return  # sin valor

    # === FASE 3: Reinicio ===
    else:
        mensajes_chat.append(("assistant", "Puedes iniciar una nueva investigación escribiendo otro tema."))
        state.update(INITIAL_STATE)
        yield mensajes_chat, state
        return


# ======================================================
# 🔹 Interfaz de Chat en Gradio
# ======================================================
with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("## 🤖 Investigación en profundidad con IA")
    gr.Markdown("Indica un tema, responde preguntas y observa cómo el agente genera el informe en tiempo real.")

    chatbot = gr.Chatbot(label="Agente de Investigación", height=550, type="messages")
    entrada = gr.Textbox(placeholder="Escribe aquí tu mensaje...", label="Tu mensaje")
    estado = gr.State(INITIAL_STATE.copy())

    async def manejar_mensaje(mensaje_usuario, historial, estado):
        async for mensajes, nuevo_estado in chat_flujo(mensaje_usuario, estado):
            historial_actualizado = []
            for autor, texto in mensajes:
                role = autor if autor in ["user", "assistant"] else "assistant"
                historial_actualizado.append({"role": role, "content": texto})
            yield historial_actualizado, nuevo_estado, ""

    entrada.submit(
        manejar_mensaje,
        inputs=[entrada, chatbot, estado],
        outputs=[chatbot, estado, entrada],
    )

ui.launch(inbrowser=True, share=False)
