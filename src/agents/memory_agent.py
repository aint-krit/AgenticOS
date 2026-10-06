from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from src.agent_runtime.agent import Agent
from src.knowledge.episodic_store import EpisodicMemoryStore
from src.knowledge.vector_store import VectorStore


class MemoryAgent(Agent):
    """
    AgenticOS Memory Agent.

    Supports:
    - Original key/value memory API
    - Episodic memory storage
    - Vector-based memory search
    - Memory deletion
    - Memory clearing
    - Memory deletion verification
    - Agent Bus communication
    """

    def __init__(
        self,
        agent_id: str = "memory-agent",
        name: str = "Memory Agent",
        episodic_store: EpisodicMemoryStore | None = None,
        vector_store: VectorStore | None = None,
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            version="0.1.0",
            agent_type="specialized",
            capabilities=[
                "remember",
                "retrieve_memory",
                "search_memory",
                "delete_memory",
                "clear_memory",
                "verify_memory",
            ],
        )

        # When no stores are explicitly provided, use isolated
        # temporary storage. This prevents different MemoryAgent
        # instances from sharing stale test data.
        self._runtime_temp_dir = None

        if episodic_store is None and vector_store is None:
            self._runtime_temp_dir = TemporaryDirectory(
                prefix="agenticos-memory-"
            )

            base_path = Path(self._runtime_temp_dir.name)

            episodic_store = EpisodicMemoryStore(
                base_path / "episodic.json"
            )

            vector_store = VectorStore(
                base_path / "vectors.json"
            )

        elif episodic_store is None:
            episodic_store = EpisodicMemoryStore()

        elif vector_store is None:
            vector_store = VectorStore()

        self.episodic_store = episodic_store
        self.vector_store = vector_store

    def remember(
        self,
        memory_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Store or update a memory in both storage layers.

        Compatible with the original:

            remember("key", "value")
        """

        # Updating an existing memory is allowed.
        try:
            self.episodic_store.get(memory_id)

            self.episodic_store.delete(memory_id)
            self.vector_store.delete(memory_id)

        except KeyError:
            pass

        episodic_memory = self.episodic_store.add(
            memory_id=memory_id,
            content=content,
            metadata=metadata,
        )

        try:
            self.vector_store.add(
                memory_id=memory_id,
                content=content,
                metadata=metadata,
            )
        except Exception:
            self.episodic_store.delete(memory_id)
            raise

        return {
            "status": "stored",
            "memory_id": memory_id,
            "key": memory_id,
            "value": content,
            "content": content,
            "memory": episodic_memory,
        }

    def retrieve(
        self,
        memory_id: str,
    ) -> dict[str, Any]:
        """
        Retrieve a memory by ID.

        Returns:
            found     -> memory exists
            not_found -> memory does not exist

        This preserves the original MemoryAgent API.
        """

        try:
            memory = self.episodic_store.get(memory_id)

        except KeyError:
            return {
                "status": "not_found",
                "memory_id": memory_id,
                "key": memory_id,
                "value": None,
                "content": None,
                "memory": None,
            }

        return {
            "status": "found",
            "memory_id": memory_id,
            "key": memory_id,
            "value": memory["content"],
            "content": memory["content"],
            "memory": memory,
        }

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Perform vector-based memory retrieval.
        """

        return self.vector_store.search(
            query=query,
            top_k=top_k,
        )

    def delete(
        self,
        memory_id: str,
    ) -> dict[str, Any]:
        """
        Delete one memory from both storage layers.
        """

        episodic_deleted = self.episodic_store.delete(
            memory_id
        )

        vector_deleted = self.vector_store.delete(
            memory_id
        )

        return {
            "status": "deleted",
            "memory_id": memory_id,
            "episodic_deleted": episodic_deleted,
            "vector_deleted": vector_deleted,
        }

    def clear(
        self,
        memory_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Clear one memory when memory_id is supplied.

        Clear all memories when no memory_id is supplied.

        Supports both:

            clear("temporary")

        and:

            clear()
        """

        if memory_id is not None:
            return self.delete(memory_id)

        episodic_count = self.episodic_store.clear()
        vector_count = self.vector_store.clear()

        return {
            "status": "cleared",
            "episodic_deleted": episodic_count,
            "vector_deleted": vector_count,
        }

    def verify_deleted(
        self,
        memory_id: str,
    ) -> bool:
        """
        Verify that a memory no longer exists in either store.
        """

        try:
            self.episodic_store.get(memory_id)
            return False

        except KeyError:
            pass

        for item in self.vector_store.list_all():
            if item["memory_id"] == memory_id:
                return False

        return True

    def list_memories(self) -> list[dict[str, Any]]:
        """
        Return all episodic memories.
        """

        return self.episodic_store.list_all()

    def receive_message(
        self,
        message: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Handle Memory Agent operations received through Agent Bus.

        Supports both the original key/value message format and
        the expanded memory_id/content format.
        """

        self.received_messages.append(message)

        payload = message.get("payload", {})

        operation = (
            payload.get("operation")
            or message.get("operation")
        )

        try:
            # -----------------------------------------------------
            # REMEMBER
            # -----------------------------------------------------
            if operation == "REMEMBER":

                memory_id = (
                    payload.get("memory_id")
                    or payload.get("key")
                    or message.get("memory_id")
                    or message.get("key")
                )

                content = (
                    payload.get("content")
                    or payload.get("value")
                    or message.get("content")
                    or message.get("value")
                )

                if memory_id is None:
                    raise ValueError(
                        "REMEMBER requires 'memory_id' or 'key'."
                    )

                if content is None:
                    raise ValueError(
                        "REMEMBER requires 'content' or 'value'."
                    )

                result = self.remember(
                    memory_id=memory_id,
                    content=content,
                    metadata=payload.get("metadata"),
                )

            # -----------------------------------------------------
            # RETRIEVE MEMORY
            # -----------------------------------------------------
            elif operation == "RETRIEVE_MEMORY":

                memory_id = (
                    payload.get("memory_id")
                    or payload.get("key")
                    or message.get("memory_id")
                    or message.get("key")
                )

                if memory_id is None:
                    raise ValueError(
                        "RETRIEVE_MEMORY requires "
                        "'memory_id' or 'key'."
                    )

                result = self.retrieve(
                    memory_id=memory_id,
                )

            # -----------------------------------------------------
            # SEARCH MEMORY
            # -----------------------------------------------------
            elif operation == "SEARCH_MEMORY":

                query = (
                    payload.get("query")
                    or message.get("query")
                )

                if query is None:
                    raise ValueError(
                        "SEARCH_MEMORY requires 'query'."
                    )

                result = {
                    "status": "searched",
                    "results": self.search(
                        query=query,
                        top_k=payload.get("top_k", 5),
                    ),
                }

            # -----------------------------------------------------
            # DELETE MEMORY
            # -----------------------------------------------------
            elif operation == "DELETE_MEMORY":

                memory_id = (
                    payload.get("memory_id")
                    or payload.get("key")
                    or message.get("memory_id")
                    or message.get("key")
                )

                if memory_id is None:
                    raise ValueError(
                        "DELETE_MEMORY requires "
                        "'memory_id' or 'key'."
                    )

                result = self.delete(
                    memory_id=memory_id,
                )

            # -----------------------------------------------------
            # CLEAR MEMORY
            # -----------------------------------------------------
            elif operation == "CLEAR_MEMORY":

                memory_id = (
                    payload.get("memory_id")
                    or payload.get("key")
                    or message.get("memory_id")
                    or message.get("key")
                )

                result = self.clear(
                    memory_id=memory_id,
                )

            # -----------------------------------------------------
            # VERIFY MEMORY
            # -----------------------------------------------------
            elif operation == "VERIFY_MEMORY":

                memory_id = (
                    payload.get("memory_id")
                    or payload.get("key")
                    or message.get("memory_id")
                    or message.get("key")
                )

                if memory_id is None:
                    raise ValueError(
                        "VERIFY_MEMORY requires "
                        "'memory_id' or 'key'."
                    )

                result = {
                    "status": "verified",
                    "memory_id": memory_id,
                    "deleted": self.verify_deleted(
                        memory_id
                    ),
                }

            else:
                raise ValueError(
                    f"Unknown memory operation: {operation}"
                )

            return {
                "message_id": message.get("message_id"),
                "request_id": message.get("request_id"),
                "sender": self.agent_id,
                "receiver": message.get("sender"),
                "message_type": "RESPONSE",
                "timestamp": message.get("timestamp"),
                "payload": result,
            }

        except (KeyError, ValueError) as error:

            return {
                "message_id": message.get("message_id"),
                "request_id": message.get("request_id"),
                "sender": self.agent_id,
                "receiver": message.get("sender"),
                "message_type": "ERROR",
                "timestamp": message.get("timestamp"),
                "payload": {
                    "status": "error",
                    "error_type": type(error).__name__,
                    "error": str(error),
                },
            }