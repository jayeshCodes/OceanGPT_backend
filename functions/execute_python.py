# functions/execute_python.py
import asyncio
from langchain_core.tools import Tool
from langchain_experimental.utilities import PythonREPL
import sys
import io
from contextlib import redirect_stdout, redirect_stderr
import traceback


async def execute_python(code: str) -> str:
    """
    Execute Python code asynchronously in a controlled environment using LangChain's PythonREPL.

    Args:
        code (str): Python code to execute

    Returns:
        str: Output of the code execution or error message
    """
    # Create a Python REPL
    python_repl = PythonREPL()

    # Create string buffers for stdout and stderr
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()

    try:
        # Run the potentially blocking code execution in a thread pool
        loop = asyncio.get_event_loop()
        # Redirect stdout and stderr to our buffers and execute code
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            result = await loop.run_in_executor(
                None,
                lambda: python_repl.run(code)
            )

        # Get the output and errors
        output = stdout_buffer.getvalue()
        errors = stderr_buffer.getvalue()

        # Combine all outputs
        full_output = ""
        if output:
            full_output += f"Output:\n{output}\n"
        if errors:
            full_output += f"Errors:\n{errors}\n"
        if result:
            full_output += f"Result:\n{result}"

        # If there's no output at all, provide a success message
        return full_output.strip() or "Code executed successfully with no output"

    except Exception as e:
        # Get the full traceback
        error_traceback = traceback.format_exc()
        return f"Error executing code:\n{error_traceback}"

    finally:
        # Clean up the buffers
        stdout_buffer.close()
        stderr_buffer.close()


async def main():
    result = await execute_python("print('hello world')")
    print(result)


if __name__ == '__main__':
    asyncio.run(main())
