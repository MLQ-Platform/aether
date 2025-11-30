from contextlib import redirect_stdout
from io import StringIO
from aether.llm.agent.tools.registry import registry
from aether.provider import InMemoryDataProvider

provider = InMemoryDataProvider()


@registry.decorator(
    name="execute_python",
    description="Execute Python code for data analysis with 30s timeout. Available in context: df (DataFrame with market data), pd (pandas), np (numpy), sp (scipy). Variables defined in previous executions within the same agent iteration persist across calls. The code should assign results to a variable named 'result' which will be returned.",
    parameters={
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python code to execute. Must assign final output to 'result' variable. Variables defined in previous executions within the same agent iteration persist (df, pd, np, sp are pre-imported).",
            }
        },
        "required": ["code"],
    },
    agent_name="rationale",
)
def execute_python(code: str, exec_context: dict = None) -> tuple[str, dict]:
    """
    Execute Python code in a controlled environment with persistent context

    Args:
        code: Python code to execute
        exec_context: Execution context dictionary (if None, creates new context)
                      Context persists across iterations within the same coroutine (claim)
    """

    df = provider.get("BTCUSDT")

    if df is None:
        # Return tuple even for errors
        error_msg = "Error: DataFrame 'df' not found in context"
        return error_msg, exec_context if exec_context is not None else {}

    if exec_context is None:
        import numpy as np
        import pandas as pd
        import scipy as sp

        exec_context = {
            "df": df,
            "pd": pd,
            "np": np,
            "sp": sp,
        }

    # Reset result for each execution
    exec_context["result"] = None

    # Capture stdout
    f = StringIO()
    try:
        with redirect_stdout(f):
            exec(code, exec_context)

    except Exception as e:
        output = f"Error executing code: {str(e)}"
        return output, exec_context

    stdout_output = f.getvalue()
    result = exec_context.get("result", None)

    # Format output
    output_parts = []
    if stdout_output:
        output_parts.append(f"Output:\n{stdout_output}")

    if result is not None:
        output_parts.append(f"Result:\n{str(result)}")

    output = "\n".join(output_parts)
    return output, exec_context
