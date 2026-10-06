import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any


class VectorStore:
    """
    Lightweight dependency-free vector store.

    v0.1 uses deterministic hashed text embeddings so that the
    AgenticOS prototype does not require external ML dependencies.
    """

    def __init__(
        self,
        storage_path: str | Path = "data/memory/vectors.json",
        dimensions: int = 128,
    ):
        if dimensions <= 0:
            raise ValueError("dimensions must be greater than zero.")

        self.storage_path = Path(storage_path)
        self.dimensions = dimensions

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.storage_path.exists():
            self._write([])

    def _read(self) -> list[dict[str, Any]]:
        try:
            with self.storage_path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, list):
                raise ValueError("Vector storage must contain a list.")

            return data

        except json.JSONDecodeError as error:
            raise ValueError(
                "Vector storage contains invalid JSON."
            ) from error

    def _write(self, vectors: list[dict[str, Any]]) -> None:
        with self.storage_path.open("w", encoding="utf-8") as file:
            json.dump(vectors, file, indent=2, ensure_ascii=False)

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower())

    def embed(self, text: str) -> list[float]:
        """
        Convert text into a deterministic normalized vector.
        """

        if not isinstance(text, str):
            raise ValueError("Text must be a string.")

        vector = [0.0] * self.dimensions

        for token in self._tokenize(text):
            digest = hashlib.sha256(
                token.encode("utf-8")
            ).digest()

            index = int.from_bytes(
                digest[:4],
                byteorder="big",
            ) % self.dimensions

            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        magnitude = math.sqrt(
            sum(value * value for value in vector)
        )

        if magnitude == 0:
            return vector

        return [
            value / magnitude
            for value in vector
        ]

    def _cosine_similarity(
        self,
        first: list[float],
        second: list[float],
    ) -> float:
        if len(first) != len(second):
            raise ValueError("Vectors must have equal dimensions.")

        return sum(
            a * b
            for a, b in zip(first, second)
        )

    def add(
        self,
        memory_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not memory_id.strip():
            raise ValueError("memory_id must be non-empty.")

        if not content.strip():
            raise ValueError("content must be non-empty.")

        vectors = self._read()

        if any(item["memory_id"] == memory_id for item in vectors):
            raise ValueError(
                f"Vector '{memory_id}' already exists."
            )

        item = {
            "memory_id": memory_id,
            "content": content,
            "metadata": metadata or {},
            "vector": self.embed(content),
        }

        vectors.append(item)
        self._write(vectors)

        return item.copy()

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        if not isinstance(query, str) or not query.strip():
            return []

        if top_k <= 0:
            return []

        query_vector = self.embed(query)
        vectors = self._read()

        scored = []

        for item in vectors:
            score = self._cosine_similarity(
                query_vector,
                item["vector"],
            )

            scored.append(
                {
                    "memory_id": item["memory_id"],
                    "content": item["content"],
                    "metadata": item["metadata"],
                    "score": score,
                }
            )

        scored.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        return scored[:top_k]

    def delete(self, memory_id: str) -> bool:
        vectors = self._read()

        updated = [
            item
            for item in vectors
            if item["memory_id"] != memory_id
        ]

        if len(updated) == len(vectors):
            return False

        self._write(updated)
        return True

    def clear(self) -> int:
        vectors = self._read()
        count = len(vectors)

        self._write([])

        return count

    def list_all(self) -> list[dict[str, Any]]:
        return [item.copy() for item in self._read()]