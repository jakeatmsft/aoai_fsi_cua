// Bicep template to deploy Azure AI Foundry (OpenAI) service and model deployments
param serviceName string {
  default: 'my-ai-foundry'
  metadata: {
    description: 'Name of the Azure Cognitive Services (OpenAI) resource'
  }
}
param location string {
  default: resourceGroup().location
  metadata: {
    description: 'Azure region for deployment'
  }
}
param skuName string {
  default: 'S0'
  allowed: [ 'S0' ]
  metadata: {
    description: 'Sku for the OpenAI service (currently only S0 supported)'
  }
}

// Create the Azure Cognitive Services (OpenAI) account
resource aiAccount 'Microsoft.CognitiveServices/accounts@2022-12-01' = {
  name: serviceName
  location: location
  kind: 'OpenAI'
  sku: {
    name: skuName
  }
  properties: {}
}

// Deploy an O4-Mini model to the service
resource o4MiniDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-10-01' = {
  name: '${aiAccount.name}/o4-mini'
  properties: {
    model: 'o4-mini'
    scaleSettings: {
      scaleType: 'Standard'
      capacity: 1
    }
  }
  dependsOn: [ aiAccount ]
}

// Optionally, add more model deployments below
// e.g., gpt-4 deployment or custom models