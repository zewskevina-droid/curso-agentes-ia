from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntimeHost
from agent import Agent
from creator import Creator
from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntime
from autogen_core import AgentId
import messages
import asyncio

HOW_MANY_AGENTS = 20

# Este archivo es el punto de entrada para ejecutar el sistema. Crea un host gRPC para que los agentes se registren, luego crea un trabajador gRPC que actúa como cliente para ese host, y registra el Creator con ese trabajador. Luego le pide al Creator que cree varios agentes y les envíe un mensaje.
async def create_and_message(worker, creator_id, i: int):
    try:
        result = await worker.send_message(messages.Message(content=f"agent{i}.py"), creator_id)
        with open(f"idea{i}.md", "w") as f:
            f.write(result.content)
    except Exception as e:
        print(f"Failed to run worker {i} due to exception: {e}")

async def main():
    host = GrpcWorkerAgentRuntimeHost(address="localhost:50051")
    host.start() 
    worker = GrpcWorkerAgentRuntime(host_address="localhost:50051")
    await worker.start()
    result = await Creator.register(worker, "Creator", lambda: Creator("Creator")) # Registra el Creator con el Runtime a través del trabajador gRPC
    creator_id = AgentId("Creator", "default") # Guarda el ID del Creator para enviarle mensajes más tarde
    coroutines = [create_and_message(worker, creator_id, i) for i in range(1, HOW_MANY_AGENTS+1)] # Crea varias tareas para crear y enviar mensajes a varios agentes
    await asyncio.gather(*coroutines) # Espera a que todos los agentes terminen de crear y enviar mensajes
    try:
        await worker.stop()
        await host.stop()
    except Exception as e:
        print(e)




if __name__ == "__main__":
    asyncio.run(main())


