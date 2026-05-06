#!/usr/bin/env python
import sys
import warnings
import os
from datetime import datetime

from engineering_team.crew import EngineeringTeam

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)

requirements = """
Un sistema sencillo de gestión de cuentas para una plataforma de simulación bursátil.
El sistema debe permitir a los usuarios crear una cuenta, depositar fondos y retirar fondos.
El sistema debe permitir a los usuarios registrar que han comprado o vendido acciones, indicando la cantidad.
El sistema debe calcular el valor total de la cartera del usuario y las ganancias o pérdidas desde el depósito inicial.
El sistema debe poder informar de las tenencias del usuario en cualquier momento.
El sistema debe poder informar de las ganancias o pérdidas del usuario en cualquier momento.
El sistema debe poder enumerar las transacciones que el usuario ha realizado a lo largo del tiempo.
El sistema debe impedir que el usuario retire fondos que le dejen con un saldo negativo, o
 que compre más acciones de las que puede permitirse, o que venda acciones que no tiene.
 El sistema tiene acceso a una función get_share_price(symbol) que devuelve el precio actual de una acción e incluye una implementación de prueba que devuelve precios fijos para AAPL, TSLA y GOOGL.
"""
module_name = "accounts.py"
class_name = "Account"


def run():
    """
    Run the research crew.
    """
    inputs = {
        'requirements': requirements,
        'module_name': module_name,
        'class_name': class_name
    }

    # Create and run the crew
    result = EngineeringTeam().crew().kickoff(inputs=inputs)


if __name__ == "__main__":
    run()