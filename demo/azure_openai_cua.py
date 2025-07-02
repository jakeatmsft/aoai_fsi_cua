"""
Simple try of the agent.

@dev You need to add AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT to your environment variables.
"""
import argparse
import os
import sys
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

from langchain_openai import AzureChatOpenAI

from browser_use import Agent
from browser_use.controller.service import Controller, ActionResult
from pydantic import BaseModel
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()

# Initialize controller first
controller = Controller()


class output_print(BaseModel):
    text: str

@controller.action('Save output', param_model=output_print)
def save_models(params: output_print):
    with open('output.txt', 'w') as f:
        f.writelines(params.text)

@controller.action('Ask user for information or assistance')
def ask_for_human_assistance(prompt: str) -> str:
	print(f'\n✋ The AI Agent is requesting assistance: {prompt}')
	print('\t(press [Enter] when ready to continue)')
	human_response = input(' > ')
	return ActionResult(output=human_response.strip(), save_in_memory=True)

load_dotenv(override=True)
# Retrieve Azure-specific environment variables
azure_openai_api_key = os.environ.get('AZURE_OPENAI_API_KEY')
azure_openai_endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')

# Initialize the Azure OpenAI client
llm = AzureChatOpenAI(
    model_name='gpt-4o-2', 
    openai_api_key=azure_openai_api_key,
    azure_endpoint=azure_openai_endpoint,  # Corrected to use azure_endpoint instead of openai_api_base
    deployment_name='gpt-4o-2',  # Use deployment_name for Azure models
    api_version='2024-08-01-preview'  # Explicitly set the API version here
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Azure OpenAI Agent with a custom task.")
    parser.add_argument(
        "--task",
        type=str,
        default="",
        help="Task prompt for the agent. Ask for human assistance before completing any steps such as submitting a form or clicking a button.",
    )
    args = parser.parse_args()

    agent = Agent(
        task=args.task,
        llm=llm,
        controller=controller,
        generate_gif=True,
    )

    async def main():
        await agent.run(max_steps=20)
        print(agent.AgentOutput)
        #input('Press Enter to continue...')

    asyncio.run(main())
