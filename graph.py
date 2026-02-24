import os
from typing import Annotated, TypedDict
from dotenv import load_dotenv

from langchain_core.messages import AnyMessage, SystemMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI

from tools import execute_pandas_code

load_dotenv()

# ---------------------------------------------------------
# 1. Define the State Structure
# ---------------------------------------------------------
class GraphState(TypedDict):
    """
    This dictionary is passed continuously between nodes.
    'add_messages' ensures new messages are appended, not overwritten.
    """
    messages: Annotated[list[AnyMessage], add_messages]
    schema: str  # We will inject the df.dtypes and df.head() here


llm = ChatOpenAI(model="gpt-5-nano")
tools = [execute_pandas_code]
llm_with_tools = llm.bind_tools(tools)

def agent_node(state: GraphState):
    """
    This node reads the state, constructs the system prompt with the schema,
    and calls the LLM.
    """
    messages = state["messages"]
    df_schema = state.get("schema", "No dataframe schema provided.")
    
    sys_prompt = SystemMessage(
        content=f"""You are an expert Data Scientist agent.
        You have access to a Pandas DataFrame named 'df'.
        
        Here is the schema and sample data of the DataFrame:
        {df_schema}
        
        INSTRUCTIONS:
        1. When asked a question, write Python code using the 'execute_pandas_code' tool to analyze 'df'.
        2. Do NOT invent column names. Only use the columns explicitly listed in the schema.
        3. If the user asks for a chart, use matplotlib.pyplot as 'plt' and generate it.
        4. CRITICAL: Do NOT use plt.show(), plt.savefig(), plt.clf(), plt.cla(), or plt.close(). The system will automatically capture and clear the plot. Just write the plotting code and stop.
        5. Do NOT modify the original dataframe directly (e.g., df.drop(inplace=True)). Assign to a new variable if needed.
        6. If a tool execution fails with an error, read the error trace, correct your Python code, and call the tool again.
        """
    )
    
    response = llm_with_tools.invoke([sys_prompt] + messages)
    
    return {"messages": [response]}

builder = StateGraph(GraphState)

builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(tools))


builder.add_edge(START, "agent")

builder.add_conditional_edges("agent", tools_condition)


builder.add_edge("tools", "agent")
eda_agent = builder.compile()