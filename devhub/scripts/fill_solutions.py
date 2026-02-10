#!/usr/bin/env python3
"""
Fill Solutions in Session 1 Notebook

Replaces "PUT YOUR CODE HERE" placeholders with actual solutions.
"""

import json
from pathlib import Path

NOTEBOOK_PATH = Path("solutions/session_01/session_01_observability_solutions.ipynb")

# Solutions for each task
SOLUTIONS = {
    # Task 1: Initialize OpenTelemetry
    "TASK 1: Initialize OpenTelemetry": '''# =============================================================================
# SOLUTION: Task 1 - Initialize OpenTelemetry
# =============================================================================

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

# Step 1: Create resource with service.name
resource = Resource.create({
    "service.name": f"devhub-{STUDENT_NAME}",
    "service.version": "1.0.0",
    "deployment.environment": "workshop"
})

# Step 2: Create TracerProvider with the resource
provider = TracerProvider(resource=resource)

# Step 3: Create OTLPSpanExporter pointing to JAEGER_ENDPOINT
exporter = OTLPSpanExporter(
    endpoint=JAEGER_ENDPOINT,
    insecure=True  # Use insecure for HTTP (non-TLS)
)

# Step 4: Add BatchSpanProcessor to the provider
provider.add_span_processor(BatchSpanProcessor(exporter))

# Step 5: Set as global tracer provider
trace.set_tracer_provider(provider)

# Step 6: Get a tracer named "devhub"
tracer = trace.get_tracer("devhub")

# Verification
print("OpenTelemetry initialized!")
print(f"   Service name: devhub-{STUDENT_NAME}")
print(f"   Exporting to: {JAEGER_ENDPOINT}")
print("\\nYour traces will now appear in Jaeger!")''',

    # Task 2: Instrument VectorDB.search()
    "TASK 2: Instrument VectorDB": '''# SOLUTION: Task 2 - Instrument VectorDB.search()

class InstrumentedVectorDB(VectorDB):
    """VectorDB with OpenTelemetry tracing."""

    def search(self, query: str, top_k: int = 3) -> dict:
        """Search with tracing instrumentation."""
        with tracer.start_as_current_span("vector_db.search") as span:
            # Set input attributes
            span.set_attribute("db.system", "chromadb")
            span.set_attribute("db.operation", "search")
            span.set_attribute("db.query", query)
            span.set_attribute("db.top_k", top_k)

            # Call original method
            result = super().search(query, top_k)

            # Set output attributes
            span.set_attribute("db.result_count", len(result.get("documents", [])))
            span.set_attribute("db.latency_ms", result.get("latency_ms", 0))

            # Record similarity scores
            distances = result.get("distances", [])
            if distances:
                # Convert distance to similarity (1 - distance for cosine)
                similarities = [1 - d for d in distances]
                span.set_attribute("db.top_similarity", max(similarities) if similarities else 0)
                span.set_attribute("db.similarities", str(similarities[:3]))

            return result

# Test the instrumented VectorDB
print("Testing InstrumentedVectorDB...")
instrumented_vector_db = InstrumentedVectorDB()
result = instrumented_vector_db.search("billing API authentication")
print(f"Found {len(result['documents'])} documents")
print(f"Latency: {result['latency_ms']}ms")
print("Check Jaeger for the vector_db.search span!")''',

    # Task 3: Instrument TeamDB.find_owner()
    "TASK 3: Instrument TeamDB": '''# SOLUTION: Task 3 - Instrument TeamDB.find_owner()

class InstrumentedTeamDB(TeamDB):
    """TeamDB with OpenTelemetry tracing."""

    def find_owner(self, service_name: str) -> dict:
        """Find owner with tracing instrumentation."""
        with tracer.start_as_current_span("team_db.find_owner") as span:
            # Set input attributes
            span.set_attribute("db.system", "json")
            span.set_attribute("db.operation", "find_owner")
            span.set_attribute("service.name", service_name)

            # Call original method
            result = super().find_owner(service_name)

            # Set output attributes
            span.set_attribute("owner.found", result.get("found", False))
            span.set_attribute("db.latency_ms", result.get("latency_ms", 0))

            if result.get("found"):
                span.set_attribute("owner.name", result.get("owner", {}).get("name", "unknown"))
                span.set_attribute("owner.email", result.get("owner", {}).get("email", "unknown"))
                span.set_attribute("owner.active", result.get("owner", {}).get("active", False))

            return result

# Test the instrumented TeamDB
print("Testing InstrumentedTeamDB...")
instrumented_team_db = InstrumentedTeamDB()
result = instrumented_team_db.find_owner("billing-service")
print(f"Found: {result['found']}")
if result['found']:
    print(f"Owner: {result['owner']['name']}")
print("Check Jaeger for the team_db.find_owner span!")''',

    # Task 4: Instrument StatusAPI.check_status()
    "TASK 4: Instrument StatusAPI": '''# SOLUTION: Task 4 - Instrument StatusAPI.check_status()

class InstrumentedStatusAPI(StatusAPI):
    """StatusAPI with OpenTelemetry tracing."""

    def check_status(self, service_name: str) -> dict:
        """Check status with tracing instrumentation."""
        with tracer.start_as_current_span("status_api.check_status") as span:
            # Set input attributes
            span.set_attribute("api.system", "status")
            span.set_attribute("api.operation", "check_status")
            span.set_attribute("service.name", service_name)

            # Call original method
            result = super().check_status(service_name)

            # Set output attributes
            span.set_attribute("status.found", result.get("found", False))
            span.set_attribute("api.latency_ms", result.get("latency_ms", 0))

            if result.get("found"):
                span.set_attribute("service.status", result.get("status", "unknown"))
                span.set_attribute("service.healthy", result.get("status") == "healthy")

                # Record incident if present
                if result.get("incident"):
                    span.set_attribute("incident.active", True)
                    span.set_attribute("incident.description", result.get("incident", ""))

            return result

# Test the instrumented StatusAPI
print("Testing InstrumentedStatusAPI...")
instrumented_status_api = InstrumentedStatusAPI()
result = instrumented_status_api.check_status("staging")
print(f"Found: {result['found']}")
if result['found']:
    print(f"Status: {result['status']}")
print("Check Jaeger for the status_api.check_status span!")''',

    # Task 5: Instrument DevHubAgent.query()
    "TASK 5: Instrument DevHubAgent": '''# SOLUTION: Task 5 - Instrument DevHubAgent.query()

class InstrumentedDevHubAgent(DevHubAgent):
    """DevHubAgent with full OpenTelemetry tracing."""

    def __init__(self):
        # Use instrumented versions of all services
        super().__init__()
        self.vector_db = InstrumentedVectorDB()
        self.team_db = InstrumentedTeamDB()
        self.status_api = InstrumentedStatusAPI()

    def query(self, user_query: str) -> str:
        """Process query with full tracing instrumentation."""
        with tracer.start_as_current_span("devhub.query") as span:
            # Set input attributes
            span.set_attribute("devhub.query", user_query)
            span.set_attribute("devhub.query_length", len(user_query))

            # Call original method (which uses instrumented services)
            result = super().query(user_query)

            # Set output attributes
            span.set_attribute("devhub.response_length", len(result))
            span.set_attribute("llm.model", "gpt-4o-mini")

            return result

# Create the fully instrumented agent
print("Creating InstrumentedDevHubAgent...")
instrumented_agent = InstrumentedDevHubAgent()
print("Ready! All components are now instrumented.")
print("\\nTry running queries and check Jaeger for complete traces!")''',

    # Lab 1.1: Explore DevHub (analysis cell)
    "LAB 1.1: Explore DevHub": '''# Lab 1.1: Explore DevHub - Example Queries

# Query 1: Documentation search
print("Query 1: Documentation search")
print("-" * 40)
response = agent.query("How do I authenticate with the Payments API?")
print(response)
print()

# Query 2: Owner lookup
print("Query 2: Owner lookup")
print("-" * 40)
response = agent.query("Who owns the billing service?")
print(response)
print()

# Query 3: Status check
print("Query 3: Status check")
print("-" * 40)
response = agent.query("Is the staging environment working?")
print(response)''',

    # Scenario 1: Analysis
    "SCENARIO 1: Your Analysis": '''# SCENARIO 1: Analysis - The Slow Query

# What I observed in Jaeger:
# 1. The root span (devhub.query) took ~3200ms total
# 2. The vector_db.search span took ~3000ms (the bottleneck!)
# 3. Other spans (team_db, llm) took normal time

# Root cause:
# The VectorDB has a 10% chance of triggering a "slow query"
# that adds 3000ms latency. This is visible in the span attributes:
# - db.latency_ms: 3000+
# - The span duration is much longer than normal (50-200ms)

# How tracing helped:
# - Without tracing: "It's slow sometimes" - no idea why
# - With tracing: Immediately see vector_db.search is the bottleneck
# - Can filter in Jaeger: latency > 2s to find all slow queries

print("Analysis complete!")
print("Root cause: VectorDB slow query (10% rate, 3000ms latency)")
print("Solution: Add caching, optimize query, or add circuit breaker")''',

    # Scenario 2: Analysis
    "SCENARIO 2: Your Analysis": '''# SCENARIO 2: Analysis - The Wrong Owner

# What I observed in Jaeger:
# 1. The team_db.find_owner span shows owner.found: true
# 2. But owner.active: false (the owner is inactive/stale!)
# 3. The owner name is "David Kim" who left the company

# Root cause:
# The TeamDB has a 10% chance of returning "stale data" -
# an inactive owner who no longer works on the service.
# This is visible in span attributes:
# - owner.found: true
# - owner.active: false  <-- This is the problem!
# - owner.name: "David Kim"

# How tracing helped:
# - Without tracing: "Wrong owner sometimes" - can't reproduce
# - With tracing: See owner.active=false in the span
# - Can add alerts when owner.active is false

print("Analysis complete!")
print("Root cause: TeamDB returning inactive owner (10% stale data rate)")
print("Solution: Filter by owner.active=true, or add data validation")''',

    # Scenario 3: Analysis
    "SCENARIO 3: Your Analysis": '''# SCENARIO 3: Analysis - Poor Retrieval Quality

# What I observed in Jaeger:
# 1. The vector_db.search span shows results were returned
# 2. But db.top_similarity is very low (< 0.5)
# 3. The retrieved documents don't match the query well

# Root cause:
# The VectorDB has a 15% chance of returning "low similarity" results -
# the search finds documents but they're not relevant.
# This is visible in span attributes:
# - db.result_count: 3 (found documents)
# - db.top_similarity: 0.3-0.4 (very low!)
# - db.similarities: [0.3, 0.25, 0.2] (all poor matches)

# How tracing helped:
# - Without tracing: "Bad answers sometimes" - can't debug
# - With tracing: See similarity scores in spans
# - Can set threshold alerts: similarity < 0.7 = bad retrieval

print("Analysis complete!")
print("Root cause: VectorDB low similarity results (15% rate)")
print("Solution: Add similarity threshold check, return 'I don't know' for low scores")''',
}


def find_and_replace_cell(cells: list, pattern: str, solution: str) -> bool:
    """Find cell containing pattern and replace its source with solution."""
    for i, cell in enumerate(cells):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        # Check for various placeholder patterns
        has_placeholder = (
            "PUT YOUR CODE HERE" in source or
            "PUT YOUR ANSWER HERE" in source or
            "# Your code here" in source
        )
        if pattern in source and has_placeholder:
            # Replace with solution
            cells[i]["source"] = [solution]
            return True
    return False


def main():
    print(f"Reading notebook: {NOTEBOOK_PATH}")

    with open(NOTEBOOK_PATH) as f:
        notebook = json.load(f)

    cells = notebook["cells"]
    print(f"Found {len(cells)} cells")

    # Replace each solution
    replaced = 0
    for pattern, solution in SOLUTIONS.items():
        if find_and_replace_cell(cells, pattern, solution):
            print(f"  Replaced: {pattern}")
            replaced += 1
        else:
            print(f"  NOT FOUND: {pattern}")

    # Update notebook
    notebook["cells"] = cells

    # Write back
    print(f"\nWriting notebook with {replaced} solutions filled...")
    with open(NOTEBOOK_PATH, "w") as f:
        json.dump(notebook, f, indent=1)

    print("Done!")


if __name__ == "__main__":
    main()
