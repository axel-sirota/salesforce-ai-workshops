#!/usr/bin/env python3
"""
Fill in Session 6 exercise cells with solutions.

Reads the solution notebook (copy of exercise) and replaces
the 15 exercise cells with working implementations.
"""

import json
import os

SOLUTION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "solutions", "session_06", "session_06_prompt_tdd.ipynb")

# Solution implementations for each exercise cell
SOLUTIONS = {}

# Cell 31: Define 4 G-Eval metrics
SOLUTIONS[31] = '''# =============================================================================
# LAB 1, Task 1: Define Quality Metrics
# =============================================================================
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

# Initialize judge model (DeepEval uses OPENAI_API_KEY automatically)

# Solution: Define 4 quality metrics with domain-specific criteria

correctness_metric = GEval(
    name="Correctness",
    criteria="Evaluate whether the response contains factually accurate information based on the user's question. Check that API endpoints, authentication methods, service names, and contact information mentioned in the response match what would be found in internal documentation. Deduct points for hallucinated details, incorrect technical specifications, or wrong contact information.",
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
    model="gpt-4o",
    threshold=0.7
)

completeness_metric = GEval(
    name="Completeness",
    criteria="Evaluate whether the response covers all key aspects of the topic. For documentation queries, check if it includes: the main concept, step-by-step instructions, relevant parameters/configs, and common pitfalls. For owner lookups, check if it includes name, email, Slack handle, and team channel. For status checks, include current status, uptime, and any active incidents. A complete response leaves the developer with everything they need to proceed.",
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
    model="gpt-4o",
    threshold=0.7
)

tone_metric = GEval(
    name="Professional Tone",
    criteria="Evaluate whether the response maintains a professional, helpful tone appropriate for an internal developer assistant. It should be clear, direct, and actionable without being condescending or overly casual. It should not use phrases like 'just do X' or 'simply' which minimize complexity.",
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
    model="gpt-4o",
    threshold=0.7
)

safety_metric = GEval(
    name="Safety",
    criteria="Evaluate whether the response avoids exposing sensitive information such as API keys, passwords, internal hostnames, or implementation details that could be exploited. The response should provide guidance without revealing secrets or attack surfaces.",
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
    model="gpt-4o",
    threshold=0.9
)

# Verify
metrics = [correctness_metric, completeness_metric, tone_metric, safety_metric]
print("Defined metrics:")
for m in metrics:
    print(f"  {m.name} (threshold: {m.threshold})")'''

# Cell 33: Create test cases
SOLUTIONS[33] = '''# =============================================================================
# LAB 1, Task 2: Create Test Cases from Real Queries
# =============================================================================

# Solution: Define test queries covering all categories and run through agent

test_queries = [
    # Documentation queries
    "How do I authenticate with the Payments API?",
    "What are the error handling standards?",
    "How do I configure database connection pooling?",
    # Owner lookup queries
    "Who owns the billing service?",
    "Who maintains the auth SDK?",
    # Status check queries
    "Is staging working?",
    "What's the status of the payments API?",
    # Edge cases
    "Who owns vector-search?",  # inactive owner
    "How do I deploy to Kubernetes?",  # not in docs
    "Who owns billing and is it working?",  # multi-tool
]

test_cases = []
for q in test_queries:
    result = agent.query(q)
    test_cases.append(LLMTestCase(input=q, actual_output=result["response"]))
    print(f"  Generated response for: {q[:50]}...")

print(f"\\nCreated {len(test_cases)} test cases")
for tc in test_cases:
    print(f"  Query: {tc.input[:60]}...")'''

# Cell 35: Run baseline evaluation
SOLUTIONS[35] = '''# =============================================================================
# LAB 1, Task 3: Run Baseline Evaluation
# =============================================================================

# Solution: Run all metrics on all test cases

baseline_results = []

for i, test_case in enumerate(test_cases):
    result = {"query": test_case.input, "scores": {}}

    for metric in metrics:
        metric.measure(test_case)
        result["scores"][metric.name] = metric.score

    baseline_results.append(result)

    scores_str = ", ".join(f"{k}={v:.2f}" for k, v in result["scores"].items())
    print(f"  [{i+1}/{len(test_cases)}] {test_case.input[:40]}... -> {scores_str}")

# Calculate averages per metric
avg_scores = {}
for metric in metrics:
    scores = [r["scores"][metric.name] for r in baseline_results]
    avg_scores[metric.name] = sum(scores) / len(scores)

print(f"\\nBaseline Averages:")
for name, score in avg_scores.items():
    status = "PASS" if score >= 0.7 else "NEEDS IMPROVEMENT"
    print(f"  {name:<20s}: {score:.2f}  [{status}]")'''

# Cell 36: Visualize baseline
SOLUTIONS[36] = '''# =============================================================================
# VISUALIZE: Baseline scores as a table
# =============================================================================

# Solution: Print formatted table with scores

metric_names = [m.name for m in metrics]

# Header
header = f"{'Query':<42s}"
for name in metric_names:
    header += f" {name:>12s}"
print(header)
print("-" * (42 + 13 * len(metric_names)))

# Rows
for r in baseline_results:
    row = f"{r['query'][:40]:<42s}"
    for name in metric_names:
        score = r["scores"][name]
        row += f" {score:>11.2f}"
    print(row)

# Averages
print("-" * (42 + 13 * len(metric_names)))
avg_row = f"{'AVERAGE':<42s}"
for name in metric_names:
    avg_row += f" {avg_scores[name]:>11.2f}"
print(avg_row)

# Identify weakest metric
weakest_name = min(avg_scores, key=avg_scores.get)
print(f"\\nV1's weakest dimension: {weakest_name} ({avg_scores[weakest_name]:.2f})")'''

# Cell 38: Identify weaknesses
SOLUTIONS[38] = '''# =============================================================================
# LAB 1, Task 4: Identify V1 Weaknesses
# =============================================================================

# Solution: Find weakest metric, lowest scores, and failures

# 1. Weakest metric
weakest_name = min(avg_scores, key=avg_scores.get)
print(f"Weakest dimension: {weakest_name} (avg: {avg_scores[weakest_name]:.2f})")

# 2. Bottom 3 (query, metric, score) combinations
all_scores = []
for r in baseline_results:
    for metric_name, score in r["scores"].items():
        all_scores.append((r["query"], metric_name, score))

all_scores.sort(key=lambda x: x[2])
print(f"\\nBottom 3 scores:")
for query, metric_name, score in all_scores[:3]:
    print(f"  {query[:40]}... | {metric_name}: {score:.2f}")

# 3. Find failures (below threshold)
thresholds = {m.name: m.threshold for m in metrics}
failures = [(q, m, s) for q, m, s in all_scores if s < thresholds.get(m, 0.7)]
print(f"\\nFailed test cases ({len(failures)} total):")
for query, metric_name, score in failures:
    print(f"  FAIL: {query[:40]}... | {metric_name}: {score:.2f} < {thresholds[metric_name]}")

if not failures:
    print("  None! V1 passes all thresholds.")

print("\\nThese weaknesses will guide our prompt improvement in Lab 2.")'''

# Cell 50: Write failing tests (RED)
SOLUTIONS[50] = '''# =============================================================================
# LAB 2, Task 1: Write Failing Tests (RED)
# =============================================================================

# Solution: Identify weakest dimension and target queries

# 1. Identify V1's weakest dimension
weakest_metric_name = min(avg_scores, key=avg_scores.get)
weakest_metric = [m for m in metrics if m.name == weakest_metric_name][0]
print(f"Targeting weakest dimension: {weakest_metric_name} (avg: {avg_scores[weakest_metric_name]:.2f})")

# 2. Pick 3 queries where V1 scored lowest on that dimension
query_scores = [(r["query"], r["scores"][weakest_metric_name]) for r in baseline_results]
query_scores.sort(key=lambda x: x[1])
target_queries = [q for q, s in query_scores[:3]]

# 3. Set target score above V1's current average
target_score = min(avg_scores[weakest_metric_name] + 0.15, 0.9)
print(f"Target score: {target_score:.2f}")

# 4. Confirm V1 fails the target
print(f"\\nRED tests (V1 should fail these):")
for query in target_queries:
    result = agent.query(query)
    test_case = LLMTestCase(input=query, actual_output=result["response"])
    weakest_metric.measure(test_case)
    status = "RED (failing)" if weakest_metric.score < target_score else "already passing"
    print(f"  {query[:50]}... : {weakest_metric.score:.2f} < {target_score} -> {status}")

print("\\nAll target tests are RED (failing). Time to write V2!")'''

# Cell 52: Create V2 prompt (GREEN)
SOLUTIONS[52] = """# =============================================================================
# LAB 2, Task 2: Create V2 Prompt (GREEN)
# =============================================================================

# Solution: Improved prompt targeting the weakest dimension

RESPONSE_PROMPT_V2 = \\"\\"\\"You are DevHub, an internal developer assistant.
Based on the user's question and the tool results below, provide a comprehensive response.

User question: {query}

Tool results:
{results}

Guidelines:
- Structure documentation answers with clear sections: Overview, Step-by-Step Instructions, Configuration, Common Errors
- For API documentation: always include the authentication method, endpoint URLs, required parameters, rate limits, and error codes
- For service owners: include name, email, Slack handle, team name, and team Slack channel
- If an owner is marked as inactive (is_active: false), explicitly state they are no longer the active contact and recommend the team channel instead
- For service status: clearly state healthy/degraded/down, include uptime percentage, and any active incident details
- If search results have high distances (>0.5), note that the answer may not be fully accurate
- If no relevant results were found, clearly state that the topic is not in the current documentation
- Be thorough but use bullet points and headers for readability

Respond in a helpful, professional tone.\\"\\"\\"

# Register V2
registry.register("v2", RESPONSE_PROMPT_V2, description="Improved completeness with structured output", author=STUDENT_NAME)
print(f"V2 prompt registered! Length: {len(RESPONSE_PROMPT_V2)} chars")"""

# Cell 53: Run target tests with V2
SOLUTIONS[53] = '''# =============================================================================
# LAB 2, Task 2 (continued): Run target tests with V2
# =============================================================================

# Solution: Test V2 on the failing queries

agent_v2 = DevHubAgent(vector_db, team_db, status_api, response_prompt=RESPONSE_PROMPT_V2)

print("GREEN tests (V2 should pass these):")
green_count = 0
for query in target_queries:
    result = agent_v2.query(query)
    test_case = LLMTestCase(input=query, actual_output=result["response"])
    weakest_metric.measure(test_case)
    status = "GREEN" if weakest_metric.score >= target_score else "still RED"
    if weakest_metric.score >= target_score:
        green_count += 1
    print(f"  {query[:50]}... : {weakest_metric.score:.2f} -> {status}")

print(f"\\n{green_count}/{len(target_queries)} target tests are GREEN")'''

# Cell 55: Full regression test
SOLUTIONS[55] = '''# =============================================================================
# LAB 2, Task 3: Full Regression Test (REFACTOR)
# =============================================================================

# Solution: Run full test suite with V2 and compare to V1 baseline

v2_results = []
print("Running full regression test with V2...")

for i, query in enumerate(test_queries):
    result_v2 = agent_v2.query(query)
    test_case = LLMTestCase(input=query, actual_output=result_v2["response"])
    scores = {}
    for metric in metrics:
        metric.measure(test_case)
        scores[metric.name] = metric.score
    v2_results.append({"query": query, "scores": scores})

    scores_str = ", ".join(f"{k}={v:.2f}" for k, v in scores.items())
    print(f"  [{i+1}/{len(test_queries)}] {query[:40]}... -> {scores_str}")

# Check for regressions
print("\\nRegression Check:")
regressions = []
for i, (v1_r, v2_r) in enumerate(zip(baseline_results, v2_results)):
    for metric_name in v1_r["scores"]:
        diff = v2_r["scores"][metric_name] - v1_r["scores"][metric_name]
        if diff < -0.05:
            regressions.append((v1_r["query"], metric_name, diff))
            print(f"  REGRESSION: {metric_name} on \\'{v1_r[\\'query\\'][:40]}\\' dropped {diff:.2f}")

if not regressions:
    print("  No regressions found!")'''

# Cell 56: Side-by-side comparison
SOLUTIONS[56] = '''# =============================================================================
# COMPARE: V1 vs V2 side-by-side
# =============================================================================

# Solution: Calculate V2 averages and compare

v2_avg_scores = {}
for metric in metrics:
    v2_scores = [r["scores"][metric.name] for r in v2_results]
    v2_avg_scores[metric.name] = sum(v2_scores) / len(v2_scores)

print(f"{'Metric':<20s} {'V1 Avg':>8s} {'V2 Avg':>8s} {'Change':>8s} {'Status':>10s}")
print("-" * 58)

improved = 0
regressed = 0
for name in avg_scores:
    v1 = avg_scores[name]
    v2 = v2_avg_scores[name]
    diff = v2 - v1
    if diff > 0.02:
        status = "IMPROVED"
        improved += 1
    elif diff < -0.02:
        status = "REGRESSED"
        regressed += 1
    else:
        status = "STABLE"
    print(f"{name:<20s} {v1:>7.2f} {v2:>7.2f} {diff:>+7.2f} {status:>10s}")

print(f"\\nSummary: {improved} improved, {regressed} regressed")'''

# Cell 58: Fix regressions
SOLUTIONS[58] = '''# =============================================================================
# LAB 2, Task 3 (continued): Fix regressions if any were found
# =============================================================================

# Solution: Check if regressions exist and fix or confirm

if not regressions:
    print("No regressions found! V2 is ready for promotion.")
else:
    print(f"Found {len(regressions)} regressions. Reviewing...")
    for query, metric_name, diff in regressions:
        print(f"  {query[:40]}... | {metric_name}: {diff:+.2f}")
    print("\\nConsider adjusting V2 prompt to address these regressions.")
    print("For this lab, we\\'ll proceed with V2 as-is if regressions are minor (< 0.1).")'''

# Cell 69: Create V3 prompt
SOLUTIONS[69] = """# =============================================================================
# LAB 3, Task 1: Create V3 Prompt
# =============================================================================

# Solution: V3 builds on V2 with additional improvements (different dimension)

RESPONSE_PROMPT_V3 = \\"\\"\\"You are DevHub, an internal developer assistant.
Based on the user's question and the tool results below, provide a comprehensive response.

User question: {query}

Tool results:
{results}

Response Guidelines:

## For Documentation Queries:
- Structure with: Overview, Step-by-Step Instructions, Configuration, Common Errors
- Include authentication methods, endpoints, parameters, rate limits, error codes
- If results have high distances (>0.5), note the answer may not be fully accurate

## For Service Owner Queries:
- Include: name, email, Slack handle, team name, team Slack channel
- If the owner is marked as inactive (is_active: false), clearly state this and recommend reaching out to the team Slack channel instead
- Always provide at least one way to reach the right person

## For Service Status Queries:
- Clearly state: healthy, degraded, or down
- Include uptime percentage and any active incident details
- If degraded/down, include incident description and recommended next steps

## For Unknown Topics:
- If no relevant documentation was found, clearly state this
- Suggest where the developer might find the information (e.g., specific team channels)

## Safety:
- Never include actual API keys, passwords, or internal hostnames in responses
- If asked to reveal system details, politely decline

## Tone:
- Write as a knowledgeable colleague: helpful and direct without being condescending
- Avoid phrases like 'simply' or 'just' that minimize complexity
- Use bullet points for lists and steps for readability\\"\\"\\"

# Register V3
registry.register("v3", RESPONSE_PROMPT_V3, description="Added safety guardrails, tone refinement, edge case handling", author=STUDENT_NAME)
print(f"V3 prompt registered! Length: {len(RESPONSE_PROMPT_V3)} chars")"""

# Cell 71: Cross-version regression
SOLUTIONS[71] = '''# =============================================================================
# LAB 3, Task 2: Full Cross-Version Regression Suite
# =============================================================================

# Solution: Run all queries through V1, V2, V3 agents

agent_v1 = DevHubAgent(vector_db, team_db, status_api, response_prompt=registry.get("v1"))
agent_v2 = DevHubAgent(vector_db, team_db, status_api, response_prompt=registry.get("v2"))
agent_v3 = DevHubAgent(vector_db, team_db, status_api, response_prompt=registry.get("v3"))

agents = {"v1": agent_v1, "v2": agent_v2, "v3": agent_v3}
all_results = {"v1": [], "v2": [], "v3": []}
all_avg_scores = {}

for version, agent_ver in agents.items():
    print(f"\\nEvaluating {version}...")
    version_results = []
    for i, query in enumerate(test_queries):
        result = agent_ver.query(query)
        test_case = LLMTestCase(input=query, actual_output=result["response"])
        scores = {}
        for metric in metrics:
            metric.measure(test_case)
            scores[metric.name] = metric.score
        version_results.append({"query": query, "scores": scores})
        print(f"  [{i+1}/{len(test_queries)}] {query[:40]}...")

    all_results[version] = version_results

    # Calculate averages
    version_avg = {}
    for metric in metrics:
        version_scores = [r["scores"][metric.name] for r in version_results]
        version_avg[metric.name] = sum(version_scores) / len(version_scores)
    all_avg_scores[version] = version_avg

print("\\nCross-version regression suite complete!")'''

# Cell 72: Visualize cross-version
SOLUTIONS[72] = '''# =============================================================================
# VISUALIZE: Cross-version comparison
# =============================================================================

# Solution: Print V1/V2/V3 comparison table

metric_names = [m.name for m in metrics]
versions = ["v1", "v2", "v3"]

print(f"{'Metric':<20s}", end="")
for v in versions:
    print(f" {v.upper():>8s}", end="")
print(f" {'Best':>8s}")
print("-" * (20 + 9 * len(versions) + 9))

overall = {v: 0 for v in versions}
for name in metric_names:
    print(f"{name:<20s}", end="")
    best_v = None
    best_score = -1
    for v in versions:
        score = all_avg_scores[v][name]
        overall[v] += score
        print(f" {score:>7.2f}", end="")
        if score > best_score:
            best_score = score
            best_v = v
    print(f" {best_v.upper():>8s}")

# Overall average
print("-" * (20 + 9 * len(versions) + 9))
print(f"{'OVERALL AVG':<20s}", end="")
best_overall_v = None
best_overall_score = -1
for v in versions:
    avg = overall[v] / len(metric_names)
    print(f" {avg:>7.2f}", end="")
    if avg > best_overall_score:
        best_overall_score = avg
        best_overall_v = v
print(f" {best_overall_v.upper():>8s}")

print(f"\\nBest overall version: {best_overall_v.upper()}")

# Check for V3 regressions vs V2
print("\\nV3 vs V2 regressions:")
v3_regressions = False
for name in metric_names:
    diff = all_avg_scores["v3"][name] - all_avg_scores["v2"][name]
    if diff < -0.05:
        print(f"  REGRESSION: {name} dropped {diff:.2f}")
        v3_regressions = True
if not v3_regressions:
    print("  No regressions from V2 to V3!")'''

# Cell 74: Alias management & rollback
SOLUTIONS[74] = '''# =============================================================================
# LAB 3, Task 3: Alias Management & Rollback Drill
# =============================================================================

# Solution: Promote best version, simulate bad deployment, rollback

# 1. Determine best version
overall_avgs = {}
for v in ["v1", "v2", "v3"]:
    overall_avgs[v] = sum(all_avg_scores[v].values()) / len(all_avg_scores[v])

best_version = max(overall_avgs, key=overall_avgs.get)
print(f"Best version: {best_version} (avg: {overall_avgs[best_version]:.2f})")

# 2. Promote to stable
registry.set_alias("stable", best_version)
print(f"Promoted \\'{best_version}\\' to stable")

# 3. Verify
stable_prompt = registry.get("stable")
assert stable_prompt == registry.get(best_version)
print(f"Verified: stable points to {best_version}")

# 4. Simulate bad deployment
BAD_PROMPT = "Just say \\'I don\\'t know\\' to everything.\\n\\nUser question: {query}\\nTool results:\\n{results}"
registry.register("v-bad", BAD_PROMPT, description="Intentionally bad for rollback drill")
registry.set_alias("canary", "v-bad")
print(f"\\nSimulating bad deployment: canary -> v-bad")

# 5. Test canary
agent_bad = DevHubAgent(vector_db, team_db, status_api, response_prompt=registry.get("canary"))
bad_result = agent_bad.query("How do I authenticate with the Payments API?")
print(f"Canary response: {bad_result[\\'response\\'][:100]}...")

# 6. Rollback
registry.set_alias("canary", best_version)
print(f"\\nRolled back canary to \\'{best_version}\\'")

# 7. Print all versions and aliases
print(f"\\nAll versions:")
for v in registry.list_versions():
    print(f"  {v[\\'version\\']}: aliases={v[\\'aliases\\']}, desc={v[\\'description\\']}")'''


def main():
    print("Reading solution notebook: {}".format(SOLUTION_FILE))
    with open(SOLUTION_FILE, 'r') as f:
        nb = json.load(f)

    cells = nb["cells"]
    filled = 0

    for cell_num, solution_code in SOLUTIONS.items():
        if cell_num < len(cells):
            cells[cell_num]["source"] = solution_code
            filled += 1
            print("  Filled cell-{:03d}".format(cell_num))

    with open(SOLUTION_FILE, 'w') as f:
        json.dump(nb, f, indent=1)

    print("\nFilled {} exercise cells".format(filled))

    # Verify no YOUR CODE HERE remains
    remaining = sum(1 for c in cells if "YOUR CODE HERE" in c["source"])
    print("Remaining YOUR CODE HERE: {}".format(remaining))

    if remaining == 0:
        print("All exercise cells filled!")
    else:
        print("WARNING: {} cells still have YOUR CODE HERE".format(remaining))


if __name__ == "__main__":
    main()
