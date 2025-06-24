import os
import sys
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

from langchain_openai import AzureChatOpenAI

from browser_use import Agent
from browser_use.controller.service import Controller
from pydantic import BaseModel
from typing import List, Optional

import streamlit as st  # Add Streamlit

from dotenv import load_dotenv

load_dotenv()

# Initialize controller first
controller = Controller()


class Model(BaseModel):
    name: str
    url: str
    version: str
    deployment: str
    default: str
    quota: str


class Models(BaseModel):
    models: List[Model]


@controller.action('Save models', param_model=Models)
def save_models(params: Models):
    with open('models.txt', 'w') as f:
        for model in params.models:
            f.write(f'{model.name} ({model.url}): {model.version} , {model.quota}\n')

load_dotenv(override=True)
# Retrieve Azure-specific environment variables
# azure_openai_api_key = os.environ.get('AZURE_OPENAI_API_KEY')
# azure_openai_endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')

# # Initialize the Azure OpenAI client
# llm = AzureChatOpenAI(
#     model_name='gpt-4o-2', 
#     openai_api_key=azure_openai_api_key,
#     azure_endpoint=azure_openai_endpoint,
#     deployment_name='gpt-4o-2',
#     api_version='2024-08-01-preview'
# )

# --- Streamlit UI ---
st.title("Azure OpenAI CUA Demo")

if "agent_result" not in st.session_state:
    st.session_state.agent_result = None

with st.form("instruction_form"):
    user_text = st.text_area(
        "Paste or type your instruction details here:",
        value=(
             "Starting at: https://devblogs.microsoft.com/blog/a-developers-guide-to-build-2025, "
            "scroll through each part of this page, review the entire page and identify all the sessions "
            "that are related to AI and ML on Azure. List the session title/ID, date/time, and links in a markdown table. "
            "Make sure to inspect entire page, save output"
        ),
        height=300
    )
    submitted = st.form_submit_button("Submit to Agent")

if submitted:
    task = user_text
    import subprocess
    import sys

    # Get the path to the current Python executable (should be the conda env Python)
    python_executable = sys.executable
    print(python_executable)
    print("running cua agent")
    script_path = os.path.join(os.path.dirname(__file__), "azure_openai_cua.py")
    print(script_path)
    # Pass the --task argument and user_text as separate arguments
    result = subprocess.run(
        [python_executable, script_path, "--task", user_text],
        capture_output=True,
        text=True,
        encoding="utf-8"

    )
    print("STDOUT:", result.stdout)
    #print("STDERR:", result.stderr)
    print("RETURN CODE:", result.returncode)

    if result.returncode == 0:
        st.success(result.stdout)
    else:
        st.error(f"Error running agent:\n{result.stderr}")
    st.success(result.stdout)
