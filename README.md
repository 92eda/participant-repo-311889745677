# Workshop Project

This project contains a FastAPI backend and CDK infrastructure for the workshop.

## Project Structure

```
├── backend/           # FastAPI Python backend application
│   ├── main.py       # Main FastAPI application
│   ├── requirements.txt
│   └── README.md
├── infrastructure/    # CDK TypeScript infrastructure-as-code
│   ├── bin/          # CDK app entry point
│   ├── lib/          # CDK stack definitions
│   ├── package.json
│   ├── cdk.json
│   └── README.md
├── .kiro/            # Kiro configuration (MCP servers)
└── README.md
```

## Getting Started

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Infrastructure
```bash
cd infrastructure
npm install
npm run build
cdk deploy
```

## MCP Servers Configured

- AWS Knowledge Server
- AWS Frontend MCP Server
- AWS CDK Server
- Brave Search Server
- Fetch Server
- Context7