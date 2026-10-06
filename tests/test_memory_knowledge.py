from src.agents.memory_agent import MemoryAgent
from src.knowledge.episodic_store import EpisodicMemoryStore
from src.knowledge.vector_store import VectorStore


def create_memory_agent(tmp_path):
    episodic_store = EpisodicMemoryStore(
        tmp_path / "episodic.json"
    )

    vector_store = VectorStore(
        tmp_path / "vectors.json"
    )

    return MemoryAgent(
        episodic_store=episodic_store,
        vector_store=vector_store,
    )


def test_store_and_retrieve_memory(tmp_path):
    agent = create_memory_agent(tmp_path)

    result = agent.remember(
        memory_id="memory-1",
        content="AgenticOS uses an Agent Bus for communication.",
        metadata={"source": "test"},
    )

    assert result["status"] == "stored"

    retrieved = agent.retrieve("memory-1")

    assert retrieved["status"] == "found"
    assert (
        retrieved["memory"]["content"]
        == "AgenticOS uses an Agent Bus for communication."
    )


def test_memory_persists_to_disk(tmp_path):
    episodic_path = tmp_path / "episodic.json"
    vector_path = tmp_path / "vectors.json"

    agent = MemoryAgent(
        episodic_store=EpisodicMemoryStore(episodic_path),
        vector_store=VectorStore(vector_path),
    )

    agent.remember(
        memory_id="persistent-1",
        content="Persistent AgenticOS memory.",
    )

    new_agent = MemoryAgent(
        episodic_store=EpisodicMemoryStore(episodic_path),
        vector_store=VectorStore(vector_path),
    )

    result = new_agent.retrieve("persistent-1")

    assert result["memory"]["content"] == (
        "Persistent AgenticOS memory."
    )


def test_vector_search(tmp_path):
    agent = create_memory_agent(tmp_path)

    agent.remember(
        memory_id="memory-browser",
        content="The Application Agent can open a web browser.",
    )

    agent.remember(
        memory_id="memory-file",
        content="The File Agent creates and reads files.",
    )

    results = agent.search(
        query="open web browser",
        top_k=2,
    )

    assert len(results) == 2
    assert results[0]["memory_id"] == "memory-browser"


def test_delete_memory(tmp_path):
    agent = create_memory_agent(tmp_path)

    agent.remember(
        memory_id="delete-me",
        content="This memory should be deleted.",
    )

    result = agent.delete("delete-me")

    assert result["status"] == "deleted"
    assert result["episodic_deleted"] is True
    assert result["vector_deleted"] is True

    assert agent.verify_deleted("delete-me") is True


def test_clear_memory(tmp_path):
    agent = create_memory_agent(tmp_path)

    agent.remember(
        memory_id="memory-1",
        content="First memory.",
    )

    agent.remember(
        memory_id="memory-2",
        content="Second memory.",
    )

    result = agent.clear()

    assert result["status"] == "cleared"
    assert result["episodic_deleted"] == 2
    assert result["vector_deleted"] == 2
    assert agent.list_memories() == []


def test_memory_agent_handles_remember_message(tmp_path):
    agent = create_memory_agent(tmp_path)

    message = {
        "message_id": "msg-1",
        "request_id": "req-1",
        "message_type": "REQUEST",
        "timestamp": "2026-10-04T10:00:00+00:00",
        "sender": "planner-agent",
        "payload": {
            "operation": "REMEMBER",
            "memory_id": "bus-memory",
            "content": "Remember the AgenticOS project structure.",
        },
    }

    response = agent.receive_message(message)

    assert response["message_type"] == "RESPONSE"
    assert response["payload"]["status"] == "stored"


def test_memory_agent_handles_search_message(tmp_path):
    agent = create_memory_agent(tmp_path)

    agent.remember(
        memory_id="search-memory",
        content="Agent Bus connects AgenticOS components.",
    )

    message = {
        "message_id": "msg-search",
        "request_id": "req-search",
        "message_type": "REQUEST",
        "timestamp": "2026-10-04T10:00:00+00:00",
        "sender": "planner-agent",
        "payload": {
            "operation": "SEARCH_MEMORY",
            "query": "Agent Bus",
            "top_k": 5,
        },
    }

    response = agent.receive_message(message)

    assert response["message_type"] == "RESPONSE"
    assert response["payload"]["status"] == "searched"
    assert len(response["payload"]["results"]) > 0


def test_memory_agent_handles_delete_and_verify(tmp_path):
    agent = create_memory_agent(tmp_path)

    agent.remember(
        memory_id="verify-memory",
        content="This memory will be removed.",
    )

    delete_message = {
        "message_id": "msg-delete",
        "request_id": "req-delete",
        "message_type": "REQUEST",
        "timestamp": "2026-10-04T10:00:00+00:00",
        "sender": "planner-agent",
        "payload": {
            "operation": "DELETE_MEMORY",
            "memory_id": "verify-memory",
        },
    }

    delete_response = agent.receive_message(
        delete_message
    )

    assert delete_response["message_type"] == "RESPONSE"
    assert delete_response["payload"]["status"] == "deleted"

    verify_message = {
        "message_id": "msg-verify",
        "request_id": "req-verify",
        "message_type": "REQUEST",
        "timestamp": "2026-10-04T10:00:00+00:00",
        "sender": "planner-agent",
        "payload": {
            "operation": "VERIFY_MEMORY",
            "memory_id": "verify-memory",
        },
    }

    verify_response = agent.receive_message(
        verify_message
    )

    assert verify_response["message_type"] == "RESPONSE"
    assert verify_response["payload"]["deleted"] is True