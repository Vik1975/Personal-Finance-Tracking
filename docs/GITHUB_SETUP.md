# GitHub Setup Guide

## Option 1: Using GitHub Website (Recommended)

### Step 1: Create Repository on GitHub

1. **Go to GitHub**: https://github.com/new
2. **Fill in repository details**:
   - Repository name: `personal-finance-tracker`
   - Description: `FastAPI-based personal finance tracker with OCR, auto-categorization, and analytics`
   - Visibility: Choose **Public** or **Private**
   - ❌ **DO NOT** check "Add a README file"
   - ❌ **DO NOT** check "Add .gitignore"
   - ❌ **DO NOT** check "Choose a license"
3. Click **"Create repository"**

### Step 2: Push Your Code

After creating the repository, GitHub will show you commands. Run these in your terminal:

```bash
cd /Users/viktorkabelkov/PycharmProjects/personal-finance-tracker

# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/personal-finance-tracker.git

# Push code
git push -u origin main
```

**Replace `YOUR_USERNAME`** with your actual GitHub username!

---

## Option 2: Using GitHub CLI (If you want to install it)

### Install GitHub CLI

```bash
# Install via Homebrew
brew install gh

# Authenticate
gh auth login
```

### Create and Push Repository

```bash
cd /Users/viktorkabelkov/PycharmProjects/personal-finance-tracker

# Create repository on GitHub
gh repo create personal-finance-tracker --public --source=. --remote=origin --push

# Or for private repo:
gh repo create personal-finance-tracker --private --source=. --remote=origin --push
```

---

## Step 3: Verify Upload

After pushing, visit:
```
https://github.com/YOUR_USERNAME/personal-finance-tracker
```

You should see:
- ✅ 45 files
- ✅ README.md displayed
- ✅ Full project structure

---

## Quick Commands Reference

```bash
# Check current remote
git remote -v

# Add remote (if not added)
git remote add origin https://github.com/YOUR_USERNAME/personal-finance-tracker.git

# Push to GitHub
git push -u origin main

# Check status
git status

# Make changes and push updates
git add .
git commit -m "Update: description of changes"
git push
```

---

## Repository URL Format

- **HTTPS**: `https://github.com/YOUR_USERNAME/personal-finance-tracker.git`
- **SSH**: `git@github.com:YOUR_USERNAME/personal-finance-tracker.git`

Use HTTPS if you haven't set up SSH keys.

---

## Troubleshooting

### Error: "remote origin already exists"
```bash
# Remove existing remote
git remote remove origin

# Add correct remote
git remote add origin https://github.com/YOUR_USERNAME/personal-finance-tracker.git
```

### Error: "Authentication failed"
- Make sure you're logged into GitHub
- Use a Personal Access Token instead of password
- Generate token at: https://github.com/settings/tokens
  - Select scopes: `repo` (full control of private repositories)
  - Use token as password when pushing

### Error: "Updates were rejected"
```bash
# Force push (only if you're sure)
git push -u origin main --force
```

---

## Next Steps After Upload

1. **Add Topics** to your repository:
   - Go to repository settings
   - Add topics: `fastapi`, `python`, `ocr`, `finance-tracker`, `analytics`

2. **Enable GitHub Actions** (CI/CD already configured):
   - Actions will run automatically on push
   - See `.github/workflows/ci.yml`

3. **Add Repository Description**:
   - Click "⚙️" next to "About"
   - Add description and website link

4. **Star Your Own Repo** ⭐ (optional but nice!)

---

## Example: Complete Setup

```bash
# 1. Verify git status
git status

# 2. Check existing remotes
git remote -v

# 3. Add GitHub remote (REPLACE YOUR_USERNAME!)
git remote add origin https://github.com/YOUR_USERNAME/personal-finance-tracker.git

# 4. Push to GitHub
git push -u origin main

# 5. Open repository in browser
open https://github.com/YOUR_USERNAME/personal-finance-tracker
```

---

## Your Repository is Ready! 🎉

Once pushed, your repository will include:
- ✅ Complete FastAPI application
- ✅ Docker setup
- ✅ Database migrations
- ✅ OCR processing
- ✅ 40+ API endpoints
- ✅ Comprehensive README
- ✅ CI/CD configuration
- ✅ All documentation

Share your repository URL and showcase your work! 🚀
