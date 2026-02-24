import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import io
import contextlib
import traceback
import uuid
from langchain_core.tools import tool

plt.show = lambda: None 
global_df = None

def set_global_df(df: pd.DataFrame):
    """Updates the dataframe the tool operates on."""
    global global_df
    global_df = df

@tool
def execute_pandas_code(code: str) -> dict:
    """
    Executes Python code using Pandas and Matplotlib.
    The dataframe is loaded as a variable named 'df'.
    Always use 'df' to refer to the dataframe.
    """
    global global_df
    
    if global_df is None:
        return {"error": "No dataframe loaded."}
    local_vars = {
        'df': global_df,
        'pd': pd,
        'plt': plt
    }

    output_buffer = io.StringIO()
    
    try:
        with contextlib.redirect_stdout(output_buffer):
            exec(code, {}, local_vars)
            
        printed_output = output_buffer.getvalue()
        
        if len(printed_output) > 2000:
            printed_output = printed_output[:2000] + "\n...[OUTPUT TRUNCATED TO SAVE TOKENS]..."
        if plt.get_fignums():

            image_path = f"plot_{uuid.uuid4().hex}.png"
            
            plt.savefig(image_path, format='png', bbox_inches='tight')

            plt.close('all') 
            
            return {
                "type": "image",
                "path": image_path,
                "text": printed_output
            }
        else:
            return {
                "type": "text",
                "content": printed_output
            }
            
    except Exception as e:
        error_msg = f"Code Execution Failed:\n{traceback.format_exc()}"
        plt.close('all') 
        return {
            "type": "error",
            "content": error_msg
        }