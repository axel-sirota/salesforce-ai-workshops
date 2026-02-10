"""
DevHubAgent
===========

Orchestration layer that decides which tools to call based on user queries.

VERSION: V0 (no observability - students will add it in Session 1)

Architecture:
1. Receives user query
2. Uses GPT-4o-mini to plan which tools to call
3. Executes tools (VectorDB, TeamDB, StatusAPI)
4. Synthesizes final response with GPT-4o-mini

INTENTIONAL: No tracing, no metrics, no logging.
Students will add OpenTelemetry in Session 1.
"""

import json
from openai import OpenAI

from config import Config
from services.vector_db import VectorDB
from services.team_db import TeamDB
from services.status_api import StatusAPI


TOOL_PLANNING_PROMPT = """You are a tool planner for DevHub, an internal developer assistant.
Based on the user's question, decide which tools to call.

Available tools:
1. search_docs: Search internal documentation for API guides, SDK docs, best practices
   - Use when: User asks "how to", needs documentation, wants examples
   - Args: {{"query": "search terms"}}

2. find_owner: Find the owner/contact for a service or topic
   - Use when: User asks "who owns", "who can help", "contact for"
   - Args: {{"service": "service name or topic"}}

3. check_status: Check if a service is healthy or has issues
   - Use when: User asks "is X working", "status of", "any issues with"
   - Args: {{"service": "service name"}}

Rules:
- Call 1-3 tools maximum
- Return a JSON array of tool calls
- Order matters: call tools in the order results should be used

User question: {query}

Respond with ONLY a JSON array, no explanation:
[{{"tool": "tool_name", "args": {{...}}}}, ...]

If no tools are needed, return: []"""


RESPONSE_SYNTHESIS_PROMPT = """You are DevHub, an internal developer assistant.
Based on the user's question and the tool results below, provide a helpful response.

User question: {query}

Tool results:
{results}

Guidelines:
- Be concise and actionable
- If documentation was found, summarize the key points
- If an owner was found, include their contact info (Slack handle, email)
- If an owner is marked as inactive (is_active: false), mention this and suggest contacting the team channel instead
- If service status is degraded/unhealthy, clearly state this with any incident details
- If results have low similarity scores (distance > 0.5), mention the answer may not be accurate
- If a tool failed or timed out, acknowledge the issue

Respond in a helpful, professional tone."""


class DevHubAgent:
    """
    Agent that orchestrates tool calls to answer developer questions.

    V0: No observability. Students will add tracing in Session 1.
    """

    def __init__(
        self,
        vector_db: VectorDB | None = None,
        team_db: TeamDB | None = None,
        status_api: StatusAPI | None = None
    ):
        """
        Initialize DevHubAgent with services.

        Args:
            vector_db: VectorDB instance (created if not provided)
            team_db: TeamDB instance (created if not provided)
            status_api: StatusAPI instance (created if not provided)
        """
        # Initialize services
        self.vector_db = vector_db or VectorDB()
        self.team_db = team_db or TeamDB()
        self.status_api = status_api or StatusAPI()

        # Initialize OpenAI client
        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set. Please set the environment variable.")

        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.LLM_MODEL

    def _plan_tools(self, query: str) -> list[dict]:
        """
        Use LLM to decide which tools to call.

        Args:
            query: User's question

        Returns:
            List of tool calls: [{"tool": "name", "args": {...}}, ...]
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a tool planning assistant. Respond only with valid JSON."
                },
                {
                    "role": "user",
                    "content": TOOL_PLANNING_PROMPT.format(query=query)
                }
            ],
            temperature=0.1,
            max_tokens=256
        )

        # Parse the JSON response
        content = response.choices[0].message.content.strip()

        # Handle potential markdown code blocks
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        try:
            tools = json.loads(content)
            if not isinstance(tools, list):
                return []
            return tools
        except json.JSONDecodeError:
            return []

    def _execute_tool(self, tool_name: str, args: dict) -> dict:
        """
        Execute a single tool and return results.

        Args:
            tool_name: Name of tool to execute
            args: Arguments for the tool

        Returns:
            dict with tool results and metadata
        """
        result = {
            "tool": tool_name,
            "success": False,
            "data": None,
            "error": None
        }

        try:
            if tool_name == "search_docs":
                query = args.get("query", "")
                data = self.vector_db.search(query)
                result["success"] = True
                result["data"] = {
                    "documents": data["documents"],
                    "metadatas": data["metadatas"],
                    "distances": data["distances"],
                    "latency_ms": data["latency_ms"]
                }

            elif tool_name == "find_owner":
                service = args.get("service", "")
                data = self.team_db.find_owner(service)
                result["success"] = True
                result["data"] = data

            elif tool_name == "check_status":
                service = args.get("service", "")
                data = self.status_api.check_status(service)
                result["success"] = True
                result["data"] = data

            else:
                result["error"] = f"Unknown tool: {tool_name}"

        except ConnectionError as e:
            result["error"] = f"Connection failed: {str(e)}"
        except TimeoutError as e:
            result["error"] = f"Timeout: {str(e)}"
        except Exception as e:
            result["error"] = f"Error: {str(e)}"

        return result

    def _generate_response(self, query: str, tool_results: list[dict]) -> str:
        """
        Synthesize final response from tool results.

        Args:
            query: Original user question
            tool_results: Results from tool execution

        Returns:
            Natural language response
        """
        # Format results for the prompt
        results_text = json.dumps(tool_results, indent=2)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are DevHub, a helpful internal developer assistant."
                },
                {
                    "role": "user",
                    "content": RESPONSE_SYNTHESIS_PROMPT.format(
                        query=query,
                        results=results_text
                    )
                }
            ],
            temperature=Config.LLM_TEMPERATURE,
            max_tokens=Config.LLM_MAX_TOKENS
        )

        return response.choices[0].message.content

    def query(self, user_query: str) -> dict:
        """
        Process a user query end-to-end.

        Args:
            user_query: The user's question

        Returns:
            dict with keys: response, tools_called, tool_results
        """
        # Step 1: Plan which tools to call
        planned_tools = self._plan_tools(user_query)

        # Step 2: Execute each tool
        tool_results = []
        for tool_call in planned_tools:
            tool_name = tool_call.get("tool", "")
            args = tool_call.get("args", {})
            result = self._execute_tool(tool_name, args)
            tool_results.append(result)

        # Step 3: Generate response
        response = self._generate_response(user_query, tool_results)

        return {
            "response": response,
            "tools_called": [t.get("tool") for t in planned_tools],
            "tool_results": tool_results
        }
