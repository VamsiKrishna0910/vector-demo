# 🚀 Publishing to GitHub - Quick Guide

This guide shows how to publish your Vector Demo project to GitHub.

---

## Step 1: Create a GitHub Account (if needed)

- Go to [GitHub.com](https://github.com)
- Click "Sign up"
- Follow the setup steps

---

## Step 2: Create a New Repository on GitHub

1. Go to [https://github.com/new](https://github.com/new)
2. Fill in the details:
   - **Repository name**: `vector-demo` (or your preferred name)
   - **Description**: `RAG pipeline with Milvus, LangChain Core, and FastAPI`
   - **Visibility**: Public (to let others access it)
   - **Initialize**: Do NOT check "Add a README" (you already have one)

3. Click **"Create repository"**

---

## Step 3: Push Your Code from Local Machine

In your terminal, from the `/home/vamsi/Vector_demo` directory:

```bash
cd /home/vamsi/Vector_demo

# Initialize git (if not already initialized)
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Vector Demo with Milvus RAG"

# Rename branch to main (GitHub default)
git branch -M main

# Add remote repository URL
# Replace YOUR_USERNAME with your GitHub username
git remote add origin https://github.com/YOUR_USERNAME/vector-demo.git

# Push to GitHub
git push -u origin main
```

---

## Step 4: Verify on GitHub

1. Go to `https://github.com/YOUR_USERNAME/vector-demo`
2. You should see all your files uploaded
3. Your README.md should display automatically

---

## What Gets Published (and what doesn't)

✅ **Pushed to GitHub:**
- `api_service.py`
- `milvus_ingest.py`
- `milvus_search.py`
- `requirements.txt`
- `README.md`
- `COMMANDS.md`
- `LICENSE`
- `.gitignore`
- `.env.example`
- `docker-compose.yml`
- `pdfs/` directory (sample structure)
- `milvus_conf/milvus.yaml`

❌ **NOT pushed (ignored by .gitignore):**
- `.env` (contains credentials)
- `.venv/` (Python virtual environment)
- `__pycache__/` (compiled Python)
- `.vscode/` (IDE settings)
- `*.log` files
- `milvus_db/`, `minio_data/` (Docker data)

---

## Step 5: Optional - Add Topics

On GitHub repository page:
1. Click **"Add topics"** (right sidebar)
2. Add relevant tags:
   - `milvus`
   - `rag`
   - `langchain`
   - `fastapi`
   - `vector-database`
   - `embeddings`
   - `llm`

This helps others discover your project!

---

## Step 6: Make Updates

To push future changes:

```bash
cd /home/vamsi/Vector_demo

# Check what changed
git status

# Stage changes
git add .

# Commit
git commit -m "Describe your changes here"

# Push to GitHub
git push origin main
```

---

## Troubleshooting

### Error: "fatal: not a git repository"

Run this once:
```bash
git init
```

### Error: "fatal: 'origin' does not appear to be a git repository"

Add the remote:
```bash
git remote add origin https://github.com/YOUR_USERNAME/vector-demo.git
```

### Error: "fatal: Authentication failed"

Use SSH keys instead of HTTPS:
```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t ed25519 -C "your-email@example.com"

# Add to GitHub: Settings → SSH and GPG keys → New SSH key
# Copy from: cat ~/.ssh/id_ed25519.pub

# Then use SSH URL instead:
git remote set-url origin git@github.com:YOUR_USERNAME/vector-demo.git
```

### Can't find `.gitignore` file

Create it:
```bash
cd /home/vamsi/Vector_demo
cat > .gitignore << 'EOF'
.env
.venv/
__pycache__/
*.pyc
*.log
milvus_db/
minio_data/
EOF
```

---

## Next Steps

After publishing:

1. **Share the link**: `https://github.com/YOUR_USERNAME/vector-demo`
2. **Add a badge** to your README (optional):
   ```markdown
   ![GitHub Stars](https://img.shields.io/github/stars/YOUR_USERNAME/vector-demo)
   ![License](https://img.shields.io/badge/license-MIT-blue)
   ```

3. **Enable GitHub Pages** (optional) for project website:
   - Go to Settings → Pages
   - Select "main" branch
   - Choose a theme

4. **Create releases** (optional):
   - Go to Releases
   - Click "Create a new release"
   - Tag: `v1.0.0`
   - Describe changes

---

## Tips for a Great GitHub Project

✨ **Make it discoverable:**
- Write a clear README (already done!)
- Add code comments
- Create example notebooks
- Add a CONTRIBUTING.md guide

✨ **Help others use it:**
- Include installation steps (already done!)
- Provide usage examples (already done!)
- Add troubleshooting section (already done!)

✨ **Maintain it:**
- Add issues for bugs
- Review pull requests
- Keep dependencies updated
- Add GitHub Actions for CI/CD (advanced)

---

## Quick Reference

```bash
# Initialize new repo
git init
git add .
git commit -m "Initial commit"
git branch -M main

# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/vector-demo.git

# First push
git push -u origin main

# Future updates
git add .
git commit -m "Your message"
git push
```

---

## Resources

- [GitHub Getting Started](https://docs.github.com/en/get-started)
- [Git Basics](https://git-scm.com/book/en/v2/Getting-Started-Git-Basics)
- [GitHub CLI](https://cli.github.com/) - Alternative to web interface

---

**Ready to publish? Let's go! 🚀**

Run the commands from Step 3 above to push your project to GitHub.
