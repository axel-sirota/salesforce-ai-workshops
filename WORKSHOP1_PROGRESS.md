# Workshop 1: Current Progress

## Overview

Building DevHub V0 + Infrastructure for AI Observability Workshop.

**Total Phases**: 8
**Estimated Time**: ~3.5 hours
**Current Status**: Phase files created, ready to implement

---

## Phase Progress

| Phase | Name | Status | Duration | Notes |
|-------|------|--------|----------|-------|
| 1 | Infrastructure (Terraform + Ansible) | ✅ Complete | 45 min | Jaeger on 46.224.233.5 |
| 2 | Project Structure & Dependencies | ✅ Complete | 20 min | Python 3.12.12, all deps installed |
| 3 | Data Files | ✅ Complete | 20 min | 8 docs, 4 teams, 5 owners, 5 services |
| 4 | VectorDB Service | ✅ Complete | 30 min | ChromaDB with failure modes |
| 5 | TeamDB Service | ⬜ Not Started | 25 min | SQLite |
| 6 | StatusAPI Service | ⬜ Not Started | 20 min | Mock API |
| 7 | DevHubAgent Orchestration | ⬜ Not Started | 40 min | OpenAI agent |
| 8 | CLI & V0 Verification | ⬜ Not Started | 25 min | Final testing |

**Legend**: ⬜ Not Started | 🔄 In Progress | ✅ Complete | ❌ Blocked

---

## Completed Items

### Planning & Setup
- [x] Created 8 phase files in `plans/workshop1/sessions/`
- [x] Created `/start-session` command
- [x] Set up permissions in `.claude/settings.local.json`
- [x] Created `.env` with OPENAI_API_KEY, HETZNER_API_TOKEN

### Phase Files Created
- [x] `phase_01_infrastructure.md` - Terraform + Ansible for Jaeger
- [x] `phase_02_project_structure.md` - DevHub skeleton
- [x] `phase_03_data_files.md` - JSON data files
- [x] `phase_04_vector_db.md` - VectorDB with ChromaDB
- [x] `phase_05_team_db.md` - TeamDB with SQLite
- [x] `phase_06_status_api.md` - StatusAPI mock
- [x] `phase_07_agent.md` - DevHubAgent with OpenAI
- [x] `phase_08_cli_verification.md` - CLI and testing

---

## Next Steps

1. **Implement Phase 5**: TeamDB Service
   - SQLite-based team/owner lookup
   - Intentional failure mode (10% stale data)
2. Continue with Phases 6-8 sequentially

## Infrastructure Details

| Resource | Value |
|----------|-------|
| Server IP | 46.224.233.5 |
| Server Type | cx23 (2 vCPU, 4GB RAM) |
| Location | nbg1 (Nuremberg) |
| Jaeger UI | https://46.224.233.5/jaeger |
| OTLP gRPC | http://46.224.233.5:4317 |
| OTLP HTTP | http://46.224.233.5:4318 |
| Basic Auth | workshop / salesforce2025 |

---

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| LLM Provider | OpenAI (GPT-4o-mini) | Workshop compatibility |
| Infrastructure | Terraform + Ansible | Follows ollama-service pattern |
| Terraform State | Local | Simple workshop setup |
| Python Version | 3.12.12 (asdf) | Colab compatibility, chromadb support |
| Jaeger Auth | Basic auth (nginx) | Simple security |
| Vector DB | ChromaDB | Easy setup, no external deps |
| Team DB | SQLite in-memory | Fast, no setup |

---

## Intentional Problems (for Workshop)

These must be preserved in V0 - students will debug them:

| Service | Problem | Rate | Trace Indicator |
|---------|---------|------|-----------------|
| VectorDB | Slow query | 10% | `latency_ms > 2000` |
| VectorDB | Connection failure | 5% | `ConnectionError` |
| VectorDB | Low similarity | 15% | `distance > 0.5` |
| TeamDB | Stale data | 10% | `is_active` flipped |
| StatusAPI | Timeout | 2% | `TimeoutError` |

---

## Workshop Scenarios

| Scenario | Query | Expected Issue |
|----------|-------|----------------|
| Wrong Owner | "Who owns vector search?" | David Kim (inactive) returned |
| Degraded Status | "Is staging working?" | Returns degraded with incident |
| Slow Search | Any search query | 3-second latency spike |

---

## Files to Create (by phase)

### Phase 1: Infrastructure
```
deploy/
├── terraform/
│   ├── providers.tf
│   ├── variables.tf
│   ├── servers.tf
│   ├── network.tf
│   └── outputs.tf
├── ansible/
│   ├── ansible.cfg
│   ├── inventory/hosts.yml.tpl
│   ├── playbooks/workshop.yml
│   └── roles/{common,nginx,jaeger}/
└── scripts/deploy.sh
```

### Phases 2-8: DevHub Application
```
devhub/
├── __init__.py
├── config.py
├── devhub.py
├── agent.py
├── services/
│   ├── __init__.py
│   ├── vector_db.py
│   ├── team_db.py
│   └── status_api.py
├── data/
│   ├── docs.json
│   ├── teams.json
│   └── status.json
├── requirements.txt
└── pyproject.toml
```

---

## Session Log

| Date | Action | Result |
|------|--------|--------|
| 2025-01-20 | Created phase files 1-8 | ✅ Complete |
| 2025-01-20 | Created /start-session command | ✅ Complete |
| 2025-01-20 | Created CURRENT_PROGRESS.md | ✅ Complete |
| 2026-01-20 | Phase 1: Terraform + Ansible deployment | ✅ Complete |
| 2026-01-20 | Phase 2: Project structure, Python 3.12.12 venv, deps | ✅ Complete |
| 2026-01-20 | Phase 3: Data files (docs, teams, status JSON) | ✅ Complete |
| 2026-01-20 | Phase 4: VectorDB with ChromaDB + failure modes | ✅ Complete |

---

## Blockers

_None currently_

---

## Notes

- Run `/start-session` at the beginning of each development session
- Use `/next-phase` to get transition prompt after completing each phase
- Update this file after each phase completion
