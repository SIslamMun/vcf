#!/bin/bash
# VCF Session Preparation Script

set -e  # Exit on any error

echo "🚀 Preparing VCF Development Environment..."
echo "=================================================="

# Check environment
if [ -f /.dockerenv ]; then
    echo "📦 Running inside VCF container"
    CONTAINER_MODE=true
else
    echo "🖥️  Running on host system"
    CONTAINER_MODE=false
fi

# Verify we're in the right place
if [ ! -f "README.md" ] || [ ! -d "sessions" ]; then
    echo "❌ Please run this script from the VCF repository root"
    echo "   Expected: git clone https://github.com/grc-iit/vcf.git && cd vcf"
    exit 1
fi

# Check Python
echo "🐍 Checking Python environment..."
PYTHON_VERSION=$(python3 --version 2>&1)
echo "   Found: $PYTHON_VERSION"

# Package management
echo "📚 Setting up Python packages..."
if command -v uv &> /dev/null; then
    echo "   Using UV package manager"
    
    # Clean approach - just install dependencies without building the project
    echo "   Installing dependencies..."
    if uv sync --no-editable 2>/dev/null; then
        echo "   ✅ UV sync successful"
    else
        echo "   ⚠️  UV sync failed, trying alternative approach..."
        # Fallback: install from pyproject.toml manually
        uv pip install -r pyproject.toml --system 2>/dev/null || {
            echo "   Using pip as fallback..."
            pip install fastapi uvicorn click rich openai anthropic requests httpx numpy pandas pytest ruff black mypy pre-commit jupyter ipython
        }
    fi
else
    echo "   UV not found, using pip"
    echo "   Installing essential packages..."
    pip install fastapi uvicorn click rich openai anthropic requests httpx numpy pandas pytest ruff black mypy pre-commit jupyter ipython
fi

# Development tools
echo "🛠️  Setting up development tools..."
if command -v pre-commit &> /dev/null && [ -f ".pre-commit-config.yaml" ]; then
    echo "   Installing pre-commit hooks..."
    pre-commit install || echo "   Pre-commit setup skipped"
else
    echo "   Pre-commit not available, skipping hooks"
fi

# Verify key tools
echo "🔍 Verifying installation..."
python3 -c "
try:
    import pytest, ruff, black, rich
    print('✅ Essential tools available')
except ImportError as e:
    print(f'⚠️  Some tools missing: {e}')
    print('   This is OK - we can install them during the session')
" 2>/dev/null || echo "   Will verify tools during session"

# Create session directory for today
SESSION_DIR="sessions/week-01"
mkdir -p "$SESSION_DIR"
if [ ! -f "$SESSION_DIR/session-notes.md" ]; then
    echo "�� Creating today's session workspace..."
    cat > "$SESSION_DIR/session-notes.md" << EOL
# Week 1 Session Notes - $(date +%Y-%m-%d)

## Attendees
- [ ] Add names as people join

## AI Tools Explored
- [ ] Document tools we try today

## Code Generated
- [ ] Link to code examples

## Key Learnings
- [ ] Add insights about AI-assisted coding

## Next Week Prep
- [ ] Action items for next session
EOL

    # Create examples directory
    mkdir -p "$SESSION_DIR/examples"
    touch "$SESSION_DIR/examples/.gitkeep"
fi

echo "=================================================="
echo "✅ VCF environment ready for AI-enhanced coding!"
echo ""
echo "🎯 Next steps:"
echo "   1. Join Zulipchat: https://grc.zulipchat.com/"
echo "   2. Open VS Code/Cursor in this directory"
echo "   3. Start exploring AI coding tools!"
echo "   4. Session notes: $SESSION_DIR/session-notes.md"
echo ""
echo "🤖 Ready to vibe with AI coding!"
