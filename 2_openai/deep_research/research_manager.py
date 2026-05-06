from agents import Runner, trace, gen_trace_id,  function_tool, Agent
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
import asyncio

class ResearchManager:

    async def run(self, query: str):
        """ Ejecutar el proceso de investigación en profundidad, que da lugar a las actualizaciones de estado y al informe final."""
        trace_id = gen_trace_id()
        with trace("Rastro de investigación - Kevin", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            print("Starting research...")
            search_plan = await self.plan_searches(query)
            yield "Búsquedas previstas, empezando a buscar ..."     
            search_results = await self.perform_searches(search_plan)
            yield "Búsquedas completas, redacción del informe..."
            report = await self.write_report(query, search_results)
            yield "Informe redactado, envío de correo electrónico..."
            await self.send_email(report)
            yield "Correo electrónico enviado, investigación finalizada"
            yield report.markdown_report
        

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """ Planificar las búsquedas a realizar para la consulta """
        print("Búsquedas de planificación...")
        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )
        print(f"Realizará {len(result.final_output.searches)} búsquedas")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """ Realizar las búsquedas para la consulta """
        print("Buscando...")
        num_completed = 0
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            print(f"Buscando... {num_completed}/{len(tasks)} completed")
        print("Búsqueda finalizada")
        return results

    async def search(self, item: WebSearchItem) -> str | None:
        """ Realizar una búsqueda de la consulta """
        input = f"Término de búsqueda: {item.query}\nMotivo de la búsqueda: {item.reason}"
        try:
            result = await Runner.run(
                search_agent,
                input,
            )
            return str(result.final_output)
        except Exception:
            return None

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """ Escribir el informe para la consulta """
        print("Reflexión sobre el informe...")
        input = f"Original query: {query}\nResultados resumidos de la búsqueda: {search_results}"
        result = await Runner.run(
            writer_agent,
            input,
        )

        print("Finalizada la redacción del informe")
        return result.final_output_as(ReportData)
    
    async def send_email(self, report: ReportData) -> None:
        print("Correo electrónico...")
        result = await Runner.run(
            email_agent,
            report.markdown_report,
        )
        print("Correo electrónico enviado")
        return report
