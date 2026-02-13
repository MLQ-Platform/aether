import threading
import warnings
from contextlib import redirect_stdout
from io import StringIO
from aether.llm.react.tools.base import Tool

# Lock to make redirect_stdout thread-safe across concurrent exec() calls.
# Only the exec() portion is serialized; LLM API calls still run in parallel.
_stdout_lock = threading.Lock()


def pyexecutor(code: str, exec_context: dict | None = None) -> tuple[str, dict]:
    """
    Python Code Executor

    Args:
        code: Python code to execute
        exec_context: Execution context dictionary (if None, creates new context)
                      Context persists across iterations within the same coroutine (claim)
    """
    if exec_context is None:
        exec_context = {}

    if "df" not in exec_context:
        error_msg = "Error: DataFrame 'df' not found in context"
        return error_msg, exec_context

    if "np" not in exec_context:
        import numpy as np
        import pandas as pd
        import scipy as sp

        exec_context["np"] = np
        exec_context["pd"] = pd
        exec_context["sp"] = sp

    # Reset result for each execution
    exec_context["result"] = None

    buf = StringIO()
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with _stdout_lock:
                with redirect_stdout(buf):
                    exec(code, exec_context)

    except Exception as e:
        output = f"Error executing code: {str(e)}"
        return output, exec_context

    stdout_output = buf.getvalue()
    result = exec_context.get("result", None)

    # Clean up intermediate variables to prevent memory accumulation
    # Keep only essential context: df, np, pd, sp, result
    essential_keys = {"df", "np", "pd", "sp", "result"}
    keys_to_remove = [k for k in exec_context.keys() if k not in essential_keys]

    for key in keys_to_remove:
        del exec_context[key]

    # Format output
    output_parts = []
    if stdout_output:
        output_parts.append(f"Output:\n{stdout_output}")

    if result is not None:
        output_parts.append(f"Result:\n{str(result)}")

    output = "\n".join(output_parts)
    return output, exec_context


tools = [
    Tool(
        name="pyexecutor",
        description="Execute Python code for data analysis with 30s timeout. Available in context: df (DataFrame with market data), pd (pandas), np (numpy), sp (scipy). Variables defined in previous executions within the same agent iteration persist across calls. The code should assign results to a variable named 'result' which will be returned.",
        func=pyexecutor,
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
    )
]
