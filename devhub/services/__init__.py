"""
DevHub Services Layer
=====================

Data layer services for DevHub:
- VectorDB: ChromaDB-based document search
- TeamDB: SQLite-based team/owner lookup
- StatusAPI: Mock service status API

Note: Service implementations will be added in Phases 4-6.
"""

from .vector_db import VectorDB

# Future imports:
# from .team_db import TeamDB
# from .status_api import StatusAPI

__all__ = ["VectorDB"]
