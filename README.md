# 🚀 VCF: Vibe Coding Fridays

Welcome to Vibe Coding Fridays - a collaborative space into AI-enhanced software development! Every Friday, we dive deep into cutting-edge AI coding tools, techniques, and workflows while building real solutions for high-performance computing and AI research.

## 🎯 Mission

Transform how we think about programming by mastering human-AI collaboration in software development. Through hands-on exploration, we're discovering the most effective ways to leverage AI as a coding partner, not just a tool.

## 📅 Program Overview

**When**: Every Friday, 10am-1pm CDT  
**Duration**: 12 weeks (Summer 2025)  
**Format**: 3-hour sessions combining tutorials, hands-on coding, and knowledge synthesis

### Three-Phase Journey

- **🏗️ Phase 1 (June)**: AI-Native Development Foundations
- **🎨 Phase 2 (July)**: Individual AI Mastery  
- **🏆 Phase 3 (August)**: Competitive AI Innovation

## 🗺️ Repository Map

### `/prompts/`
**AI Prompt Library** - Battle-tested prompts for various coding scenarios
- `system-prompts/` - System prompts for different AI coding contexts
- `user-prompts/` - Effective user prompts organized by task type
- `prompt-patterns/` - Reusable prompt templates and patterns

### `/tools/`
**AI Development Tools & Configurations**
- `cline/` - Cline AI assistant configurations and workflows
- `roo-code/` - Roo Code integration and usage examples  
- `augment/` - Code augmentation tools and scripts
- `evaluations/` - Tool comparison frameworks and results

### `/ai-rules/`
**AI Editor Configuration**
- `cursor/` - Cursor IDE global and project-specific rules
- `vscode/` - VS Code AI extension configurations
- `windsurf/` - Windsurf setup and optimization settings
- `global-rules.md` - Universal AI coding guidelines
- `project-rules.md` - Project-specific AI behavior rules

### `/apps/`
**Applications We're Building**
- `scifon-mcp/` - MCP server for HPC workflow memory and storage
- `prototypes/` - Experimental tools and proof-of-concepts
- `integrations/` - HPC system integrations and utilities

### `/sessions/`
**Weekly Session Documentation**
- `week-01/` through `week-12/` - Each session's materials and outcomes
- Session notes, code examples, and learning insights
- AI-generated summaries and community discussions

### `/resources/`
**Learning Materials & References**
- `setup-guides/` - Environment setup instructions for different platforms
- `best-practices/` - Documented AI coding strategies that work
- `research/` - Papers, articles, and external resources
- `community/` - Community guidelines and contribution processes

## 🛠️ Getting Started

### Prerequisites
- Docker Desktop
- VS Code with Copilot Pro
- UV package manager: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Access to [GRC Zulipchat](https://grc.zulipchat.com/)

### Quick Setup
```bash
# Clone the repository
git clone https://github.com/grc-iit/vcf.git
cd vcf

# Initialize development environment
uv init
uv add --dev pytest ruff black

# Setup Docker development container
docker build -t vcf-dev .
docker run -it -v $(pwd):/workspace vcf-dev
```

## 🎯 Current Focus: Scifon-MCP

Our primary project is **Scifon-MCP** - an MCP (Model Context Protocol) server that acts as intelligent memory and storage for AI-assisted developers. Think of it as a smart clipboard that understands scientific computing contexts.

## 🤝 Contributing

We welcome collaboration! Whether you're part of our core team or joining as an external collaborator:

1. **Join our community**: Get access to [GRC Zulipchat](https://grc.zulipchat.com/join/huzcpefq3dfkg3rvkvpnsbsz/)
2. **Attend sessions**: Fridays 10am-1pm CDT online at [Google Meet](https://calendar.app.google/fZWGoeaVTKu2BPmZ6)
3. **Share discoveries**: Document your AI coding breakthroughs on [Gnosis Github](https://github.com/grc-iit/vcf/)
4. **Experiment boldly**: This is a learning-first environment. There are no right answers!
5. **Session Schedule**: See `/sessions/` directory for detailed agendas

## 📝 License

MIT License - Feel free to use, modify, and share our discoveries!

---

**Ready to vibe with AI coding?** 🤖✨ Join us Fridays and let's explore the future of development together!
