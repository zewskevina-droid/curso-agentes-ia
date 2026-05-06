#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from debate.crew import Debate

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Este archivo principal está destinado a ser una manera para que usted pueda ejecutar su
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    inputs = {
        'motion': 'Se necesitan leyes estrictas para regular los LLM',
    }
    
    try:
        result = Debate().crew().kickoff(inputs=inputs)
        print(result.raw)
    except Exception as e:
        raise Exception(f"Se ha producido un error al ejecutar la tripulación: {e}")
