"""
TeamDB Service
==============

SQLite-based team and owner lookup.

INTENTIONAL PROBLEM (for workshop debugging):
- 10% stale data: Returns owners with flipped is_active flag

Students will add OpenTelemetry tracing to detect stale data issues.
"""

import json
import random
import sqlite3
import time
from pathlib import Path

from config import Config


class TeamDB:
    """
    SQLite database for team and owner information.

    Uses in-memory SQLite for fast lookups.
    Has intentional stale data problem for workshop exercises.
    """

    def __init__(self, teams_path: str | None = None):
        """
        Initialize TeamDB with SQLite.

        Args:
            teams_path: Path to teams.json. Defaults to Config.TEAMS_PATH.
        """
        self.teams_path = teams_path or Config.TEAMS_PATH

        # Initialize in-memory SQLite
        self._conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

        # Create tables and load data
        self._create_tables()
        self._load_data()

    def _create_tables(self):
        """Create teams and owners tables."""
        cursor = self._conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                slack_channel TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS owners (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                slack_handle TEXT,
                team_id TEXT REFERENCES teams(id),
                services TEXT,  -- JSON array of service names
                is_active INTEGER DEFAULT 1
            )
        """)

        # Create index for service lookup
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_owners_services
            ON owners(services)
        """)

        self._conn.commit()

    def _load_data(self):
        """Load data from JSON into SQLite."""
        teams_file = Path(self.teams_path)
        if not teams_file.exists():
            raise FileNotFoundError(f"Teams file not found: {self.teams_path}")

        with open(teams_file) as f:
            data = json.load(f)

        cursor = self._conn.cursor()

        # Insert teams
        for team in data.get("teams", []):
            cursor.execute(
                "INSERT OR REPLACE INTO teams (id, name, description, slack_channel) VALUES (?, ?, ?, ?)",
                (team["id"], team["name"], team["description"], team["slack_channel"])
            )

        # Insert owners
        for owner in data.get("owners", []):
            cursor.execute(
                """INSERT OR REPLACE INTO owners
                   (id, name, email, slack_handle, team_id, services, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    owner["id"],
                    owner["name"],
                    owner["email"],
                    owner["slack_handle"],
                    owner["team_id"],
                    json.dumps(owner["services"]),
                    1 if owner["is_active"] else 0
                )
            )

        self._conn.commit()

        # Store counts
        cursor.execute("SELECT COUNT(*) FROM teams")
        self._team_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM owners")
        self._owner_count = cursor.fetchone()[0]

    def find_owner(self, service_or_topic: str) -> dict:
        """
        Find the owner of a service or topic.

        Args:
            service_or_topic: Service name or topic to search for

        Returns:
            dict with keys: found, owner, team, latency_ms
        """
        start_time = time.time()

        # Simulate normal latency
        latency = random.randint(
            Config.TEAM_DB_LATENCY_MIN,
            Config.TEAM_DB_LATENCY_MAX
        )
        time.sleep(latency / 1000)

        cursor = self._conn.cursor()

        # Search for owner by service (case-insensitive partial match)
        search_term = f"%{service_or_topic.lower()}%"

        cursor.execute("""
            SELECT o.*, t.name as team_name, t.slack_channel as team_slack
            FROM owners o
            JOIN teams t ON o.team_id = t.id
            WHERE LOWER(o.services) LIKE ?
            ORDER BY o.is_active DESC, o.name ASC
            LIMIT 1
        """, (search_term,))

        row = cursor.fetchone()

        latency_ms = int((time.time() - start_time) * 1000)

        if not row:
            return {
                "found": False,
                "owner": None,
                "team": None,
                "latency_ms": latency_ms
            }

        # Convert row to dict
        owner = {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "slack_handle": row["slack_handle"],
            "services": json.loads(row["services"]),
            "is_active": bool(row["is_active"])
        }

        team = {
            "id": row["team_id"],
            "name": row["team_name"],
            "slack_channel": row["team_slack"]
        }

        # === INTENTIONAL PROBLEM: Stale Data (10%) ===
        # Sometimes return owner with flipped is_active flag
        if random.random() < Config.TEAM_DB_STALE_DATA_RATE:
            # Flip is_active to simulate stale cache
            owner["is_active"] = not owner["is_active"]

        return {
            "found": True,
            "owner": owner,
            "team": team,
            "latency_ms": latency_ms
        }

    def get_all_teams(self) -> list[dict]:
        """Get all teams."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM teams")

        return [dict(row) for row in cursor.fetchall()]

    def get_team_owners(self, team_id: str) -> list[dict]:
        """Get all owners for a team."""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM owners WHERE team_id = ?",
            (team_id,)
        )

        owners = []
        for row in cursor.fetchall():
            owners.append({
                "id": row["id"],
                "name": row["name"],
                "email": row["email"],
                "slack_handle": row["slack_handle"],
                "services": json.loads(row["services"]),
                "is_active": bool(row["is_active"])
            })

        return owners

    @property
    def team_count(self) -> int:
        """Return number of teams in the database."""
        return self._team_count

    @property
    def owner_count(self) -> int:
        """Return number of owners in the database."""
        return self._owner_count
