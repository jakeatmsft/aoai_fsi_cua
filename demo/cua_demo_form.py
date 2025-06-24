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
             "Go to URL: https://forms.office.com/r/zH5V66N8P4 , "
        "complete the form with the following data, stop once completed for human review:\n"
            "{Full Name: Alex Johnson\n"
            "Date of Birth: 03/22/1990\n"
            "Gender: Female\n"
            "Address: 456 Maple Street, San Diego, CA 92103\n"
            "Phone Number: (619) 555-6789\n"
            "Email Address: alex.johnson@example.com\n"
            "Type of Insurance: Health Insurance\n"
            "Coverage Amount: $50,000\n"
            "Policy Start Date: 07/01/2025\n"
            "Policy End Date: 07/01/2026\n"
            "Do you have any pre-existing conditions?: Yes\n"
            "If yes, please specify: Asthma\n"
            "Are you currently taking any medication?: Yes\n"
            "Property Address: 456 Maple Street, San Diego, CA 92103\n"
            "Type of Property: Condo\n"
            "Year Built: 2010\n"
            "Square Footage: 1,200 sq ft}"
                    "pause once completed for human review and wait for the next step."
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
