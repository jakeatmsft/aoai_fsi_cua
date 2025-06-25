# Azure OpenAI CUA Demo

This repository contains two Streamlit-based demos showcasing conversational UI automation (CUA) using Azure OpenAI, LangChain, and Streamlit.

## Prerequisites
- Python 3.8 or higher
- pip
- An Azure OpenAI resource with endpoint and API key
1. Create a `.env` file in the project root with your Azure OpenAI credentials:
   ```dotenv
   # Azure OpenAI API key
   AZURE_OPENAI_API_KEY=your_api_key_here

   # Azure OpenAI endpoint URL (e.g. https://your-resource-name.openai.azure.com)
   AZURE_OPENAI_ENDPOINT=https://your_endpoint_here
   ```

## Installation
1. Clone the repository:
   ```bash
   git clone <repo_url>
   cd <repo_folder>
   ```
2. (Optional) Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .\.venv\Scripts\activate  # Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Run either of the Streamlit apps:

- Build Demo:
  ```bash
  streamlit run demo/cua_demo_build.py
  ```
- Form Demo:
  ```bash
  streamlit run demo/cua_demo_form.py
  ```

Follow on-screen instructions to interact with the conversational agent.

## Files
- `demo/cua_demo_build.py`: Streamlit UI for running CUA agent against a URL with browsing instructions
- `demo/cua_demo_form.py`: Streamlit UI for agent-based form completion
- `requirements.txt`: Project dependencies

## Infrastructure Deployment

Use the included Bicep template to create an Azure OpenAI (AI Foundry) resource and deploy an o4-mini model.

<!-- Deploy directly using ARM template from this repo -->
[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fjakeatmsft%2Faoai_fsi_cua%2Fmain%2Finfra%2Fmain.json)

> Note: The button above points directly to the ARM template (infra/main.json) in this repository. Ensure it references the raw JSON URL and not the GitHub HTML page to avoid parsing errors.


1. Ensure you have the [Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli) and the Bicep CLI installed.
2. Log in to Azure:
   ```bash
   az login
   az account set --subscription <YOUR_SUBSCRIPTION_ID>
   ```
3. Create (or select) a resource group:
   ```bash
   az group create \
     --name <RESOURCE_GROUP> \
     --location <LOCATION>
   ```
4. Deploy the Bicep template:
   ```bash
   az deployment group create \
     --resource-group <RESOURCE_GROUP> \
     --template-file infra/main.bicep \
     --parameters serviceName=<SERVICE_NAME> location=<LOCATION>
   ```
5. After deployment completes, retrieve the endpoint and key:
   ```bash
   az cognitiveservices account show-keys \
     --name <SERVICE_NAME> \
     --resource-group <RESOURCE_GROUP>
   ```
6. Populate your `.env` file with the returned **key** and **endpoint**.

## License
This project is released under the MIT License.