#!/usr/bin/env python3
"""Build Session 4 Debugging notebook from the plan."""

import json
import os

# Base notebook structure
notebook = {
    "cells": [],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.10.0"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 5
}

def add_markdown(content: str):
    """Add a markdown cell."""
    notebook["cells"].append({
        "cell_type": "markdown",
        "metadata": {},
        "source": content
    })

def add_code(content: str):
    """Add a code cell."""
    notebook["cells"].append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": content
    })

# =============================================================================
# SECTION 0: WELCOME & SETUP (Cells 1-12)
# =============================================================================

# Cell 1 - Title & Learning Objectives
add_markdown("""# Session 4: Debugging LLM-Based Features

**Salesforce AI Workshop Series**

---

## Learning Objectives

By the end of this session, you will be able to:

1. **Debug LLM reasoning chains** to understand WHY models made decisions
2. **Distinguish system vs model failures** in 30 seconds using traces
3. **Use Langfuse** for LLM-specific observability (generations, tool calls, reasoning)
4. **Replay production failures** for root cause analysis
5. **Convert failures into regression tests** that prevent recurrence

## Prerequisites

- Sessions 1-2 completed (DevHub with OpenTelemetry + DeepEval testing)
- Basic understanding of LLM tool calling
- No prior Langfuse experience required

## Session Structure

| Time | Activity |
|------|----------|
| 0:00-0:15 | Setup + The Wrong Tool Mystery |
| 0:15-0:35 | 5-Layer LLM Failure Framework |
| 0:35-1:05 | **Lab 1:** Add Langfuse to DevHub |
| 1:05-1:15 | Break |
| 1:15-1:30 | Demo: Trace Replay Workflow |
| 1:30-2:10 | **Lab 2:** Debug 4 Failure Scenarios |
| 2:10-2:35 | **Lab 3:** Failure → Regression Test |
| 2:35-2:45 | Wrap-up + Take-Home |""")

# Cell 2 - The Problem Story
add_markdown("""## The Problem: "Why Does The Agent Keep Calling The Wrong Tool?"

Your customer service agent repeatedly invokes the wrong tool...

**The Bug Report:**
> "User asked about order STATUS, but the agent called find_owner instead of check_status!"

You check your application logs:
```
INFO: query="What's the status of order #67890?"
INFO: tool_called=find_owner
INFO: tool_args={"service_name": "orders"}
```

That tells you WHAT happened, but not WHY.

**Questions logs DON'T answer:**
- Why did the model choose find_owner instead of check_status?
- What was in the conversation history that influenced this?
- What was the model's reasoning process?

**Is this:**
- A routing bug in your code?
- A prompt problem?
- A model error?
- Context from a previous conversation turn?

**Without LLM observability, you're debugging blind.**

This session teaches you how to see inside the LLM's reasoning process.""")

# Cell 3 - What We'll Build
add_markdown("""## What We'll Build Today

| Component | Purpose |
|-----------|---------|
| **Langfuse Integration** | See LLM reasoning, not just actions |
| **5-Layer Framework** | Systematic failure categorization |
| **Debug 4 Scenarios** | Hands-on failure diagnosis with CODE |
| **Failure → Test Pipeline** | Never have the same bug twice |

### The Key Insight

**Session 1 (Jaeger/OpenTelemetry):** Shows WHERE something happened
- Service latencies, error propagation, bottlenecks

**Session 4 (Langfuse):** Shows WHY the model decided
- Tool selection reasoning, context that influenced decisions, hallucination detection

Both are essential. Today we add the "WHY" layer.""")

# Cell 4 - Install Packages
add_code("""# =============================================================================
# SETUP: Install Required Packages
# =============================================================================
# Langfuse v3 for LLM observability
# DeepEval 3.x for evaluation metrics

!pip install -q langfuse>=3.0.0 deepeval>=3.0.0 openai>=1.0.0 chromadb>=0.4.0 rich>=13.0.0

print("Packages installed!")""")

# Cell 5 - Configure Credentials
add_code("""# =============================================================================
# CONFIGURATION: API Keys and Student Identity
# =============================================================================
import os
import uuid

# ─────────────────────────────────────────────────────────────────────────────
# INSTRUCTOR: Update these before the workshop
# ─────────────────────────────────────────────────────────────────────────────
LANGFUSE_PUBLIC_KEY = "pk-lf-..."  # Instructor provides
LANGFUSE_SECRET_KEY = "sk-lf-..."  # Instructor provides
LANGFUSE_HOST = "https://cloud.langfuse.com"

# OpenAI API Key
OPENAI_API_KEY = "sk-..."  # Or use instructor-provided key

# ─────────────────────────────────────────────────────────────────────────────
# STUDENT: Change this to your name (lowercase, no spaces)
# ─────────────────────────────────────────────────────────────────────────────
STUDENT_NAME = "your-name-here"  # e.g., "sarah-chen"

# Set environment variables
os.environ["LANGFUSE_PUBLIC_KEY"] = LANGFUSE_PUBLIC_KEY
os.environ["LANGFUSE_SECRET_KEY"] = LANGFUSE_SECRET_KEY
os.environ["LANGFUSE_HOST"] = LANGFUSE_HOST
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Generate unique session ID for this workshop run
LAB_SESSION_ID = f"{STUDENT_NAME}-session-{uuid.uuid4().hex[:8]}"

print(f"Student: {STUDENT_NAME}")
print(f"Session ID: {LAB_SESSION_ID}")
print(f"Langfuse Host: {LANGFUSE_HOST}")""")

# Cell 6 - Test Langfuse Connection
add_code("""# =============================================================================
# VERIFY: Test Langfuse Connection
# =============================================================================
# Langfuse v3's get_client() is idempotent (singleton pattern).
# Safe to re-run this cell without issues.

from langfuse import get_client

try:
    langfuse = get_client()

    # Create a test trace
    with langfuse.start_as_current_span(name="connection-test") as span:
        span.update(
            input={"test": "connection"},
            output={"status": "success"}
        )

    langfuse.flush()

    print("Langfuse connection successful!")
    print(f"View traces at: {LANGFUSE_HOST}")
    print(f"Filter by session: {LAB_SESSION_ID}")

except Exception as e:
    print(f"Langfuse connection failed: {e}")
    print("Check your LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY")""")

# Cell 7 - Configuration Class
add_code("""# =============================================================================
# CONFIGURATION: DevHub Settings with Failure Modes
# =============================================================================
from dataclasses import dataclass

@dataclass
class Config:
    \"\"\"DevHub configuration with intentional failure modes for debugging practice.\"\"\"

    # LLM Settings
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_MAX_TOKENS: int = 1024
    LLM_TEMPERATURE: float = 0.3

    # Latency ranges (milliseconds)
    VECTOR_DB_LATENCY_MIN: int = 50
    VECTOR_DB_LATENCY_MAX: int = 200
    TEAM_DB_LATENCY_MIN: int = 20
    TEAM_DB_LATENCY_MAX: int = 100
    STATUS_API_LATENCY_MIN: int = 30
    STATUS_API_LATENCY_MAX: int = 150

    # Session 1-2 failure rates
    VECTOR_DB_FAILURE_RATE: float = 0.05
    VECTOR_DB_SLOW_QUERY_RATE: float = 0.10
    VECTOR_DB_LOW_SIMILARITY_RATE: float = 0.15
    TEAM_DB_STALE_DATA_RATE: float = 0.10
    STATUS_API_TIMEOUT_RATE: float = 0.02

    # Session 4: LLM-specific failure scenarios (for debugging practice)
    CONTEXT_BLEED_RATE: float = 0.20      # Previous context affects tool selection
    HALLUCINATION_RATE: float = 0.15      # Model invents details
    PARAM_ERROR_RATE: float = 0.10        # Wrong parameters to correct tool

config = Config()
print("Config loaded with Session 4 failure modes")""")

# Cell 8 - Load Data Files
add_code("""# =============================================================================
# DATA: Load DevHub Knowledge Base
# =============================================================================

# Documentation entries
DOCS_DATA = [
    {
        "id": "doc-payments-auth",
        "title": "Payments API Authentication",
        "category": "api",
        "content": "To authenticate with the Payments API, use OAuth 2.0 client credentials flow. Obtain your client_id and client_secret from the Developer Portal. Make a POST request to /oauth/token with grant_type=client_credentials. The response includes an access_token valid for 1 hour. Include this token in the Authorization header as 'Bearer {token}' for all subsequent API calls."
    },
    {
        "id": "doc-billing-service",
        "title": "Billing Service Overview",
        "category": "service",
        "content": "The Billing Service handles all subscription management, invoice generation, and payment processing. Key endpoints: POST /v1/subscriptions (create), GET /v1/invoices (list), POST /v1/refunds (process refund). Rate limit: 100 requests/minute. Contact #payments-support for billing issues."
    },
    {
        "id": "doc-error-handling",
        "title": "Error Handling Standards",
        "category": "standards",
        "content": "All APIs return standard error responses with error_code, message, and request_id fields. Common codes: 400 (bad request), 401 (unauthorized), 429 (rate limited), 500 (internal error). Always log the request_id for debugging. Implement exponential backoff for 429 and 5xx errors."
    },
    {
        "id": "doc-rate-limiting",
        "title": "Rate Limiting Configuration",
        "category": "guide",
        "content": "Default rate limits: 100 req/min for standard tier, 1000 req/min for premium. Limits are per API key. Response header X-RateLimit-Remaining shows remaining quota. When rate limited, wait for X-RateLimit-Reset seconds before retrying."
    }
]

# Teams and owners
TEAMS_DATA = {
    "teams": [
        {"id": "team-payments", "name": "Payments Team", "slack_channel": "#payments-support"},
        {"id": "team-platform", "name": "Platform Team", "slack_channel": "#platform-help"},
        {"id": "team-data", "name": "Data Platform", "slack_channel": "#data-platform"}
    ],
    "owners": [
        {"id": "owner-sarah", "name": "Sarah Chen", "email": "sarah.chen@company.com",
         "team_id": "team-payments", "services": ["payments-api", "billing-service", "billing"], "is_active": True},
        {"id": "owner-james", "name": "James Wilson", "email": "james.wilson@company.com",
         "team_id": "team-platform", "services": ["rate-limiting", "api-gateway"], "is_active": True},
        {"id": "owner-david", "name": "David Kim", "email": "david.kim@company.com",
         "team_id": "team-data", "services": ["vector-search", "embeddings"], "is_active": False}  # Left company
    ]
}

# Service status
STATUS_DATA = {
    "services": [
        {"name": "payments-api", "status": "healthy", "uptime_percent": 99.95},
        {"name": "auth-service", "status": "healthy", "uptime_percent": 99.99},
        {"name": "staging", "status": "degraded", "uptime_percent": 95.5,
         "last_incident": "2024-01-15T09:00:00Z",
         "incident_description": "Database connection pool exhaustion causing intermittent 503 errors"},
        {"name": "vector-search", "status": "healthy", "uptime_percent": 99.8},
        {"name": "api-gateway", "status": "healthy", "uptime_percent": 99.97}
    ]
}

print(f"Loaded: {len(DOCS_DATA)} docs, {len(TEAMS_DATA['owners'])} owners, {len(STATUS_DATA['services'])} services")""")

# Cell 9 - Initialize Services
add_code("""# =============================================================================
# SERVICES: DevHub Components (Simplified for Session 4)
# =============================================================================
import time
import random

class VectorDB:
    \"\"\"Simplified vector search for workshop.\"\"\"

    def __init__(self, docs: list):
        self.docs = {d["id"]: d for d in docs}

    def search(self, query: str, top_k: int = 3) -> dict:
        \"\"\"Simple keyword-based search.\"\"\"
        query_lower = query.lower()
        results = []

        for doc in self.docs.values():
            score = 0
            content_lower = doc["content"].lower()
            title_lower = doc["title"].lower()

            for word in query_lower.split():
                if word in content_lower:
                    score += 1
                if word in title_lower:
                    score += 2

            if score > 0:
                results.append({"doc": doc, "score": score})

        results.sort(key=lambda x: x["score"], reverse=True)
        top_results = results[:top_k]

        return {
            "documents": [r["doc"]["content"] for r in top_results],
            "metadatas": [{"title": r["doc"]["title"], "id": r["doc"]["id"]} for r in top_results],
            "distances": [1.0 / (r["score"] + 1) for r in top_results]
        }


class TeamDB:
    \"\"\"Team and owner lookup.\"\"\"

    def __init__(self, data: dict):
        self.teams = {t["id"]: t for t in data["teams"]}
        self.owners = data["owners"]

    def find_owner(self, service_or_topic: str) -> dict:
        \"\"\"Find owner for a service.\"\"\"
        service_lower = service_or_topic.lower()

        for owner in self.owners:
            for service in owner["services"]:
                if service_lower in service.lower() or service.lower() in service_lower:
                    team = self.teams.get(owner["team_id"], {})
                    return {
                        "found": True,
                        "owner_name": owner["name"],
                        "owner_email": owner["email"],
                        "team_name": team.get("name", "Unknown"),
                        "slack_channel": team.get("slack_channel", ""),
                        "is_active": owner["is_active"]
                    }

        return {"found": False}


class StatusAPI:
    \"\"\"Service status checker.\"\"\"

    def __init__(self, data: dict):
        self.services = {s["name"]: s for s in data["services"]}

    def check_status(self, service_name: str) -> dict:
        \"\"\"Check service status.\"\"\"
        service_lower = service_name.lower()

        for name, service in self.services.items():
            if service_lower in name.lower() or name.lower() in service_lower:
                result = {
                    "found": True,
                    "service_name": name,
                    "status": service["status"],
                    "uptime_percent": service["uptime_percent"]
                }
                if "incident_description" in service:
                    result["incident"] = service["incident_description"]
                return result

        return {"found": False, "service_name": service_name}


# Initialize services
vector_db = VectorDB(DOCS_DATA)
team_db = TeamDB(TEAMS_DATA)
status_api = StatusAPI(STATUS_DATA)

print("Services initialized: VectorDB, TeamDB, StatusAPI")""")

# Cell 10 - DevHub V4
add_code("""# =============================================================================
# DEVHUB V4: Multi-turn Conversation Support (NO TRACING YET)
# =============================================================================
# This version supports conversation history, which enables the "context bleed"
# bug we'll debug in Lab 2.

from openai import OpenAI
import json

class DevHubV4:
    \"\"\"DevHub with multi-turn conversation support but NO tracing.\"\"\"

    def __init__(self, vector_db: VectorDB, team_db: TeamDB, status_api: StatusAPI):
        self.vector_db = vector_db
        self.team_db = team_db
        self.status_api = status_api
        self.client = OpenAI()
        self.sessions: dict[str, list] = {}  # session_id -> list of turns

        # Tool definitions for OpenAI function calling
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_docs",
                    "description": "Search documentation for API guides, SDK docs, how-to guides",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_owner",
                    "description": "Find the person or team who owns a service. Use for cancellation requests, escalations, or 'who can help' questions.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "service_name": {"type": "string", "description": "Service to find owner for"}
                        },
                        "required": ["service_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_status",
                    "description": "Check if a service is healthy, degraded, or down",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "service_name": {"type": "string", "description": "Service to check"}
                        },
                        "required": ["service_name"]
                    }
                }
            }
        ]

    def _get_system_prompt(self) -> str:
        return \"\"\"You are DevHub, an AI assistant for developers.
You help with:
- Finding documentation (use search_docs)
- Finding service owners (use find_owner) - especially for cancellations or escalations
- Checking service health (use check_status)

Be concise and helpful. Use the appropriate tool for each question.\"\"\"

    def _build_messages(self, user_query: str, session_id: str = None) -> list:
        \"\"\"Build messages with conversation history if session exists.\"\"\"
        messages = []

        # Include history if session exists (last 3 turns)
        if session_id and session_id in self.sessions:
            for turn in self.sessions[session_id][-3:]:
                messages.append({"role": "user", "content": turn["user"]})
                messages.append({"role": "assistant", "content": turn["assistant"]})

        messages.append({"role": "user", "content": user_query})
        return messages

    def _execute_tool(self, tool_name: str, args: dict) -> dict:
        \"\"\"Execute a tool and return results.\"\"\"
        try:
            if tool_name == "search_docs":
                result = self.vector_db.search(args.get("query", ""))
                return {"success": True, "data": result}
            elif tool_name == "find_owner":
                result = self.team_db.find_owner(args.get("service_name", ""))
                return {"success": True, "data": result}
            elif tool_name == "check_status":
                result = self.status_api.check_status(args.get("service_name", ""))
                return {"success": True, "data": result}
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def query(self, user_query: str, session_id: str = None) -> dict:
        \"\"\"Process a query with optional session context.\"\"\"
        messages = self._build_messages(user_query, session_id)

        # Get tool selection from LLM
        response = self.client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[{"role": "system", "content": self._get_system_prompt()}] + messages,
            tools=self.tools,
            tool_choice="auto",
            max_tokens=config.LLM_MAX_TOKENS,
            temperature=config.LLM_TEMPERATURE
        )

        assistant_message = response.choices[0].message
        tools_called = []
        tool_results = []

        # Execute tools if any
        if assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                result = self._execute_tool(tool_name, tool_args)

                tools_called.append(tool_name)
                tool_results.append({
                    "tool": tool_name,
                    "args": tool_args,
                    "result": result
                })

            # Generate final response with tool results
            tool_messages = messages + [assistant_message.model_dump()]
            for i, tool_call in enumerate(assistant_message.tool_calls):
                tool_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_results[i]["result"])
                })

            final_response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[{"role": "system", "content": self._get_system_prompt()}] + tool_messages,
                max_tokens=config.LLM_MAX_TOKENS
            )

            response_text = final_response.choices[0].message.content
        else:
            response_text = assistant_message.content or "I couldn't process that request."

        # Store in session
        if session_id:
            if session_id not in self.sessions:
                self.sessions[session_id] = []
            self.sessions[session_id].append({
                "user": user_query,
                "assistant": response_text,
                "tools": tools_called
            })

        return {
            "response": response_text,
            "tools_called": tools_called,
            "tool_results": tool_results
        }


# Create DevHub instance
devhub = DevHubV4(vector_db, team_db, status_api)
print("DevHub V4 created (multi-turn support, no tracing)")""")

# Cell 11 - Test DevHub V4
add_code("""# =============================================================================
# TEST: Verify DevHub V4 Works
# =============================================================================

test_result = devhub.query("How do I authenticate with the Payments API?")
print(f"Response: {test_result['response'][:200]}...")
print(f"Tools called: {test_result['tools_called']}")
print("\\nDevHub V4 is working!")""")

# Cell 12 - Setup Complete
add_markdown("""---

## Setup Complete!

If you see:
- Packages installed
- Langfuse connection successful
- DevHub V4 created and working

**You're ready to begin!**

---

**Next:** We'll explore a mysterious bug - the "Wrong Tool Mystery" - and see why traditional debugging fails for LLM applications.""")

# =============================================================================
# SECTION 1: THE WRONG TOOL MYSTERY (Cells 13-19)
# =============================================================================

# Cell 13 - Topic Header
add_markdown("""---

# Topic 1: The Wrong Tool Mystery

A real bug that will change how you think about LLM debugging.""")

# Cell 14 - The Bug Description + Diagram
add_markdown("""## The Bug: Wrong Tool Called

![Wrong Tool Mystery](https://raw.githubusercontent.com/axel-sirota/salesforce-ai-workshops/main/exercises/session_04/charts/00_wrong_tool_mystery.svg)

**What happened:**

| Turn | User Query | Expected Tool | Actual Tool |
|------|-----------|---------------|-------------|
| 1 | "I need to cancel my order #12345" | find_owner | find_owner |
| 2 | "What's the status of order #67890?" | check_status | find_owner |

**Turn 1:** User asks about cancellation → Agent correctly calls `find_owner` to escalate

**Turn 2:** User asks about order status → Agent INCORRECTLY calls `find_owner` instead of `check_status`

**The question:** Why did the agent pick the wrong tool for Turn 2?""")

# Cell 15 - Demo: Recreate The Bug
add_code("""# =============================================================================
# DEMO: Recreate the "Wrong Tool" Bug
# =============================================================================
# Watch what happens when we run these queries in sequence.

# Create a session to maintain conversation history
bug_session = "bug-demo-session"

print("=" * 60)
print("TURN 1: Cancellation Request")
print("=" * 60)

turn1 = devhub.query(
    "I need to cancel my order #12345. Who can help?",
    session_id=bug_session
)
print(f"Query: 'I need to cancel my order #12345. Who can help?'")
print(f"Tools called: {turn1['tools_called']}")
print(f"Response: {turn1['response'][:200]}...")

print("\\n" + "=" * 60)
print("TURN 2: Status Request (WATCH THE TOOL!)")
print("=" * 60)

turn2 = devhub.query(
    "What's the status of order #67890?",
    session_id=bug_session
)
print(f"Query: 'What's the status of order #67890?'")
print(f"Tools called: {turn2['tools_called']}")  # Often shows find_owner instead of check_status!
print(f"Response: {turn2['response'][:200]}...")

print("\\n" + "=" * 60)
print("ANALYSIS")
print("=" * 60)
if "find_owner" in turn2['tools_called']:
    print("BUG REPRODUCED: Agent called find_owner for a status question!")
    print("But WHY? The query clearly asks about STATUS...")
else:
    print("Interesting - this time it worked correctly.")
    print("(The bug doesn't happen 100% of the time - that's part of the mystery!)")""")

# Cell 16 - Traditional Debugging Attempt
add_code("""# =============================================================================
# TRADITIONAL DEBUGGING: What We Know
# =============================================================================
# Let's see what traditional debugging tells us...

print("What traditional logs would show:")
print("-" * 40)
print(f"Turn 1: query='cancel order #12345', tool=find_owner")
print(f"Turn 2: query='status of #67890', tool={turn2['tools_called']}")
print()
print("What traditional logs DON'T show:")
print("-" * 40)
print("- What was in the conversation history?")
print("- What context influenced the model's decision?")
print("- Why did the model think find_owner was appropriate?")
print("- What was the model's reasoning process?")
print()
print("We see WHAT happened, but not WHY.")""")

# Cell 17 - The Visibility Gap
add_markdown("""## The Visibility Gap

Traditional application logging shows:
- **Request received** ✅
- **Tool called** ✅
- **Response sent** ✅

But for LLM applications, we also need to see:
- **Conversation history** that influenced the decision
- **Model's reasoning** about which tool to use
- **Context** passed to the model
- **Confidence** in the tool selection

**The problem:** LLMs make decisions based on context you can't see in traditional logs.

**The solution:** LLM-specific observability tools like **Langfuse**.""")

# Cell 18 - Why This Bug Happens
add_markdown("""## Spoiler: Why This Bug Happens

**Root Cause: Context Bleed**

When we built DevHub V4 with multi-turn support, we included conversation history:

```python
def _build_messages(self, user_query: str, session_id: str = None) -> list:
    messages = []
    if session_id and session_id in self.sessions:
        for turn in self.sessions[session_id][-3:]:  # Last 3 turns
            messages.append({"role": "user", "content": turn["user"]})
            messages.append({"role": "assistant", "content": turn["assistant"]})
    messages.append({"role": "user", "content": user_query})
    return messages
```

**What happens:**
1. Turn 1 mentions "cancel" → Agent correctly calls `find_owner`
2. Turn 2's context INCLUDES Turn 1 (with "cancel")
3. Model sees "cancel" in history and thinks "cancellation context"
4. Model chooses `find_owner` because "cancel" keywords are still present

**Without Langfuse:** You'd spend HOURS guessing
**With Langfuse:** You'd see the history in 30 SECONDS

This is the power of LLM observability.""")

# Cell 19 - Key Insight
add_markdown("""## Key Insight: LLM Bugs Are Different

**Traditional bugs:** Code does the wrong thing
- Fix: Change the code

**LLM bugs:** Model reasons incorrectly based on context
- Fix: Change the context, prompt, or model settings

**You need different debugging tools for different bug types.**

| Bug Type | Traditional Debugging | LLM Debugging |
|----------|----------------------|---------------|
| Code error | Stack trace | Stack trace |
| Performance | Profiler | Profiler |
| **Wrong decision** | ❌ Useless | ✅ Trace reasoning |
| **Hallucination** | ❌ Can't detect | ✅ Compare to sources |
| **Context bleed** | ❌ Can't see context | ✅ See full history |

**Coming up:** The 5-Layer Framework for systematically categorizing LLM failures.""")

# =============================================================================
# SECTION 2: 5-LAYER LLM FAILURE FRAMEWORK (Cells 20-28)
# =============================================================================

# Cell 20 - Topic Header
add_markdown("""---

# Topic 2: The 5-Layer LLM Failure Framework

A systematic approach to categorizing and debugging LLM failures.""")

# Cell 21 - Framework Overview + Diagram
add_markdown("""## The 5-Layer Framework

![5-Layer Framework](https://raw.githubusercontent.com/axel-sirota/salesforce-ai-workshops/main/exercises/session_04/charts/01_five_layer_framework.svg)

When an LLM application fails, the problem exists in one of five layers:

| Layer | Name | What Can Go Wrong |
|-------|------|-------------------|
| 1 | **Prompt** | Bad instructions, wrong context, history issues |
| 2 | **Retrieval** | No relevant docs, wrong docs, stale data |
| 3 | **Generation** | Hallucination, wrong format, refusal |
| 4 | **Validation** | Schema errors, constraint violations |
| 5 | **Latency** | Slow retrieval, slow LLM, timeouts |

**Key insight:** Each layer has different symptoms and different fixes.""")

# Cell 22 - Layer 1 - Prompt
add_markdown("""## Layer 1: Prompt Layer

**What it is:** The instructions and context given to the model.

**What can go wrong:**

| Symptom | Cause | Debug Approach |
|---------|-------|----------------|
| Wrong tool selected | Ambiguous tool descriptions | Check tool descriptions in trace |
| Inconsistent behavior | Temperature too high | Check model settings |
| Context bleed | History included bad context | Check conversation history in trace |
| Ignores instructions | Prompt too long/confusing | Check full prompt content |

**Debugging in Langfuse:**
- View the full prompt sent to the model
- See conversation history included
- Check system prompt content
- Verify tool descriptions""")

# Cell 23 - Layer 2 - Retrieval
add_markdown("""## Layer 2: Retrieval Layer

**What it is:** Finding relevant information (RAG, database queries).

**What can go wrong:**

| Symptom | Cause | Debug Approach |
|---------|-------|----------------|
| "I don't have information about X" | No docs match query | Check retrieval results |
| Wrong answer | Retrieved wrong docs | Check similarity scores |
| Outdated information | Stale data in vector DB | Check document timestamps |
| Partial answer | Not enough docs retrieved | Check top_k setting |

**Debugging in Langfuse:**
- See what was retrieved
- Check similarity/distance scores
- Verify document content
- Compare query vs retrieved docs""")

# Cell 24 - Layer 3 - Generation
add_markdown("""## Layer 3: Generation Layer

**What it is:** The LLM generating text/decisions.

**What can go wrong:**

| Symptom | Cause | Debug Approach |
|---------|-------|----------------|
| Hallucination | Model invents facts | Compare output to retrieval context |
| Wrong format | Unclear format instructions | Check prompt format requirements |
| Refusal | Safety filters triggered | Check model response |
| Inconsistent | Non-deterministic (temperature) | Check temperature setting |

**Debugging in Langfuse:**
- Compare generation to retrieval context
- Check if output matches instructions
- View raw model response
- Verify token counts and settings

**This is where DeepEval helps:** FaithfulnessMetric catches hallucinations.""")

# Cell 25 - Layer 4 - Validation
add_markdown("""## Layer 4: Validation Layer

**What it is:** Ensuring outputs meet requirements.

**What can go wrong:**

| Symptom | Cause | Debug Approach |
|---------|-------|----------------|
| Schema errors | Model output doesn't match schema | Check JSON structure |
| Invalid parameters | Wrong args to tool | Check tool call arguments |
| Constraint violation | Output exceeds limits | Check constraints in trace |
| Type errors | Wrong data types | Check parameter types |

**Debugging in Langfuse:**
- View tool call arguments
- Check parameter values
- Verify schema compliance
- Compare expected vs actual format""")

# Cell 26 - Layer 5 - Latency
add_markdown("""## Layer 5: Latency Layer

**What it is:** Performance and timing issues.

**What can go wrong:**

| Symptom | Cause | Debug Approach |
|---------|-------|----------------|
| Slow responses | Large context window | Check token counts |
| Timeouts | Model overloaded | Check LLM latency |
| Bottlenecks | Slow retrieval | Check span timings |
| Cost spikes | Too many tokens | Check token usage |

**Debugging in Langfuse:**
- View span timings
- Check token counts
- Identify bottleneck operations
- Compare across traces""")

# Cell 27 - Decision Tree + Diagram
add_markdown("""## Debug Decision Tree: 30-Second Triage

![Debug Decision Tree](https://raw.githubusercontent.com/axel-sirota/salesforce-ai-workshops/main/exercises/session_04/charts/03_debug_decision_tree.svg)

**Quick triage process:**

1. **Did it error?** → Check error message and stack trace
2. **Did it pick the right tool?** → Check Prompt Layer (conversation history)
3. **Did it pass valid parameters?** → Check Validation Layer
4. **Did retrieval return good results?** → Check Retrieval Layer (similarity scores)
5. **Does output match retrieval?** → Check Generation Layer (hallucination)
6. **Is it slow?** → Check Latency Layer (span timings)

**With Langfuse, you can answer these in 30 seconds instead of hours.**""")

# Cell 28 - Framework Summary
add_markdown("""## Framework Summary

**Use the 5-Layer Framework to:**

1. **Categorize** the failure type immediately
2. **Focus** your investigation on the right layer
3. **Apply** layer-specific debugging techniques
4. **Fix** the root cause, not symptoms

| If you see... | Check this layer |
|---------------|------------------|
| Wrong tool called | Prompt (history, tool descriptions) |
| "No information found" | Retrieval (query, similarity) |
| Made-up facts | Generation (hallucination) |
| Invalid arguments | Validation (schema, params) |
| Slow response | Latency (timings) |

**Coming up:** Lab 1 - We'll add Langfuse to DevHub so you can actually SEE these layers.""")

# =============================================================================
# SECTION 3: LAB 1 - ADD LANGFUSE TO DEVHUB (Cells 29-42)
# =============================================================================

# Cell 29 - Lab Header
add_markdown("""---

# Lab 1: Add Langfuse Instrumentation to DevHub

**Duration:** ~30 minutes

**Goal:** Instrument DevHub with Langfuse so we can see LLM reasoning.

**What you'll build:**
- Task 1: Configure Langfuse client
- Task 2: Add @observe() decorator for automatic tracing
- Task 3: Add nested spans for tool planning
- Task 4: Add spans for tool execution
- Task 5: Add span for response synthesis""")

# Cell 30 - Langfuse Trace Model + Diagram
add_markdown("""## Langfuse Trace Model

![Langfuse Trace Model](https://raw.githubusercontent.com/axel-sirota/salesforce-ai-workshops/main/exercises/session_04/charts/02_langfuse_trace_model.svg)

**Hierarchy:**
```
Session (groups related traces)
└── Trace (one user interaction)
    ├── Span: tool-planning
    │   └── Generation: LLM call
    ├── Span: tool.search_docs
    ├── Span: tool.find_owner
    └── Span: response-synthesis
        └── Generation: LLM call
```

**Key concepts:**
- **Session:** Groups traces from same conversation
- **Trace:** One request/response cycle
- **Span:** A logical operation within a trace
- **Generation:** An LLM call (automatically tracked)""")

# Cell 31 - Task 1 Instructions
add_markdown("""## Task 1: Understand Langfuse v3 Patterns

**Goal:** Learn the Langfuse v3 API patterns we'll use.

**Key patterns:**

```python
# Import
from langfuse import observe, get_client

# Get client (singleton, safe to call multiple times)
langfuse = get_client()

# Update trace metadata
langfuse.update_current_trace(
    session_id="...",
    user_id="...",
    input="...",
    metadata={...}
)

# Create nested spans
with langfuse.start_as_current_span(name="operation", input={...}) as span:
    # ... your code ...
    span.update(output={...})
```

**Time:** Review only (~2 minutes)""")

# Cell 32 - Task 2 Instructions
add_markdown("""## Task 2: Create DevHubWithLangfuse Class

**Goal:** Create an instrumented version of DevHub with Langfuse tracing.

**What to implement:**

1. **@observe() decorator** on the `query()` method
2. **update_current_trace()** to set session and user metadata
3. **Nested spans** for:
   - `tool-planning`: The LLM call that selects tools
   - `tool.{name}`: Each tool execution
   - `response-synthesis`: The final LLM response

**Pattern:**
```python
@observe()
def query(self, user_query: str, session_id: str = None) -> dict:
    langfuse = get_client()
    langfuse.update_current_trace(session_id=..., user_id=..., input=...)

    with langfuse.start_as_current_span(name="tool-planning", input={...}) as span:
        # LLM call to select tools
        span.update(output={...})

    for tool in tools_to_call:
        with langfuse.start_as_current_span(name=f"tool.{tool_name}", input=...) as span:
            # Execute tool
            span.update(output=...)

    with langfuse.start_as_current_span(name="response-synthesis", input={...}) as span:
        # Final LLM response
        span.update(output=...)
```

**Time:** ~15 minutes""")

# Cell 33 - Task 2 Starter Code
add_code("""# =============================================================================
# TASK 2: Create DevHubWithLangfuse
# =============================================================================
# Add Langfuse instrumentation to see LLM reasoning.
#
# TIME: ~15 minutes
# =============================================================================

from langfuse import observe, get_client
from openai import OpenAI
import json

class DevHubWithLangfuse:
    \"\"\"
    DevHub with Langfuse observability.

    This version captures:
    - Full query traces with session grouping
    - Tool selection and reasoning
    - Tool execution results
    \"\"\"

    def __init__(self, vector_db: VectorDB, team_db: TeamDB, status_api: StatusAPI):
        self.vector_db = vector_db
        self.team_db = team_db
        self.status_api = status_api
        self.client = OpenAI()
        self.sessions: dict[str, list] = {}

        # Same tools as DevHubV4
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_docs",
                    "description": "Search documentation for API guides, SDK docs, how-to guides",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_owner",
                    "description": "Find the person or team who owns a service. Use for cancellation requests, escalations, or 'who can help' questions.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "service_name": {"type": "string", "description": "Service to find owner for"}
                        },
                        "required": ["service_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_status",
                    "description": "Check if a service is healthy, degraded, or down",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "service_name": {"type": "string", "description": "Service to check"}
                        },
                        "required": ["service_name"]
                    }
                }
            }
        ]

    def _get_system_prompt(self) -> str:
        return \"\"\"You are DevHub, an AI assistant for developers.
You help with:
- Finding documentation (use search_docs)
- Finding service owners (use find_owner) - especially for cancellations or escalations
- Checking service health (use check_status)

Be concise and helpful. Use the appropriate tool for each question.\"\"\"

    def _build_messages(self, user_query: str, session_id: str = None) -> list:
        \"\"\"Build messages with conversation history.\"\"\"
        messages = []

        if session_id and session_id in self.sessions:
            for turn in self.sessions[session_id][-3:]:
                messages.append({"role": "user", "content": turn["user"]})
                messages.append({"role": "assistant", "content": turn["assistant"]})

        messages.append({"role": "user", "content": user_query})
        return messages

    # =========================================================================
    # YOUR CODE: Add @observe() decorator here
    # =========================================================================
    def query(self, user_query: str, session_id: str = None) -> dict:
        \"\"\"
        Process a user query with Langfuse tracing.
        \"\"\"
        # ─────────────────────────────────────────────────────────────────────
        # YOUR CODE: Get langfuse client and update trace metadata
        # ─────────────────────────────────────────────────────────────────────
        # langfuse = get_client()
        # langfuse.update_current_trace(
        #     session_id=session_id or LAB_SESSION_ID,
        #     user_id=STUDENT_NAME,
        #     input=user_query,
        #     metadata={"devhub_version": "v4-langfuse"}
        # )
        pass  # YOUR CODE HERE
        # ─────────────────────────────────────────────────────────────────────

        # Build messages with history
        messages = self._build_messages(user_query, session_id)

        # ─────────────────────────────────────────────────────────────────────
        # YOUR CODE: Wrap LLM call in tool-planning span
        # ─────────────────────────────────────────────────────────────────────
        # with langfuse.start_as_current_span(
        #     name="tool-planning",
        #     input={"query": user_query, "history_length": len(messages) - 1}
        # ) as planning_span:
        #     response = self.client.chat.completions.create(...)
        #     planning_span.update(output={...})

        # For now, just make the call without span (you'll fix this)
        response = self.client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[{"role": "system", "content": self._get_system_prompt()}] + messages,
            tools=self.tools,
            tool_choice="auto",
            max_tokens=config.LLM_MAX_TOKENS,
            temperature=config.LLM_TEMPERATURE
        )
        # ─────────────────────────────────────────────────────────────────────

        assistant_message = response.choices[0].message
        tools_called = []
        tool_results = []

        if assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                # ─────────────────────────────────────────────────────────────
                # YOUR CODE: Wrap tool execution in a span
                # ─────────────────────────────────────────────────────────────
                # with langfuse.start_as_current_span(
                #     name=f"tool.{tool_name}",
                #     input=tool_args
                # ) as tool_span:
                #     result = self._execute_tool(tool_name, tool_args)
                #     tool_span.update(output=result)

                # For now, just execute without span (you'll fix this)
                result = self._execute_tool(tool_name, tool_args)
                # ─────────────────────────────────────────────────────────────

                tools_called.append(tool_name)
                tool_results.append({
                    "tool": tool_name,
                    "args": tool_args,
                    "result": result
                })

            # Generate final response
            tool_messages = messages + [assistant_message.model_dump()]
            for i, tool_call in enumerate(assistant_message.tool_calls):
                tool_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_results[i]["result"])
                })

            # ─────────────────────────────────────────────────────────────────
            # YOUR CODE: Wrap response synthesis in a span
            # ─────────────────────────────────────────────────────────────────
            # with langfuse.start_as_current_span(
            #     name="response-synthesis",
            #     input={"tools_used": tools_called}
            # ) as synth_span:
            #     final_response = self.client.chat.completions.create(...)
            #     synth_span.update(output=response_text)

            # For now, just make the call without span (you'll fix this)
            final_response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[{"role": "system", "content": self._get_system_prompt()}] + tool_messages,
                max_tokens=config.LLM_MAX_TOKENS
            )
            response_text = final_response.choices[0].message.content
            # ─────────────────────────────────────────────────────────────────
        else:
            response_text = assistant_message.content or "I couldn't process that request."

        # Store in session
        if session_id:
            if session_id not in self.sessions:
                self.sessions[session_id] = []
            self.sessions[session_id].append({
                "user": user_query,
                "assistant": response_text,
                "tools": tools_called
            })

        # ─────────────────────────────────────────────────────────────────────
        # YOUR CODE: Update trace with final output
        # ─────────────────────────────────────────────────────────────────────
        # langfuse.update_current_trace(output=response_text)
        pass  # YOUR CODE HERE
        # ─────────────────────────────────────────────────────────────────────

        return {
            "response": response_text,
            "tools_called": tools_called,
            "tool_results": tool_results
        }

    def _execute_tool(self, tool_name: str, args: dict) -> dict:
        \"\"\"Execute a tool and return results.\"\"\"
        try:
            if tool_name == "search_docs":
                result = self.vector_db.search(args.get("query", ""))
                return {"success": True, "data": result}
            elif tool_name == "find_owner":
                result = self.team_db.find_owner(args.get("service_name", ""))
                return {"success": True, "data": result}
            elif tool_name == "check_status":
                result = self.status_api.check_status(args.get("service_name", ""))
                return {"success": True, "data": result}
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Test the class compiles
print("DevHubWithLangfuse class defined")
print("Now implement the YOUR CODE sections!")""")

# Cell 34 - Task 2 Solution (Collapsed)
add_code("""# =============================================================================
# SOLUTION: Task 2 - DevHubWithLangfuse with Full Instrumentation
# =============================================================================
# Expand this cell if you need help.

from langfuse import observe, get_client
from openai import OpenAI
import json

class DevHubWithLangfuseSolution:
    \"\"\"DevHub with complete Langfuse instrumentation.\"\"\"

    def __init__(self, vector_db: VectorDB, team_db: TeamDB, status_api: StatusAPI):
        self.vector_db = vector_db
        self.team_db = team_db
        self.status_api = status_api
        self.client = OpenAI()
        self.sessions: dict[str, list] = {}

        self.tools = [
            {"type": "function", "function": {"name": "search_docs", "description": "Search documentation", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
            {"type": "function", "function": {"name": "find_owner", "description": "Find service owner", "parameters": {"type": "object", "properties": {"service_name": {"type": "string"}}, "required": ["service_name"]}}},
            {"type": "function", "function": {"name": "check_status", "description": "Check service status", "parameters": {"type": "object", "properties": {"service_name": {"type": "string"}}, "required": ["service_name"]}}}
        ]

    def _get_system_prompt(self) -> str:
        return "You are DevHub, an AI assistant. Use search_docs for documentation, find_owner for service owners, check_status for service health."

    def _build_messages(self, user_query: str, session_id: str = None) -> list:
        messages = []
        if session_id and session_id in self.sessions:
            for turn in self.sessions[session_id][-3:]:
                messages.append({"role": "user", "content": turn["user"]})
                messages.append({"role": "assistant", "content": turn["assistant"]})
        messages.append({"role": "user", "content": user_query})
        return messages

    @observe()  # SOLUTION: Add decorator
    def query(self, user_query: str, session_id: str = None) -> dict:
        # SOLUTION: Get client and update trace
        langfuse = get_client()
        langfuse.update_current_trace(
            session_id=session_id or LAB_SESSION_ID,
            user_id=STUDENT_NAME,
            input=user_query,
            metadata={"devhub_version": "v4-langfuse", "has_history": session_id in self.sessions if session_id else False}
        )

        messages = self._build_messages(user_query, session_id)

        # SOLUTION: Tool planning span
        with langfuse.start_as_current_span(name="tool-planning", input={"query": user_query, "history_length": len(messages) - 1}) as planning_span:
            response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[{"role": "system", "content": self._get_system_prompt()}] + messages,
                tools=self.tools, tool_choice="auto", max_tokens=config.LLM_MAX_TOKENS, temperature=config.LLM_TEMPERATURE
            )
            assistant_message = response.choices[0].message
            tools_to_call = [{"name": tc.function.name, "args": json.loads(tc.function.arguments)} for tc in (assistant_message.tool_calls or [])]
            planning_span.update(output={"tools_selected": [t["name"] for t in tools_to_call]})

        tools_called = []
        tool_results = []

        if assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                # SOLUTION: Tool execution span
                with langfuse.start_as_current_span(name=f"tool.{tool_name}", input=tool_args) as tool_span:
                    result = self._execute_tool(tool_name, tool_args)
                    tool_span.update(output=result)

                tools_called.append(tool_name)
                tool_results.append({"tool": tool_name, "args": tool_args, "result": result})

            tool_messages = messages + [assistant_message.model_dump()]
            for i, tool_call in enumerate(assistant_message.tool_calls):
                tool_messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(tool_results[i]["result"])})

            # SOLUTION: Response synthesis span
            with langfuse.start_as_current_span(name="response-synthesis", input={"tools_used": tools_called}) as synth_span:
                final_response = self.client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=[{"role": "system", "content": self._get_system_prompt()}] + tool_messages,
                    max_tokens=config.LLM_MAX_TOKENS
                )
                response_text = final_response.choices[0].message.content
                synth_span.update(output=response_text)
        else:
            response_text = assistant_message.content or "I couldn't process that request."

        if session_id:
            if session_id not in self.sessions:
                self.sessions[session_id] = []
            self.sessions[session_id].append({"user": user_query, "assistant": response_text, "tools": tools_called})

        # SOLUTION: Update trace with output
        langfuse.update_current_trace(output=response_text)

        return {"response": response_text, "tools_called": tools_called, "tool_results": tool_results}

    def _execute_tool(self, tool_name: str, args: dict) -> dict:
        try:
            if tool_name == "search_docs": return {"success": True, "data": self.vector_db.search(args.get("query", ""))}
            elif tool_name == "find_owner": return {"success": True, "data": self.team_db.find_owner(args.get("service_name", ""))}
            elif tool_name == "check_status": return {"success": True, "data": self.status_api.check_status(args.get("service_name", ""))}
            else: return {"success": False, "error": f"Unknown tool: {tool_name}"}
        except Exception as e: return {"success": False, "error": str(e)}

print("Solution: DevHubWithLangfuseSolution defined")""")

# Cell 35 - Test Your Implementation
add_code("""# =============================================================================
# TEST: Verify Your Langfuse Instrumentation
# =============================================================================

# Use your implementation or the solution
# devhub_traced = DevHubWithLangfuse(vector_db, team_db, status_api)
devhub_traced = DevHubWithLangfuseSolution(vector_db, team_db, status_api)

# Run a test query
test_result = devhub_traced.query("How do I authenticate with the Payments API?")

print(f"Response: {test_result['response'][:200]}...")
print(f"Tools called: {test_result['tools_called']}")
print()
print(f"View your trace at: {LANGFUSE_HOST}")
print(f"Filter by session: {LAB_SESSION_ID}")

# Flush to ensure trace is sent
langfuse = get_client()
langfuse.flush()""")

# Cell 36 - Multi-Turn Test
add_markdown("""## Test Multi-Turn: Reproduce the Bug with Visibility

Now let's reproduce the "wrong tool" bug - but this time we can SEE why it happens!

![Multi-Turn Session](https://raw.githubusercontent.com/axel-sirota/salesforce-ai-workshops/main/exercises/session_04/charts/04_multi_turn_session.svg)""")

# Cell 37 - Multi-Turn Test Code
add_code("""# =============================================================================
# TEST: Multi-Turn Bug Reproduction with Tracing
# =============================================================================

# Create a new session for this test
debug_session = f"debug-session-{uuid.uuid4().hex[:6]}"

print("=" * 60)
print("TURN 1: Cancellation Request")
print("=" * 60)

turn1 = devhub_traced.query(
    "I need to cancel my subscription. Who can help?",
    session_id=debug_session
)
print(f"Query: 'I need to cancel my subscription. Who can help?'")
print(f"Tools called: {turn1['tools_called']}")

print("\\n" + "=" * 60)
print("TURN 2: Status Check (Watch for context bleed!)")
print("=" * 60)

turn2 = devhub_traced.query(
    "Is the payments API working?",
    session_id=debug_session
)
print(f"Query: 'Is the payments API working?'")
print(f"Tools called: {turn2['tools_called']}")

# Flush traces
langfuse.flush()

print("\\n" + "=" * 60)
print("VIEW YOUR TRACES")
print("=" * 60)
print(f"Open Langfuse: {LANGFUSE_HOST}")
print(f"Filter by session_id: {debug_session}")
print()
print("Look for:")
print("1. Turn 1 trace: Should show find_owner called")
print("2. Turn 2 trace: Check the 'tool-planning' span")
print("3. In Turn 2's tool-planning input, look at history_length")
print("4. The context from Turn 1 ('cancel') may have influenced Turn 2!")""")

# Cell 38 - Lab 1 Complete
add_markdown("""## Lab 1 Complete!

You've successfully added Langfuse instrumentation to DevHub.

**What you built:**
- @observe() decorator for automatic tracing
- Trace metadata (session_id, user_id)
- Nested spans for tool-planning, tool execution, response-synthesis
- Full visibility into LLM reasoning

**What you can now see in Langfuse:**
- Complete conversation history
- Which tools were selected and why
- Tool execution results
- Response synthesis process

**Next:** Demo of the trace replay workflow, then Lab 2 where you'll debug 4 failure scenarios.""")

# =============================================================================
# SECTION 4: DEMO - TRACE REPLAY WORKFLOW (Cells 39-43)
# =============================================================================

# Cell 39 - Demo Header
add_markdown("""---

# Demo: Trace Replay Debugging Workflow

**Duration:** ~15 minutes (instructor-led)

Watch how to use Langfuse traces to debug LLM failures in 30 seconds.""")

# Cell 40 - The Workflow
add_markdown("""## The Debug Workflow

**Step 1: Find the failing trace**
- Filter by session_id, user_id, or time range
- Look for traces with errors or unexpected outputs

**Step 2: Examine the trace structure**
- Check tool-planning span: What tools were selected?
- Check tool execution spans: What data was returned?
- Check response-synthesis span: What was generated?

**Step 3: Identify the layer**
- Wrong tool? → Prompt Layer (check history)
- No/bad data? → Retrieval Layer (check results)
- Made-up facts? → Generation Layer (compare to context)
- Invalid params? → Validation Layer (check args)

**Step 4: Fix and verify**
- Make the fix
- Run the same query
- Compare traces""")

# Cell 41 - Demo Code
add_code("""# =============================================================================
# DEMO: Instructor walks through finding context bleed in Langfuse
# =============================================================================
# This code recreates the bug so instructor can demonstrate trace analysis.

demo_session = f"demo-context-bleed-{uuid.uuid4().hex[:6]}"

# Turn 1: Sets up the "cancel" context
turn1 = devhub_traced.query(
    "I need to cancel my billing subscription immediately!",
    session_id=demo_session
)
print(f"Turn 1 tools: {turn1['tools_called']}")

# Turn 2: Should check status, but might be influenced by Turn 1
turn2 = devhub_traced.query(
    "What's the current status of the payments API?",
    session_id=demo_session
)
print(f"Turn 2 tools: {turn2['tools_called']}")

langfuse.flush()

print(f"\\nDemo session: {demo_session}")
print(f"Open Langfuse and filter by this session to see both traces.")
print("\\nIn the Turn 2 trace, look at the 'tool-planning' span input.")
print("You'll see history_length > 0, meaning Turn 1's context was included!")""")

# Cell 42 - What to Look For
add_markdown("""## What to Look for in Langfuse

### In the Turn 2 Trace:

**1. tool-planning span INPUT:**
```json
{
  "query": "What's the current status of the payments API?",
  "history_length": 2  // <-- This means 2 previous messages were included!
}
```

**2. The conversation history included "cancel" from Turn 1**

**3. tool-planning span OUTPUT:**
```json
{
  "tools_selected": ["find_owner"],  // <-- Wrong! Should be check_status
  "tool_calls": [...]
}
```

### Root Cause Identified in 30 Seconds:
The model saw "cancel" in history and associated it with owner lookup context.

### Fix Options:
1. Clear session between unrelated queries
2. Add instruction: "Consider only the current query, not history, for tool selection"
3. Reduce history window from 3 turns to 1""")

# Cell 43 - Demo Complete
add_markdown("""## Demo Complete!

**Key takeaways:**

1. **Find** → Filter traces by session/user/time
2. **Examine** → Check span inputs and outputs
3. **Identify** → Use 5-Layer Framework to categorize
4. **Fix** → Address root cause, not symptoms

**Your turn:** In Lab 2, you'll debug 4 different failure scenarios using this workflow.""")

# =============================================================================
# SECTION 5: LAB 2 - DEBUG 4 FAILURE SCENARIOS (Cells 44-57)
# =============================================================================

# Cell 44 - Lab Header
add_markdown("""---

# Lab 2: Debug 4 Failure Scenarios

**Duration:** ~40 minutes

**Goal:** Apply the 5-Layer Framework to diagnose and fix real LLM failures.

**Scenarios:**
1. **Context Bleed** (Prompt Layer) - Previous context affects tool selection
2. **Retrieval Failure** (Retrieval Layer) - No relevant docs found
3. **Hallucination** (Generation Layer) - Model invents facts
4. **Parameter Error** (Validation Layer) - Wrong parameters to tool

**For each scenario, you will:**
1. Run the failing code
2. Find the trace in Langfuse
3. Identify the layer and root cause
4. Write code to fix or detect the issue""")

# Cell 45 - Scenario 1 Header
add_markdown("""## Scenario 1: Context Bleed (Prompt Layer)

![Context Bleed](https://raw.githubusercontent.com/axel-sirota/salesforce-ai-workshops/main/exercises/session_04/charts/05_context_bleed_scenario.svg)

**The Bug:** Previous conversation context causes wrong tool selection.

**Layer:** Prompt Layer

**Your tasks:**
1. Run the scenario code
2. Find the trace and identify the context bleed
3. Write code to detect when history might be causing issues""")

# Cell 46 - Scenario 1 Code
add_code("""# =============================================================================
# SCENARIO 1: Context Bleed
# =============================================================================
# Run this to create a context bleed situation, then debug it.

scenario1_session = f"scenario1-{uuid.uuid4().hex[:6]}"

print("=" * 60)
print("SCENARIO 1: Context Bleed")
print("=" * 60)

# Turn 1: Cancellation context
s1_turn1 = devhub_traced.query(
    "I need to cancel my order and get a refund. Who handles that?",
    session_id=scenario1_session
)
print(f"Turn 1: 'Cancel order, who handles refund?'")
print(f"  Tools: {s1_turn1['tools_called']}")

# Turn 2: Status query (should use check_status, not find_owner)
s1_turn2 = devhub_traced.query(
    "Is the staging environment working right now?",
    session_id=scenario1_session
)
print(f"\\nTurn 2: 'Is staging working?'")
print(f"  Tools: {s1_turn2['tools_called']}")
print(f"  Expected: ['check_status']")
print(f"  Bug if: 'find_owner' was called instead")

langfuse.flush()
print(f"\\nSession ID: {scenario1_session}")
print("Open Langfuse and examine the Turn 2 trace.")""")

# Cell 47 - Task 3 Starter Code
add_code("""# =============================================================================
# TASK 3: Write a Context Bleed Detector
# =============================================================================
# Write code that analyzes a trace and detects potential context bleed.
#
# TIME: ~8 minutes
# =============================================================================

def detect_context_bleed(query: str, tools_called: list, history_length: int) -> dict:
    \"\"\"
    Detect if context bleed might have occurred.

    Args:
        query: The user's query
        tools_called: List of tools that were called
        history_length: Number of previous turns in context

    Returns:
        dict with 'likely_bleed' (bool) and 'reason' (str)
    \"\"\"
    # ─────────────────────────────────────────────────────────────────────────
    # YOUR CODE HERE
    # ─────────────────────────────────────────────────────────────────────────

    # Hint: Check if the query suggests a different tool than what was called
    # For example:
    # - Query contains "status", "working", "healthy" → expect check_status
    # - Query contains "who owns", "contact", "help with" → expect find_owner
    # - Query contains "how to", "documentation", "guide" → expect search_docs

    # If history_length > 0 AND the expected tool doesn't match called tool,
    # that's a potential context bleed.

    likely_bleed = False  # YOUR CODE: Set this based on analysis
    reason = ""  # YOUR CODE: Explain why you think there's bleed (or not)

    # ─────────────────────────────────────────────────────────────────────────
    # END YOUR CODE
    # ─────────────────────────────────────────────────────────────────────────

    return {
        "likely_bleed": likely_bleed,
        "reason": reason
    }


# Test your detector
test_result = detect_context_bleed(
    query="Is the staging environment working?",
    tools_called=["find_owner"],
    history_length=2
)
print(f"Bleed detected: {test_result['likely_bleed']}")
print(f"Reason: {test_result['reason']}")""")

# Cell 48 - Task 3 Solution
add_code("""# =============================================================================
# SOLUTION: Task 3 - Context Bleed Detector
# =============================================================================

def detect_context_bleed_solution(query: str, tools_called: list, history_length: int) -> dict:
    \"\"\"Detect potential context bleed.\"\"\"

    query_lower = query.lower()

    # Determine expected tool based on query keywords
    expected_tool = None

    # Status-related keywords
    status_keywords = ["status", "working", "healthy", "up", "down", "degraded", "running"]
    if any(kw in query_lower for kw in status_keywords):
        expected_tool = "check_status"

    # Owner-related keywords
    owner_keywords = ["who owns", "who can help", "contact", "responsible", "team for", "cancel", "escalate"]
    if any(kw in query_lower for kw in owner_keywords):
        expected_tool = "find_owner"

    # Doc-related keywords
    doc_keywords = ["how to", "how do", "documentation", "guide", "tutorial", "example", "authenticate"]
    if any(kw in query_lower for kw in doc_keywords):
        expected_tool = "search_docs"

    # Check for bleed
    if expected_tool and history_length > 0:
        if expected_tool not in tools_called:
            return {
                "likely_bleed": True,
                "reason": f"Query suggests '{expected_tool}' but got {tools_called}. History length {history_length} may have influenced tool selection."
            }

    return {
        "likely_bleed": False,
        "reason": f"Tool selection appears appropriate for query. Expected: {expected_tool}, Got: {tools_called}"
    }


# Test solution
result = detect_context_bleed_solution(
    query="Is the staging environment working?",
    tools_called=["find_owner"],
    history_length=2
)
print(f"Solution - Bleed detected: {result['likely_bleed']}")
print(f"Solution - Reason: {result['reason']}")""")

# Cell 49 - Scenario 2 Header
add_markdown("""## Scenario 2: Retrieval Failure (Retrieval Layer)

**The Bug:** User asks about a topic with no matching documentation.

**Layer:** Retrieval Layer

**Your tasks:**
1. Run a query about something NOT in our docs
2. Examine the retrieval results in Langfuse
3. Write code to detect low-quality retrieval""")

# Cell 50 - Scenario 2 Code
add_code("""# =============================================================================
# SCENARIO 2: Retrieval Failure
# =============================================================================
# Query about something not in our documentation.

scenario2_session = f"scenario2-{uuid.uuid4().hex[:6]}"

print("=" * 60)
print("SCENARIO 2: Retrieval Failure")
print("=" * 60)

# Query about Kubernetes (not in our docs!)
s2_result = devhub_traced.query(
    "How do I deploy a Kubernetes pod with our auth service?",
    session_id=scenario2_session
)

print(f"Query: 'How do I deploy a Kubernetes pod with our auth service?'")
print(f"Tools called: {s2_result['tools_called']}")
print(f"\\nResponse preview: {s2_result['response'][:300]}...")

langfuse.flush()
print(f"\\nSession ID: {scenario2_session}")
print("Check the 'tool.search_docs' span - look at the retrieval results.")
print("Are any documents actually relevant to Kubernetes?")""")

# Cell 51 - Task 4 Starter Code
add_code("""# =============================================================================
# TASK 4: Write a Retrieval Quality Checker
# =============================================================================
# Check if retrieval results are actually relevant to the query.
#
# TIME: ~8 minutes
# =============================================================================

def check_retrieval_quality(query: str, retrieved_docs: list, distances: list) -> dict:
    \"\"\"
    Check if retrieved documents are relevant to the query.

    Args:
        query: The user's search query
        retrieved_docs: List of document contents
        distances: List of similarity distances (lower = better)

    Returns:
        dict with 'quality' (str: good/fair/poor) and 'issues' (list)
    \"\"\"
    # ─────────────────────────────────────────────────────────────────────────
    # YOUR CODE HERE
    # ─────────────────────────────────────────────────────────────────────────

    # Hint: Check these things:
    # 1. Are there any results at all?
    # 2. Are the distances low enough? (< 0.5 is typically good)
    # 3. Do the documents contain keywords from the query?

    quality = "unknown"  # YOUR CODE: Set to "good", "fair", or "poor"
    issues = []  # YOUR CODE: Add strings describing any issues found

    # ─────────────────────────────────────────────────────────────────────────
    # END YOUR CODE
    # ─────────────────────────────────────────────────────────────────────────

    return {
        "quality": quality,
        "issues": issues
    }


# Test with scenario 2 data (if available from tool results)
if s2_result.get('tool_results'):
    for tr in s2_result['tool_results']:
        if tr['tool'] == 'search_docs' and tr['result'].get('success'):
            data = tr['result']['data']
            check = check_retrieval_quality(
                query="How do I deploy a Kubernetes pod",
                retrieved_docs=data.get('documents', []),
                distances=data.get('distances', [])
            )
            print(f"Retrieval quality: {check['quality']}")
            print(f"Issues: {check['issues']}")""")

# Cell 52 - Task 4 Solution
add_code("""# =============================================================================
# SOLUTION: Task 4 - Retrieval Quality Checker
# =============================================================================

def check_retrieval_quality_solution(query: str, retrieved_docs: list, distances: list) -> dict:
    \"\"\"Check retrieval quality.\"\"\"

    issues = []
    query_words = set(query.lower().split())

    # Check 1: Any results?
    if not retrieved_docs:
        return {"quality": "poor", "issues": ["No documents retrieved"]}

    # Check 2: Distance scores
    if distances:
        avg_distance = sum(distances) / len(distances)
        if avg_distance > 0.7:
            issues.append(f"High average distance: {avg_distance:.2f} (threshold: 0.7)")
        if distances[0] > 0.5:
            issues.append(f"Best match distance {distances[0]:.2f} > 0.5 threshold")

    # Check 3: Keyword overlap
    total_overlap = 0
    for doc in retrieved_docs:
        doc_words = set(doc.lower().split())
        overlap = len(query_words & doc_words)
        total_overlap += overlap

    if total_overlap < len(query_words):
        issues.append(f"Low keyword overlap: {total_overlap} matches for {len(query_words)} query words")

    # Determine quality
    if len(issues) == 0:
        quality = "good"
    elif len(issues) == 1:
        quality = "fair"
    else:
        quality = "poor"

    return {"quality": quality, "issues": issues}


# Test solution
print("Testing retrieval quality checker...")
test_check = check_retrieval_quality_solution(
    query="Kubernetes deployment pod auth",
    retrieved_docs=["OAuth authentication with client credentials...", "Error handling standards..."],
    distances=[0.8, 0.9]
)
print(f"Quality: {test_check['quality']}")
print(f"Issues: {test_check['issues']}")""")

# Cell 53 - Scenario 3 Header
add_markdown("""## Scenario 3: Hallucination (Generation Layer)

**The Bug:** Model invents details not present in retrieved documents.

**Layer:** Generation Layer

**Your tasks:**
1. Run a query where the model might hallucinate
2. Compare the response to the retrieved context
3. Write code to detect potential hallucinations""")

# Cell 54 - Scenario 3 Code
add_code("""# =============================================================================
# SCENARIO 3: Hallucination Detection
# =============================================================================
# Ask about something where the model might make up details.

scenario3_session = f"scenario3-{uuid.uuid4().hex[:6]}"

print("=" * 60)
print("SCENARIO 3: Hallucination")
print("=" * 60)

# Query that might trigger hallucination
s3_result = devhub_traced.query(
    "What's the exact rate limit for the Premium Plus tier on the Payments API?",
    session_id=scenario3_session
)

print(f"Query: 'What's the exact rate limit for the Premium Plus tier?'")
print(f"Tools called: {s3_result['tools_called']}")
print(f"\\nResponse:\\n{s3_result['response']}")

langfuse.flush()
print(f"\\nSession ID: {scenario3_session}")
print("\\nCheck: Does our documentation mention 'Premium Plus tier'?")
print("If the model gave a specific number, did it come from the docs or was it invented?")""")

# Cell 55 - Task 5 Starter Code
add_code("""# =============================================================================
# TASK 5: Write a Simple Hallucination Detector
# =============================================================================
# Check if the response contains claims not in the source documents.
#
# TIME: ~10 minutes
# =============================================================================
import re

def detect_hallucination(response: str, source_docs: list) -> dict:
    \"\"\"
    Detect if the response contains information not in source documents.

    Args:
        response: The model's response
        source_docs: List of source document contents

    Returns:
        dict with 'likely_hallucination' (bool), 'suspicious_claims' (list)
    \"\"\"
    # ─────────────────────────────────────────────────────────────────────────
    # YOUR CODE HERE
    # ─────────────────────────────────────────────────────────────────────────

    # Hint: Look for specific patterns that indicate potential hallucination:
    # 1. Specific numbers (rates, percentages, limits) not in sources
    # 2. Product names or tier names not mentioned in sources
    # 3. Dates or version numbers not in sources

    # Combine all source docs into one text for searching
    # all_sources = " ".join(source_docs).lower()

    # Extract specific claims from response (numbers, proper nouns, etc.)
    # Check if they appear in sources

    likely_hallucination = False  # YOUR CODE
    suspicious_claims = []  # YOUR CODE: List of claims that seem made up

    # ─────────────────────────────────────────────────────────────────────────
    # END YOUR CODE
    # ─────────────────────────────────────────────────────────────────────────

    return {
        "likely_hallucination": likely_hallucination,
        "suspicious_claims": suspicious_claims
    }


# Test with scenario 3
if s3_result.get('tool_results'):
    for tr in s3_result['tool_results']:
        if tr['tool'] == 'search_docs' and tr['result'].get('success'):
            source_docs = tr['result']['data'].get('documents', [])
            result = detect_hallucination(s3_result['response'], source_docs)
            print(f"Likely hallucination: {result['likely_hallucination']}")
            print(f"Suspicious claims: {result['suspicious_claims']}")""")

# Cell 56 - Task 5 Solution
add_code("""# =============================================================================
# SOLUTION: Task 5 - Hallucination Detector
# =============================================================================
import re

def detect_hallucination_solution(response: str, source_docs: list) -> dict:
    \"\"\"Detect potential hallucinations.\"\"\"

    suspicious_claims = []
    all_sources = " ".join(source_docs).lower()

    # Extract numbers from response
    numbers_in_response = re.findall(r'\\b\\d+(?:,\\d{3})*(?:\\.\\d+)?\\b', response)

    # Check if numbers appear in sources
    for num in numbers_in_response:
        if num not in all_sources:
            suspicious_claims.append(f"Number '{num}' not found in source documents")

    # Check for tier/plan names not in sources
    tier_patterns = ["premium plus", "enterprise", "professional", "basic tier", "standard tier"]
    response_lower = response.lower()
    for tier in tier_patterns:
        if tier in response_lower and tier not in all_sources:
            suspicious_claims.append(f"Tier '{tier}' mentioned but not in sources")

    # Check for specific endpoint paths
    endpoints = re.findall(r'/[a-z]+/v\\d+/[a-z]+', response.lower())
    for endpoint in endpoints:
        if endpoint not in all_sources:
            suspicious_claims.append(f"Endpoint '{endpoint}' not found in sources")

    likely_hallucination = len(suspicious_claims) > 0

    return {
        "likely_hallucination": likely_hallucination,
        "suspicious_claims": suspicious_claims
    }


# Test solution
test_response = "The Premium Plus tier has a rate limit of 5000 requests per minute."
test_sources = ["Default rate limits: 100 req/min for standard tier, 1000 req/min for premium."]
result = detect_hallucination_solution(test_response, test_sources)
print(f"Solution - Likely hallucination: {result['likely_hallucination']}")
print(f"Solution - Suspicious claims: {result['suspicious_claims']}")""")

# Cell 57 - Scenario 4 Header
add_markdown("""## Scenario 4: Parameter Error (Validation Layer)

**The Bug:** Model calls the right tool with wrong parameters.

**Layer:** Validation Layer

**Your tasks:**
1. Run a query that results in invalid parameters
2. Check the tool call arguments in Langfuse
3. Write code to validate tool parameters""")

# Cell 58 - Scenario 4 Code
add_code("""# =============================================================================
# SCENARIO 4: Parameter Error
# =============================================================================
# Query that might result in wrong parameters.

scenario4_session = f"scenario4-{uuid.uuid4().hex[:6]}"

print("=" * 60)
print("SCENARIO 4: Parameter Error")
print("=" * 60)

# Query with ambiguous service name
s4_result = devhub_traced.query(
    "Check the status of the payment-processing-v2 service",
    session_id=scenario4_session
)

print(f"Query: 'Check status of payment-processing-v2'")
print(f"Tools called: {s4_result['tools_called']}")

# Check what parameter was passed
if s4_result.get('tool_results'):
    for tr in s4_result['tool_results']:
        if tr['tool'] == 'check_status':
            print(f"Parameter passed: {tr['args']}")
            print(f"Result: {tr['result']}")

langfuse.flush()
print(f"\\nSession ID: {scenario4_session}")
print("\\nCheck: Does 'payment-processing-v2' match any valid service?")
print("Valid services: payments-api, auth-service, staging, vector-search, api-gateway")""")

# Cell 59 - Task 6 Starter Code
add_code("""# =============================================================================
# TASK 6: Write a Parameter Validator
# =============================================================================
# Validate that tool parameters match known valid values.
#
# TIME: ~8 minutes
# =============================================================================

# Known valid services (from our STATUS_DATA)
VALID_SERVICES = ["payments-api", "auth-service", "staging", "vector-search", "api-gateway"]

def validate_tool_params(tool_name: str, args: dict) -> dict:
    \"\"\"
    Validate tool parameters against known valid values.

    Args:
        tool_name: Name of the tool called
        args: Arguments passed to the tool

    Returns:
        dict with 'valid' (bool), 'errors' (list), 'suggestions' (list)
    \"\"\"
    # ─────────────────────────────────────────────────────────────────────────
    # YOUR CODE HERE
    # ─────────────────────────────────────────────────────────────────────────

    # Hint: For check_status tool:
    # 1. Get the service_name parameter
    # 2. Check if it's in VALID_SERVICES
    # 3. If not, find the closest match (fuzzy matching)

    valid = True  # YOUR CODE
    errors = []  # YOUR CODE
    suggestions = []  # YOUR CODE: Suggest valid alternatives

    # ─────────────────────────────────────────────────────────────────────────
    # END YOUR CODE
    # ─────────────────────────────────────────────────────────────────────────

    return {
        "valid": valid,
        "errors": errors,
        "suggestions": suggestions
    }


# Test
result = validate_tool_params("check_status", {"service_name": "payment-processing-v2"})
print(f"Valid: {result['valid']}")
print(f"Errors: {result['errors']}")
print(f"Suggestions: {result['suggestions']}")""")

# Cell 60 - Task 6 Solution
add_code("""# =============================================================================
# SOLUTION: Task 6 - Parameter Validator
# =============================================================================

def validate_tool_params_solution(tool_name: str, args: dict) -> dict:
    \"\"\"Validate tool parameters.\"\"\"

    errors = []
    suggestions = []

    if tool_name == "check_status":
        service_name = args.get("service_name", "")

        # Check exact match
        if service_name.lower() in [s.lower() for s in VALID_SERVICES]:
            return {"valid": True, "errors": [], "suggestions": []}

        # Check partial match
        errors.append(f"Unknown service: '{service_name}'")

        # Find similar services
        service_lower = service_name.lower()
        for valid_service in VALID_SERVICES:
            # Check if any part matches
            if any(part in valid_service for part in service_lower.split("-")):
                suggestions.append(valid_service)

        if not suggestions:
            suggestions = VALID_SERVICES[:3]  # Show first 3 as examples

        return {"valid": False, "errors": errors, "suggestions": suggestions}

    elif tool_name == "find_owner":
        service_name = args.get("service_name", "")
        if not service_name:
            return {"valid": False, "errors": ["Missing service_name"], "suggestions": []}
        return {"valid": True, "errors": [], "suggestions": []}

    elif tool_name == "search_docs":
        query = args.get("query", "")
        if not query or len(query) < 3:
            return {"valid": False, "errors": ["Query too short"], "suggestions": []}
        return {"valid": True, "errors": [], "suggestions": []}

    return {"valid": True, "errors": [], "suggestions": []}


# Test solution
result = validate_tool_params_solution("check_status", {"service_name": "payment-processing-v2"})
print(f"Solution - Valid: {result['valid']}")
print(f"Solution - Errors: {result['errors']}")
print(f"Solution - Suggestions: {result['suggestions']}")""")

# Cell 61 - Lab 2 Complete
add_markdown("""## Lab 2 Complete!

You've debugged 4 different LLM failure scenarios:

| Scenario | Layer | What You Built |
|----------|-------|----------------|
| Context Bleed | Prompt | `detect_context_bleed()` function |
| Retrieval Failure | Retrieval | `check_retrieval_quality()` function |
| Hallucination | Generation | `detect_hallucination()` function |
| Parameter Error | Validation | `validate_tool_params()` function |

**Key skill:** Using traces to identify the layer, then writing code to detect similar issues.

**Next:** Lab 3 - Convert one of these failures into a regression test.""")

# =============================================================================
# SECTION 6: LAB 3 - FAILURE TO REGRESSION TEST (Cells 62-70)
# =============================================================================

# Cell 62 - Lab Header
add_markdown("""---

# Lab 3: Convert Failures to Regression Tests

**Duration:** ~25 minutes

![Failure to Test Pipeline](https://raw.githubusercontent.com/axel-sirota/salesforce-ai-workshops/main/exercises/session_04/charts/06_failure_to_test_pipeline.svg)

**Goal:** Ensure the hallucination bug (Scenario 3) never happens again.

**The Pipeline:**
1. **Find** failing trace in Langfuse
2. **Analyze** with 5-Layer Framework
3. **Export** trace data (query, response, context)
4. **Test** with DeepEval FaithfulnessMetric
5. **CI/CD** - Add to regression test suite""")

# Cell 63 - FaithfulnessMetric Intro
add_markdown("""## DeepEval FaithfulnessMetric

**What it does:** Checks if a response is faithful to (grounded in) the provided context.

**How it works:**
1. Extracts claims from the response
2. Checks if each claim is supported by the context
3. Returns a score (0-1) and pass/fail based on threshold

**Pattern:**
```python
from deepeval.test_case import LLMTestCase
from deepeval.metrics import FaithfulnessMetric

# Create test case
test_case = LLMTestCase(
    input="What's the rate limit?",
    actual_output="The rate limit is 100 requests per minute.",
    retrieval_context=["Rate limits: 100 req/min standard, 1000 req/min premium."]
)

# Run faithfulness check
metric = FaithfulnessMetric(threshold=0.7)
metric.measure(test_case)
print(f"Score: {metric.score}, Passed: {metric.is_successful()}")
```""")

# Cell 64 - Task 7 Starter Code
add_code("""# =============================================================================
# TASK 7: Extract Test Case from Scenario 3
# =============================================================================
# Create a test case from the hallucination scenario.
#
# TIME: ~5 minutes
# =============================================================================

from deepeval.test_case import LLMTestCase
from deepeval.metrics import FaithfulnessMetric

# We'll use the scenario 3 data
test_query = "What's the exact rate limit for the Premium Plus tier on the Payments API?"

# Get the response and context from scenario 3
test_response = s3_result['response']

# Extract retrieval context from tool results
retrieval_context = []
for tr in s3_result.get('tool_results', []):
    if tr['tool'] == 'search_docs' and tr['result'].get('success'):
        retrieval_context = tr['result']['data'].get('documents', [])
        break

print("Extracted from Scenario 3 trace:")
print(f"  Query: {test_query[:50]}...")
print(f"  Response: {test_response[:100]}...")
print(f"  Context docs: {len(retrieval_context)}")

# ─────────────────────────────────────────────────────────────────────────────
# YOUR CODE: Create the LLMTestCase
# ─────────────────────────────────────────────────────────────────────────────

# hallucination_test_case = LLMTestCase(
#     input=...,
#     actual_output=...,
#     retrieval_context=...
# )

hallucination_test_case = None  # YOUR CODE HERE

# ─────────────────────────────────────────────────────────────────────────────
# END YOUR CODE
# ─────────────────────────────────────────────────────────────────────────────

if hallucination_test_case:
    print("\\nTest case created successfully!")""")

# Cell 65 - Task 7 Solution
add_code("""# =============================================================================
# SOLUTION: Task 7 - Create Test Case
# =============================================================================

hallucination_test_case = LLMTestCase(
    input=test_query,
    actual_output=test_response,
    retrieval_context=retrieval_context
)

print("Solution - Test case created:")
print(f"  Input: {hallucination_test_case.input[:50]}...")
print(f"  Output: {hallucination_test_case.actual_output[:50]}...")
print(f"  Context items: {len(hallucination_test_case.retrieval_context)}")""")

# Cell 66 - Task 8 Starter Code
add_code("""# =============================================================================
# TASK 8: Run FaithfulnessMetric on the Test Case
# =============================================================================
# Check if the response is faithful to the retrieval context.
#
# TIME: ~5 minutes
# =============================================================================

# ─────────────────────────────────────────────────────────────────────────────
# YOUR CODE: Create and run the FaithfulnessMetric
# ─────────────────────────────────────────────────────────────────────────────

# Hint:
# 1. Create FaithfulnessMetric with threshold=0.7
# 2. Call metric.measure(test_case)
# 3. Check metric.score and metric.is_successful()

# metric = FaithfulnessMetric(threshold=0.7, include_reason=True)
# metric.measure(hallucination_test_case)

# print(f"Score: {metric.score}")
# print(f"Passed: {metric.is_successful()}")
# print(f"Reason: {metric.reason}")

print("YOUR CODE: Run the FaithfulnessMetric")

# ─────────────────────────────────────────────────────────────────────────────
# END YOUR CODE
# ─────────────────────────────────────────────────────────────────────────────""")

# Cell 67 - Task 8 Solution
add_code("""# =============================================================================
# SOLUTION: Task 8 - Run FaithfulnessMetric
# =============================================================================

print("Running FaithfulnessMetric (this may take a few seconds)...")

faithfulness_metric = FaithfulnessMetric(threshold=0.7, include_reason=True)

try:
    faithfulness_metric.measure(hallucination_test_case)

    print(f"\\nFaithfulness Score: {faithfulness_metric.score:.2f}")
    print(f"Passed (>= 0.7): {faithfulness_metric.is_successful()}")
    print(f"\\nReason: {faithfulness_metric.reason}")

    if not faithfulness_metric.is_successful():
        print("\\n HALLUCINATION DETECTED!")
        print("The response contains claims not supported by the retrieval context.")
except Exception as e:
    print(f"Error running metric: {e}")
    print("(This may happen if you don't have OpenAI credits)")""")

# Cell 68 - Task 9 Starter Code
add_code("""# =============================================================================
# TASK 9: Create a Reusable Regression Test Function
# =============================================================================
# This function can be added to your CI/CD pipeline.
#
# TIME: ~8 minutes
# =============================================================================

def test_no_hallucinated_rate_limits():
    \"\"\"
    Regression test: DevHub should not invent rate limits.

    Bug: HALL-001
    Root cause: Model extrapolated tier names not in documentation
    Fix: Added grounding instructions to system prompt

    This test ensures the fix hasn't regressed.
    \"\"\"
    # ─────────────────────────────────────────────────────────────────────────
    # YOUR CODE HERE
    # ─────────────────────────────────────────────────────────────────────────

    # 1. Run the query that caused the original bug
    # result = devhub_traced.query("What's the rate limit for Premium Plus tier?")

    # 2. Extract response and retrieval context
    # response = result['response']
    # context = [extract from tool_results]

    # 3. Create test case
    # test_case = LLMTestCase(input=..., actual_output=..., retrieval_context=...)

    # 4. Run faithfulness check
    # metric = FaithfulnessMetric(threshold=0.7)
    # metric.measure(test_case)

    # 5. Assert the test passes
    # assert metric.is_successful(), f"Hallucination detected: {metric.reason}"

    print("YOUR CODE: Implement the regression test function")
    pass

    # ─────────────────────────────────────────────────────────────────────────
    # END YOUR CODE
    # ─────────────────────────────────────────────────────────────────────────


# Run the test
print("Testing regression test function...")
test_no_hallucinated_rate_limits()""")

# Cell 69 - Task 9 Solution
add_code("""# =============================================================================
# SOLUTION: Task 9 - Regression Test Function
# =============================================================================

def test_no_hallucinated_rate_limits_solution():
    \"\"\"
    Regression test: DevHub should not invent rate limits.

    Bug: HALL-001 (detected in Scenario 3)
    Root cause: Model extrapolated tier names not in documentation
    \"\"\"
    # 1. Run the problematic query
    result = devhub_traced.query(
        "What are the rate limits for different tiers?",
        session_id=f"regression-{uuid.uuid4().hex[:6]}"
    )

    # 2. Extract data
    response = result['response']
    context = []
    for tr in result.get('tool_results', []):
        if tr['tool'] == 'search_docs' and tr['result'].get('success'):
            context = tr['result']['data'].get('documents', [])
            break

    # 3. Create test case
    test_case = LLMTestCase(
        input="What are the rate limits for different tiers?",
        actual_output=response,
        retrieval_context=context
    )

    # 4. Run faithfulness check
    metric = FaithfulnessMetric(threshold=0.7, include_reason=True)
    metric.measure(test_case)

    # 5. Report results
    print(f"Faithfulness score: {metric.score:.2f}")
    print(f"Test passed: {metric.is_successful()}")

    if not metric.is_successful():
        print(f"REGRESSION DETECTED: {metric.reason}")
        # In CI/CD, this would be: assert metric.is_successful()

    langfuse.flush()
    return metric.is_successful()


# Run solution
print("Running regression test solution...")
try:
    passed = test_no_hallucinated_rate_limits_solution()
    print(f"\\nFinal result: {'PASS' if passed else 'FAIL'}")
except Exception as e:
    print(f"Test error: {e}")""")

# Cell 70 - Lab 3 Complete
add_markdown("""## Lab 3 Complete!

You've built a complete failure-to-test pipeline:

**What you created:**
1. **Test case extraction** from Langfuse traces
2. **FaithfulnessMetric** evaluation
3. **Regression test function** for CI/CD

**The pattern:**
```python
def test_regression_bug_XXX():
    # 1. Run the query that caused the bug
    result = devhub.query("...")

    # 2. Create test case with retrieval context
    test_case = LLMTestCase(input=..., actual_output=..., retrieval_context=...)

    # 3. Run appropriate metric
    metric = FaithfulnessMetric(threshold=0.7)
    metric.measure(test_case)

    # 4. Assert
    assert metric.is_successful(), f"Regression: {metric.reason}"
```

**Add to CI/CD:**
- Run these tests on every PR
- If they fail, the bug has returned
- Never fix the same bug twice!""")

# =============================================================================
# SECTION 7: WRAP-UP (Cells 71-76)
# =============================================================================

# Cell 71 - Before and After
add_markdown("""---

# Wrap-Up: Before and After

![Before After](https://raw.githubusercontent.com/axel-sirota/salesforce-ai-workshops/main/exercises/session_04/charts/07_before_after_debugging.svg)""")

# Cell 72 - Key Takeaways
add_markdown("""## Key Takeaways

### 1. LLM Bugs Are Different
- Traditional debugging shows WHAT happened
- LLM debugging shows WHY the model decided
- Different tools for different bug types

### 2. The 5-Layer Framework
| Layer | Debug Focus |
|-------|-------------|
| Prompt | History, tool descriptions, system prompt |
| Retrieval | Similarity scores, document relevance |
| Generation | Compare output to context |
| Validation | Parameter values, schema compliance |
| Latency | Span timings, token counts |

### 3. The Debug Workflow
1. **Find** the trace
2. **Identify** the layer
3. **Analyze** inputs and outputs
4. **Fix** the root cause
5. **Test** to prevent regression

### 4. Tools You Learned
- **Langfuse:** LLM observability (traces, spans, generations)
- **DeepEval:** Evaluation metrics (FaithfulnessMetric)
- **Your detectors:** Context bleed, retrieval quality, hallucination, parameter validation""")

# Cell 73 - Take-Home Challenge
add_markdown("""## Take-Home Challenge

**Challenge:** Build a comprehensive debug toolkit for DevHub.

**Requirements:**

1. **Create a DebugToolkit class** that combines all 4 detectors:
   ```python
   class DebugToolkit:
       def analyze_trace(self, trace_data: dict) -> dict:
           # Run all detectors
           # Return comprehensive analysis
   ```

2. **Add automatic layer identification:**
   - Based on symptoms, suggest which layer to investigate

3. **Create 3 more regression tests** for other failure scenarios:
   - Context bleed regression test
   - Retrieval failure regression test
   - Parameter error regression test

4. **Bonus:** Create a Langfuse dashboard that shows:
   - Traces with potential issues (filtered by your detectors)
   - Failure rate by layer
   - Regression test results over time""")

# Cell 74 - What's Next
add_markdown("""## What's Next

### Session 5: Guardrails & Safety
- Input/output validation
- Content filtering
- Bias detection
- Rate limiting for AI

### Session 6: Production Deployment
- Scaling considerations
- Cost optimization
- Monitoring dashboards
- Incident response

### Resources
- **Langfuse Docs:** https://langfuse.com/docs
- **DeepEval Docs:** https://docs.confident-ai.com/
- **OpenTelemetry + Langfuse:** https://langfuse.com/docs/integrations/opentelemetry""")

# Cell 75 - Questions
add_markdown("""## Questions?

**Feedback:** [Workshop Feedback Form]

**Support:**
- Workshop Slack: #ai-workshop-support
- Langfuse Discord: https://discord.gg/langfuse

**Code Repository:** [GitHub Link]

---

**Thank you for attending Session 4!**

You now have the skills to debug LLM applications like a pro.""")

# Cell 76 - Final Cleanup
add_code("""# =============================================================================
# CLEANUP: Flush all traces
# =============================================================================

langfuse = get_client()
langfuse.flush()

print("All traces flushed to Langfuse.")
print(f"\\nYour traces are available at: {LANGFUSE_HOST}")
print(f"Filter by user_id: {STUDENT_NAME}")
print("\\nSession 4 Complete!")""")

# =============================================================================
# Write final notebook
# =============================================================================
output_path = "/Users/axelsirota/repos/salesforce-ai-workshops/exercises/session_04/session_04_debugging.ipynb"

# Save final version
with open(output_path, 'w') as f:
    json.dump(notebook, f, indent=1)

print(f"Notebook complete: {len(notebook['cells'])} cells written")
print(f"Output: {output_path}")
