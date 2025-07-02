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
# initialize session state defaults
for _key, _default in [
    ('proc', None),
    ('agent_output_lines', []),
    ('thread', None),
    ('result_shown', False),
    ('last_agent_lines_len', 0),
]:
    if _key not in st.session_state:
        st.session_state[_key] = _default


with st.form("instruction_form"):
    user_text = st.text_area(
        "Paste or type your instruction details here:",
        value=(
             """Go to URL: https://forms.office.com/r/zH5V66N8P4 , complete the form with the following data, stop once completed for human review:
{Full Name: Alex Johnson
Date of Birth: 03/22/1990
Gender: Female
Address: 456 Maple Street, San Diego, CA 92103
Phone Number: (619) 555-6789
Email Address: alex.johnson@example.com
Type of Insurance: Health Insurance
Coverage Amount: $50,000
Policy Start Date: 07/01/2025
Policy End Date: 07/01/2026
Do you have any pre-existing conditions?: Yes
If yes, please specify: Asthma
Are you currently taking any medication?: Yes
Property Address: 456 Maple Street, San Diego, CA 92103
Type of Property: Condo
Year Built: 2010
Square Footage: 1,200 sq ft}pause once all fields are completed ask for human assistance before submitting the form .  Do not submit the form."""
        ),
        height=300
    )
    submitted = st.form_submit_button("Submit to Agent")

if submitted and st.session_state.proc is None:
    import subprocess, sys, os, threading, signal
    cmd = [
        sys.executable,
        os.path.join(os.path.dirname(__file__), "azure_openai_cua.py"),
        "--task",
        user_text,
    ]
    popen_kwargs = dict(stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if os.name == 'nt':
        popen_kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
    proc = subprocess.Popen(cmd, **popen_kwargs)
    st.session_state.proc = proc
    st.session_state.agent_output_lines = []
    def _reader():
        for line in proc.stdout:
            # Reassigning new list to session_state to trigger rerun
            st.session_state['agent_output_lines'] = st.session_state['agent_output_lines'] + [line]
        proc.wait()
    thread = threading.Thread(target=_reader, daemon=True)
    thread.start()
    st.session_state.thread = thread

if st.session_state.proc is not None:
    placeholder = st.empty()
    lines = st.session_state.agent_output_lines
    placeholder.text("".join(lines))
    prev = st.session_state.last_agent_lines_len
    curr = len(lines)
    if curr != prev:
        st.session_state.last_agent_lines_len = curr
        st.experimental_rerun()
    proc = st.session_state.proc
    import signal
    if proc.poll() is None:
        if st.button("Stop agent"):
            if os.name == 'nt':
                proc.send_signal(signal.CTRL_C_EVENT)
            else:
                proc.send_signal(signal.SIGINT)
    else:
        if not st.session_state.result_shown:
            if proc.returncode == 0:
                st.success("Agent completed successfully.")
            else:
                st.error(f"Agent failed (exit code {proc.returncode}).")
            st.session_state.result_shown = True
