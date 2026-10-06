from pathlib import Path
from tempfile import TemporaryDirectory

from src.agents.memory_agent import MemoryAgent
from src.knowledge.episodic_store import EpisodicMemoryStore
from src.knowledge.vector_store import VectorStore


def main():
    print("=" * 70)
    print("AgenticOS v0.1 - Knowledge + Memory Demo")
    print("=" * 70)

    with TemporaryDirectory(prefix="agenticos-demo-") as temp_dir:
        base_path = Path(temp_dir)

        episodic_store = EpisodicMemoryStore(
            base_path / "episodic.json"
        )

        vector_store = VectorStore(
            base_path / "vectors.json"
        )

        memory = MemoryAgent(
            episodic_store=episodic_store,
            vector_store=vector_store,
        )

        memory.start()

        # ---------------------------------------------------------
        # 1. STORE
        # ---------------------------------------------------------
        print("\n[1] Storing memories...")

        memory.remember(
            memory_id="project-architecture",
            content=(
                "AgenticOS uses an Agent Bus to connect "
                "agents and route messages."
            ),
            metadata={
                "category": "architecture",
                "source": "demo",
            },
        )

        memory.remember(
            memory_id="application-agent",
            content=(
                "The Application Agent can open a web browser "
                "through the capability layer."
            ),
            metadata={
                "category": "agents",
                "source": "demo",
            },
        )

        memory.remember(
            memory_id="file-agent",
            content=(
                "The File Agent creates, reads, writes, "
                "and deletes files."
            ),
            metadata={
                "category": "agents",
                "source": "demo",
            },
        )

        print("    ✓ 3 memories stored")

        # ---------------------------------------------------------
        # 2. RETRIEVE
        # ---------------------------------------------------------
        print("\n[2] Retrieving exact memory...")

        retrieved = memory.retrieve(
            "project-architecture"
        )

        print(
            f"    Status: {retrieved['status']}"
        )

        print(
            f"    Memory: {retrieved['content']}"
        )

        # ---------------------------------------------------------
        # 3. VECTOR SEARCH
        # ---------------------------------------------------------
        print("\n[3] Searching memory using vector store...")

        results = memory.search(
            query="How do agents communicate?",
            top_k=3,
        )

        print(
            f"    Search results: {len(results)}"
        )

        for index, result in enumerate(results, start=1):
            print(
                f"    {index}. "
                f"{result['memory_id']} "
                f"(score={result['score']:.4f})"
            )

        # ---------------------------------------------------------
        # 4. USE MEMORY
        # ---------------------------------------------------------
        print("\n[4] Using retrieved memory...")

        if retrieved["status"] == "found":
            remembered_context = retrieved["content"]

            print("    ✓ Memory successfully retrieved")
            print(
                f"    Context supplied to agent: "
                f"{remembered_context}"
            )

        # ---------------------------------------------------------
        # 5. DELETE
        # ---------------------------------------------------------
        print("\n[5] Deleting one memory...")

        deleted = memory.delete(
            "file-agent"
        )

        print(
            f"    Status: {deleted['status']}"
        )

        print(
            f"    Episodic deleted: "
            f"{deleted['episodic_deleted']}"
        )

        print(
            f"    Vector deleted: "
            f"{deleted['vector_deleted']}"
        )

        # ---------------------------------------------------------
        # 6. VERIFY DELETION
        # ---------------------------------------------------------
        print("\n[6] Verifying memory deletion...")

        verified = memory.verify_deleted(
            "file-agent"
        )

        print(
            f"    Deleted successfully: {verified}"
        )

        # ---------------------------------------------------------
        # 7. CLEAR
        # ---------------------------------------------------------
        print("\n[7] Clearing remaining memories...")

        cleared = memory.clear()

        print(
            f"    Episodic memories cleared: "
            f"{cleared['episodic_deleted']}"
        )

        print(
            f"    Vector memories cleared: "
            f"{cleared['vector_deleted']}"
        )

        # ---------------------------------------------------------
        # 8. FINAL VERIFICATION
        # ---------------------------------------------------------
        print("\n[8] Final verification...")

        remaining = memory.list_memories()

        print(
            f"    Remaining memories: "
            f"{len(remaining)}"
        )

        if len(remaining) == 0:
            print("    ✓ Memory store is empty")

        print("\n" + "=" * 70)
        print("Knowledge + Memory workflow completed successfully.")
        print("=" * 70)


if __name__ == "__main__":
    main()