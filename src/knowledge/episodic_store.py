import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class EpisodicMemoryStore:
    """
    Persistent episodic memory store.

    Each memory is stored as an independent episode containing:
    - memory_id
    - content
    - metadata
    - created_at
    """

    def __init__(self, storage_path: str | Path = "data/memory/episodic.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.storage_path.exists():
            self._write([])

    def _read(self) -> list[dict[str, Any]]:
        try:
            with self.storage_path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, list):
                raise ValueError("Episodic memory storage must contain a list.")

            return data

        except json.JSONDecodeError as error:
            raise ValueError(
                "Episodic memory storage contains invalid JSON."
            ) from error

    def _write(self, memories: list[dict[str, Any]]) -> None:
        with self.storage_path.open("w", encoding="utf-8") as file:
            json.dump(memories, file, indent=2, ensure_ascii=False)

    def add(
        self,
        memory_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not isinstance(memory_id, str) or not memory_id.strip():
            raise ValueError("memory_id must be a non-empty string.")

        if not isinstance(content, str) or not content.strip():
            raise ValueError("content must be a non-empty string.")

        memories = self._read()

        if any(memory["memory_id"] == memory_id for memory in memories):
            raise ValueError(
                f"Memory '{memory_id}' already exists."
            )

        memory = {
            "memory_id": memory_id,
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        memories.append(memory)
        self._write(memories)

        return memory.copy()

    def get(self, memory_id: str) -> dict[str, Any]:
        memories = self._read()

        for memory in memories:
            if memory["memory_id"] == memory_id:
                return memory.copy()

        raise KeyError(
            f"Memory '{memory_id}' does not exist."
        )

    def list_all(self) -> list[dict[str, Any]]:
        return [memory.copy() for memory in self._read()]

    def delete(self, memory_id: str) -> bool:
        memories = self._read()

        updated = [
            memory
            for memory in memories
            if memory["memory_id"] != memory_id
        ]

        if len(updated) == len(memories):
            return False

        self._write(updated)
        return True

    def clear(self) -> int:
        memories = self._read()
        count = len(memories)

        self._write([])

        return count

    def search(self, query: str) -> list[dict[str, Any]]:
        """
        Basic keyword retrieval from episodic memory.

        This is intentionally lightweight. Semantic retrieval is handled
        separately by VectorStore.
        """
        if not isinstance(query, str) or not query.strip():
            return []

        query_terms = set(query.lower().split())
        results = []

        for memory in self._read():
            content_terms = set(memory["content"].lower().split())

            if query_terms & content_terms:
                results.append(memory.copy())

        return results