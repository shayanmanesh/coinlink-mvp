# Project Cleanup Recommendations (Non-Disruptive)

## ⚠️ CAUTION: Other agents may be working simultaneously
### Only remove files after confirming no active dependencies

## Safe to Clean (Low Risk):
```bash
# Python cache files (28 files, ~200KB)
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# macOS system files
find . -name ".DS_Store" -delete

# Log files
find . -name "*.log" -delete
```

## Size Optimization Opportunities:

### 1. **node_modules (361MB)** 
- ⚠️ DO NOT DELETE if other agents are running frontend
- Already in `.gitignore` - won't affect deployment
- Can regenerate with `npm install`

### 2. **Duplicate/Unused Files** (Can remove after confirming):
- `backend/api/main.py` (588 lines) - Using `main_production.py` for deployment
- `backend/requirements.txt` (22 lines) - Using `requirements-production.txt`
- `Opus_first_prompt_mid_project.py` - Appears to be old prompt file
- `done.mp3` (duplicate in root and backend/frontend/public)

### 3. **Heavy Dependencies** (Currently commented out in requirements-production.txt):
- `torch` - 2GB+ when installed
- `transformers` - 500MB+
- `langchain` - 100MB+
- These are NOT needed for MVP

### 4. **Documentation Files** (Keep for now):
- `DEPLOYMENT_PLAN.md` - May be referenced by other agents
- `VERCEL_DEPLOYMENT.md` - Active deployment guide
- `RAILWAY_DEPLOY.md` - Current task reference

## Recommended .gitignore Additions:
```gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment
.env
.env.local
.env.production

# Deployment
.vercel/
railway.json
```

## Before Cleanup:
- Project size: ~400MB (mostly node_modules)
- Files: ~15,000 (mostly in node_modules)

## After Cleanup (without node_modules):
- Project size: ~40MB
- Files: ~200

## ⚠️ DO NOT CLEAN NOW:
- Wait for confirmation no agents are using these files
- Coordinate with other agents before deletion
- Keep all configuration files for active deployments