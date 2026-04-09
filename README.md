# CloudOps MCP Agent: AI-Powered AWS DevOps Tooling System
A production-style, AI agent system that lets you query and monitor your AWS infrastructure using plain English. Built on the official Model Context Protocol (MCP), LangChain, Groq (Llama 3.3 70B), and FastAPI - with clean architectural separation across every layer.

- The AI agent never calls AWS directly
- All AWS operations go through a dedicated MCP tool server
- The backend exposes a JWT-secured REST API
- Every layer has a single, clear responsibility

Ask: "Which of my EC2 instances are idle and wasting money?"
The agent figures out what to call, queries AWS in real-time, and gives you a direct answer.

This is not a chatbot wrapper around an LLM. It is a structured, multi-layer system where the AI reasons about which tools to use, calls them via a protocol, and returns answers grounded in real AWS data.

## Architecture

<img width="1937" height="937" alt="mcp-agent_AWS_architecture drawio" src="https://github.com/user-attachments/assets/2b42a340-ec34-4c71-93cf-f8c961591f95" />


## System Overview

This system follows a layered architecture where each component has a single responsibility:

- FastAPI Backend — Handles authentication (JWT), request routing, and agent lifecycle
- LangChain Agent — Interprets user queries and decides which tools to call
- MCP Server — Exposes structured tools via the Model Context Protocol
- Service Layer — Contains all business logic and AWS interactions
- AWS (via boto3) — Source of real-time infrastructure data

## Request Flow

- User sends request → /chat with JWT
- Backend validates token and forwards query to agent
- Agent reasons and selects the appropriate tool
- MCP server executes the tool
- Service layer calls AWS via boto3
- AWS returns data (EC2, CloudWatch, Cost Explorer)
- Results propagate back → MCP → Agent → Backend → User

## Available Tools

| Tool                    | Description                          | AWS Service        |
|--------------------------|--------------------------------------|--------------------|
| list_ec2_instances       | List instances in a region           | EC2                |
| list_all_ec2_instances   | Scan all regions                     | EC2                |
| get_cost_summary         | Cost breakdown                       | Cost Explorer      |
| get_costly_instances     | Top expensive instances              | Cost Explorer      |
| detect_idle_instances    | Identify idle instances via CPU      | CloudWatch + EC2   |

Example queries the agent handles:

- "List all my EC2 instances"
- "What did I spend in the last 30 days?"
- "Which instances are idle?"
- "Show me the top 5 most expensive instances this month"
- "Is the instance in Mumbai idle?" (uses memory from previous turn)

## API Reference

| Method | Endpoint    | Auth         | Description              |
| ------ | ----------- | ------------ | ------------------------ |
| POST   | /auth/login | None         | Returns JWT token        |
| POST   | /chat       | Bearer token | Send message, get answer |
| GET    | /health     | None         | Server + agent status    |

## Tech Stack

| Layer            | Technology               | Purpose                          |
|------------------|--------------------------|----------------------------------|
| MCP Server       | FastMCP (`mcp` SDK)      | Tool exposure layer              |
| Agent            | LangChain + LangGraph    | Reasoning + tool selection       |
| LLM              | Groq (Llama 3.3 70B)     | Inference + decision making      |
| Backend          | FastAPI                  | API + authentication             |
| AWS SDK          | boto3                    | Calls AWS APIs                   |
| Cloud Services   | EC2, CloudWatch, CE      | Infrastructure + metrics + cost  |

## AWS Permissions

- Managed policy: `AmazonEC2ReadOnlyAccess`
- CloudWatch read access (`cloudwatch:GetMetricStatistics`, `cloudwatch:ListMetrics`)
- Cost Explorer access (`ce:GetCostAndUsage`, `ce:GetDimensionValues`)

> Note: Enable Cost Explorer in the AWS Billing console (one-time setup).

## Setup & Installation

### Prerequisites
- Python 3.11+
- AWS account (with IAM user credentials)
- Groq API key (for LLM access)

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/cloudOps-mcp-agent.git
cd cloudOps-mcp-agent
```

### 2. Create virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r mcp-server/requirements.txt
pip install fastapi uvicorn "python-jose[cryptography]"
```

### 4. Configure Environment Variables

```bash
cp mcp-server/.env.example mcp-server/.env
```
Edit the .env file:

```env
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=ap-south-1

GROQ_API_KEY=your_groq_api_key

JWT_SECRET_KEY=your_secret_key
ADMIN_USERNAME=your_username
ADMIN_PASSWORD=your_password
```

### 5. Run Options

Option A: CLI Agent (terminal)
```bash
cd langchain_agent
python main.py
```

Option B: FastAPI Backend (REST API)

```bash
uvicorn backend.main:app --reload --port 8000
```
Open in browser:
http://localhost:8000/docs for interactive API documentation.
