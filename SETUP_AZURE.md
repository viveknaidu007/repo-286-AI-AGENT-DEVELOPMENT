# Azure Deployment Configuration for RAG AI Agent

## Prerequisites

Before deploying to Azure, ensure you have:

1. **Azure Account**: Active Azure subscription
2. **Azure CLI**: Installed and configured ([Install Guide](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli))
3. **Azure OpenAI Service**: Deployed with a model deployment
4. **Azure AI Search**: Created search service (optional, can use FAISS)

## Step 1: Create Azure Resources

### 1.1 Login to Azure

```bash
az login
az account set --subscription "Your-Subscription-Name"
```

### 1.2 Create Resource Group

```bash
az group create \
  --name rg-rag-agent \
  --location eastus
```

### 1.3 Create Azure OpenAI Service

```bash
# Create Azure OpenAI resource
az cognitiveservices account create \
  --name openai-rag-agent \
  --resource-group rg-rag-agent \
  --kind OpenAI \
  --sku S0 \
  --location eastus

# Deploy a model (e.g., GPT-4)
az cognitiveservices account deployment create \
  --name openai-rag-agent \
  --resource-group rg-rag-agent \
  --deployment-name gpt-4 \
  --model-name gpt-4 \
  --model-version "0613" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name "Standard"
```

### 1.4 Create Azure AI Search (Optional)

```bash
az search service create \
  --name search-rag-agent \
  --resource-group rg-rag-agent \
  --sku basic \
  --location eastus
```

### 1.5 Create App Service Plan

```bash
az appservice plan create \
  --name plan-rag-agent \
  --resource-group rg-rag-agent \
  --sku B1 \
  --is-linux
```

### 1.6 Create Web App

```bash
az webapp create \
  --name rag-agent-app \
  --resource-group rg-rag-agent \
  --plan plan-rag-agent \
  --runtime "PYTHON:3.11"
```

## Step 2: Configure Environment Variables

### 2.1 Get Azure OpenAI Credentials

```bash
# Get endpoint
az cognitiveservices account show \
  --name openai-rag-agent \
  --resource-group rg-rag-agent \
  --query "properties.endpoint" \
  --output tsv

# Get API key
az cognitiveservices account keys list \
  --name openai-rag-agent \
  --resource-group rg-rag-agent \
  --query "key1" \
  --output tsv
```

### 2.2 Get Azure AI Search Credentials (if using)

```bash
# Get endpoint
az search service show \
  --name search-rag-agent \
  --resource-group rg-rag-agent \
  --query "hostName" \
  --output tsv

# Get admin key
az search admin-key show \
  --service-name search-rag-agent \
  --resource-group rg-rag-agent \
  --query "primaryKey" \
  --output tsv
```

### 2.3 Set Environment Variables in App Service

```bash
az webapp config appsettings set \
  --name rag-agent-app \
  --resource-group rg-rag-agent \
  --settings \
    LLM_PROVIDER="azure_openai" \
    AZURE_OPENAI_API_KEY="your-api-key" \
    AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/" \
    AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4" \
    AZURE_OPENAI_API_VERSION="2024-02-15-preview" \
    VECTOR_STORE="azure_search" \
    AZURE_SEARCH_ENDPOINT="https://your-search.search.windows.net" \
    AZURE_SEARCH_API_KEY="your-search-key" \
    AZURE_SEARCH_INDEX_NAME="rag-documents" \
    DEBUG="False" \
    LOG_LEVEL="WARNING" \
    ALLOWED_ORIGINS="https://rag-agent-app.azurewebsites.net"
```

## Step 3: Deploy Application

### 3.1 Deploy from Local Git

```bash
# Configure deployment source
az webapp deployment source config-local-git \
  --name rag-agent-app \
  --resource-group rg-rag-agent

# Get deployment URL
az webapp deployment list-publishing-credentials \
  --name rag-agent-app \
  --resource-group rg-rag-agent \
  --query scmUri \
  --output tsv

# Add Azure as git remote
git remote add azure <deployment-url>

# Push to Azure
git push azure main
```

### 3.2 Deploy from GitHub

```bash
az webapp deployment source config \
  --name rag-agent-app \
  --resource-group rg-rag-agent \
  --repo-url https://github.com/your-username/your-repo \
  --branch main \
  --manual-integration
```

### 3.3 Deploy using ZIP

```bash
# Create deployment package
zip -r deploy.zip . -x "*.git*" "venv/*" "__pycache__/*" "*.pyc"

# Deploy
az webapp deployment source config-zip \
  --name rag-agent-app \
  --resource-group rg-rag-agent \
  --src deploy.zip
```

## Step 4: Configure Startup Command

```bash
az webapp config set \
  --name rag-agent-app \
  --resource-group rg-rag-agent \
  --startup-file "startup.sh"
```

## Step 5: Enable Application Insights (Optional)

```bash
# Create Application Insights
az monitor app-insights component create \
  --app rag-agent-insights \
  --location eastus \
  --resource-group rg-rag-agent

# Get instrumentation key
az monitor app-insights component show \
  --app rag-agent-insights \
  --resource-group rg-rag-agent \
  --query "connectionString" \
  --output tsv

# Set in App Service
az webapp config appsettings set \
  --name rag-agent-app \
  --resource-group rg-rag-agent \
  --settings APPLICATIONINSIGHTS_CONNECTION_STRING="your-connection-string"
```

## Step 6: Process Documents

After deployment, you need to process the sample documents:

```bash
# SSH into the App Service
az webapp ssh --name rag-agent-app --resource-group rg-rag-agent

# Run document processing
python process_documents.py
```

Alternatively, you can process documents locally and upload the vector store:

```bash
# Process locally (with Azure credentials in .env)
python process_documents.py

# Upload vector_store directory to Azure
az webapp deployment source config-zip \
  --name rag-agent-app \
  --resource-group rg-rag-agent \
  --src vector_store.zip
```

## Step 7: Verify Deployment

```bash
# Get app URL
az webapp show \
  --name rag-agent-app \
  --resource-group rg-rag-agent \
  --query "defaultHostName" \
  --output tsv

# Check health
curl https://rag-agent-app.azurewebsites.net/health

# View logs
az webapp log tail \
  --name rag-agent-app \
  --resource-group rg-rag-agent
```

## Troubleshooting

### Check Application Logs

```bash
# Enable logging
az webapp log config \
  --name rag-agent-app \
  --resource-group rg-rag-agent \
  --application-logging filesystem \
  --level information

# Stream logs
az webapp log tail \
  --name rag-agent-app \
  --resource-group rg-rag-agent
```

### Common Issues

1. **Module not found errors**: Ensure `requirements.txt` is complete and deployed
2. **Environment variables not set**: Verify with `az webapp config appsettings list`
3. **Startup timeout**: Increase timeout in Azure portal (Configuration > General settings)
4. **Vector store not found**: Run `process_documents.py` after deployment

## Scaling

### Scale Up (Vertical)

```bash
az appservice plan update \
  --name plan-rag-agent \
  --resource-group rg-rag-agent \
  --sku P1V2
```

### Scale Out (Horizontal)

```bash
az appservice plan update \
  --name plan-rag-agent \
  --resource-group rg-rag-agent \
  --number-of-workers 3
```

## Cost Optimization

- Use **Basic** tier for development/testing
- Use **Standard** or **Premium** for production
- Enable **auto-scaling** based on CPU/memory
- Use **Azure AI Search Basic** tier for small datasets
- Monitor costs with **Azure Cost Management**

## Security Best Practices

1. **Use Managed Identity** instead of API keys where possible
2. **Enable HTTPS only** in App Service settings
3. **Restrict CORS** to specific domains
4. **Use Azure Key Vault** for secrets
5. **Enable Azure AD authentication** for the web app
6. **Set up network restrictions** (IP allowlist)

## Cleanup

To delete all resources:

```bash
az group delete --name rg-rag-agent --yes --no-wait
```

## Additional Resources

- [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Azure AI Search Documentation](https://learn.microsoft.com/en-us/azure/search/)
- [Azure App Service Documentation](https://learn.microsoft.com/en-us/azure/app-service/)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
