# Infrastructure Requirements — Sysco Intelligent Supplier Collaboration Portal
Prodapt IPL 2026 | Team [YOUR TEAM NAME]

## Development VM

| Spec | Requirement |
|---|---|
| OS | Ubuntu 24.04 LTS |
| CPU | 8 vCPU minimum |
| RAM | 32 GB |
| Storage | 200 GB SSD/NVMe |
| Access | sudo access |

## Core Software

- Docker & Docker Compose
- Python 3.12
- Node.js LTS & npm
- PostgreSQL 15+ with `pgvector` extension enabled
- Git
- FFmpeg
- SSH
- Chrome/Chromium

## Development Tools

- VS Code (or company-standard IDE)
- Claude Code CLI (AI coding assistant)
- GitHub access — team repo + researching open-source reference implementations

## Required Network / Firewall Access

**GitHub**
- github.com
- api.github.com
- raw.githubusercontent.com
- codeload.github.com

**Package registries**
- pypi.org
- files.pythonhosted.org
- registry.npmjs.org
- Docker Hub

**AI / LLM APIs**
- api.anthropic.com (Claude — core dependency for the entire project)
- Embeddings provider API (api.voyageai.com or api.openai.com — final choice TBD, see below)

**Synapt sandbox endpoints**
- Context Substrate and Agent Hub sandbox domains — *to be confirmed with
  Sivaraman K Lakshmanan (Context Substrate) and Dibyendu Dey (Agent Hub)
  once sandbox access is provisioned*

## AI Development Access

- **Claude/Anthropic access** for development and implementation, with
  **extended usage rights** — a 6-week build with heavy AI-assisted coding
  plus live API calls for document parsing, item matching, and email
  drafting will exceed default-tier limits
- **Synapt Context Substrate** — platform provides the underlying vector +
  graph store endpoints and credentials for institutional memory (past bid
  records). No separate database infrastructure needed on the VM for this.
- **Synapt Agent Hub** — sandbox access for registering and governing the
  Outreach Agent (manifest-based, low autonomy, human approval gate)

## Note on data architecture (for IT's awareness, not an access request)

Unlike a fully Context Substrate–based setup, our product catalog
(~600 SKUs, row-per-record structured data) stays on our **own PostgreSQL +
pgvector** on the VM rather than in Context Substrate, per Synapt's own
guidance that large row-per-record datasets are a better fit for a
traditional database than their document/graph ingestion model.
Institutional memory (narrative summaries of past bids) uses Context
Substrate. This is why both Postgres and Context Substrate access are
listed above — they serve different parts of the system, not overlapping
ones.