import streamlit as st
import pandas as pd
import ast
import uuid
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from graph import eda_agent
from tools import set_global_df

st.set_page_config(page_title="Autonomous EDA Agent", layout="wide")
st.title("📊 Autonomous EDA Agent")


# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

with st.sidebar:
    st.header("1. Upload Data")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    st.markdown("---")
    st.markdown("""
    **How it works:**
    * Upload a CSV dataset.
    * The agent reads the schema (not the raw data).
    * It writes and executes Python code locally to answer your questions.
    """)


if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)    
    set_global_df(df)
    

    schema_str = (
        f"Columns and Data Types:\n{df.dtypes.to_string()}\n\n"
        f"Sample Data:\n{df.head(3).to_string()}"
    )
    
    st.sidebar.success("Data loaded into memory!")
    
    with st.sidebar.expander("View Raw Data Preview"):
        st.dataframe(df.head())
    for msg in st.session_state.messages:
        if isinstance(msg, HumanMessage):
            st.chat_message("user").write(msg.content)
            
        elif isinstance(msg, AIMessage) and msg.content:
            st.chat_message("assistant").write(msg.content)
            
        elif isinstance(msg, ToolMessage):
            try:
                tool_output = ast.literal_eval(msg.content)
                
                if isinstance(tool_output, dict):
                    

                    if tool_output.get("type") == "image":
                        st.chat_message("assistant").image(tool_output["path"])
                        
                        if tool_output.get("text"):
                            st.chat_message("assistant").write(
                                f"```text\n{tool_output['text']}\n```"
                            )
                    elif tool_output.get("type") == "text":
                        if tool_output.get("content"):
                            st.chat_message("assistant").write(
                                f"```text\n{tool_output['content']}\n```"
                            )
                            
            except Exception:
                pass


    if prompt := st.chat_input(
        "E.g., 'What is the correlation between column A and column B?'"
    ):
        st.session_state.messages.append(HumanMessage(content=prompt))
        st.chat_message("user").write(prompt)

        with st.spinner("🧠 Agent is thinking and writing code..."):
            
            inputs = {
                "messages": st.session_state.messages,
                "schema": schema_str
            }

            final_state = eda_agent.invoke(
                inputs,
                config={
                    "configurable": {
                        "thread_id": st.session_state.thread_id
                    }
                }
            )
            st.session_state.messages = final_state["messages"]

            st.rerun()

else:
    st.info("Please upload a CSV file in the sidebar to begin exploratory data analysis.")
    