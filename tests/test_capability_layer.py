
import pytest

from src.capability.service import CapabilityService
from src.capability.skill import Skill, SkillLibrary
from src.capability.permissions import PermissionManager
from src.capability.registry import CapabilityRegistry
from src.capability.tool import Tool


def add_numbers(a: int, b: int) -> int:
    return a + b


def multiply_numbers(a: int, b: int) -> int:
    return a * b


def test_tool_registration():
    registry = CapabilityRegistry()

    tool = Tool(
        tool_id="calculator",
        name="Calculator",
        description="Performs basic calculations.",
        handler=add_numbers,
        capabilities=["calculate"],
    )

    result = registry.register_tool(tool)

    assert result["status"] == "registered"
    assert result["tool"]["tool_id"] == "calculator"
    assert "calculate" in registry.discover_capabilities()


def test_duplicate_tool_registration_fails():
    registry = CapabilityRegistry()

    tool = Tool(
        tool_id="calculator",
        name="Calculator",
        description="Performs calculations.",
        handler=add_numbers,
        capabilities=["calculate"],
    )

    registry.register_tool(tool)

    try:
        registry.register_tool(tool)
        assert False, "Expected duplicate registration to fail."
    except ValueError as error:
        assert "already registered" in str(error)


def test_capability_resolution():
    registry = CapabilityRegistry()

    tool = Tool(
        tool_id="calculator",
        name="Calculator",
        description="Performs calculations.",
        handler=add_numbers,
        capabilities=["calculate"],
    )

    registry.register_tool(tool)

    resolved = registry.get_tool_for_capability(
        "calculate"
    )

    assert resolved.tool_id == "calculator"


def test_unknown_capability_fails():
    registry = CapabilityRegistry()

    try:
        registry.get_tool_for_capability(
            "does_not_exist"
        )
        assert False, "Expected unknown capability to fail."
    except ValueError as error:
        assert "not registered" in str(error)


def test_permission_manager():
    permissions = PermissionManager()

    assert not permissions.is_allowed(
        "executor-agent",
        "calculate",
    )

    permissions.grant(
        "executor-agent",
        "calculate",
    )

    assert permissions.is_allowed(
        "executor-agent",
        "calculate",
    )

    permissions.revoke(
        "executor-agent",
        "calculate",
    )

    assert not permissions.is_allowed(
        "executor-agent",
        "calculate",
    )


def test_unauthorized_agent_cannot_execute():
    registry = CapabilityRegistry()

    tool = Tool(
        tool_id="calculator",
        name="Calculator",
        description="Performs calculations.",
        handler=add_numbers,
        capabilities=["calculate"],
    )

    registry.register_tool(tool)

    try:
        registry.execute(
            agent_id="executor-agent",
            capability="calculate",
            a=2,
            b=3,
        )
        assert False, "Expected permission denial."
    except PermissionError as error:
        assert "not authorized" in str(error)


def test_authorized_agent_executes_tool():
    registry = CapabilityRegistry()

    tool = Tool(
        tool_id="calculator",
        name="Calculator",
        description="Performs calculations.",
        handler=add_numbers,
        capabilities=["calculate"],
    )

    registry.register_tool(tool)

    registry.grant_permission(
        agent_id="executor-agent",
        capability="calculate",
    )

    result = registry.execute(
        agent_id="executor-agent",
        capability="calculate",
        a=2,
        b=3,
    )

    assert result["status"] == "completed"
    assert result["agent_id"] == "executor-agent"
    assert result["capability"] == "calculate"
    assert result["tool_id"] == "calculator"
    assert result["result"] == 5
    assert result["verified"] is True


def test_multiple_tools_and_capabilities():
    registry = CapabilityRegistry()

    calculator = Tool(
        tool_id="calculator",
        name="Calculator",
        description="Adds numbers.",
        handler=add_numbers,
        capabilities=["calculate"],
    )

    multiplier = Tool(
        tool_id="multiplier",
        name="Multiplier",
        description="Multiplies numbers.",
        handler=multiply_numbers,
        capabilities=["multiply"],
    )

    registry.register_tool(calculator)
    registry.register_tool(multiplier)

    registry.grant_permission(
        "executor-agent",
        "calculate",
    )

    registry.grant_permission(
        "executor-agent",
        "multiply",
    )

    addition = registry.execute(
        agent_id="executor-agent",
        capability="calculate",
        a=4,
        b=6,
    )

    multiplication = registry.execute(
        agent_id="executor-agent",
        capability="multiply",
        a=4,
        b=6,
    )

    assert addition["result"] == 10
    assert multiplication["result"] == 24


def test_permission_revocation_blocks_execution():
    registry = CapabilityRegistry()

    tool = Tool(
        tool_id="calculator",
        name="Calculator",
        description="Performs calculations.",
        handler=add_numbers,
        capabilities=["calculate"],
    )

    registry.register_tool(tool)

    registry.grant_permission(
        "executor-agent",
        "calculate",
    )

    registry.revoke_permission(
        "executor-agent",
        "calculate",
    )

    try:
        registry.execute(
            agent_id="executor-agent",
            capability="calculate",
            a=5,
            b=5,
        )
        assert False, "Expected permission denial."
    except PermissionError:
        pass


def test_tool_unregister_removes_capabilities():
    registry = CapabilityRegistry()

    tool = Tool(
        tool_id="calculator",
        name="Calculator",
        description="Performs calculations.",
        handler=add_numbers,
        capabilities=["calculate"],
    )

    registry.register_tool(tool)

    result = registry.unregister_tool(
        "calculator"
    )

    assert result["status"] == "unregistered"
    assert "calculate" not in registry.discover_capabilities()

    try:
        registry.get_tool_for_capability(
            "calculate"
        )
        assert False, "Expected capability to be removed."
    except ValueError:
        pass

def test_capability_audit_records_success():
    registry = CapabilityRegistry()
    tool = Tool(
        tool_id="calculator",
        name="Calculator",
        description="Adds two numbers.",
        handler=add_numbers,
        capabilities=["calculate"],
    )
    registry.register_tool(tool)
    registry.grant_permission("executor-agent", "calculate")

    result = registry.execute(
        agent_id="executor-agent",
        capability="calculate",
        a=2,
        b=3,
    )

    assert result["result"] == 5
    events = registry.get_audit_log()
    assert len(events) == 1
    assert events[0]["outcome"] == "success"
    assert events[0]["agent_id"] == "executor-agent"
    assert events[0]["capability"] == "calculate"
    assert events[0]["tool_id"] == "calculator"


def test_capability_audit_records_denial_with_request_id():
    registry = CapabilityRegistry()
    registry.register_tool(
        Tool(
            tool_id="calculator",
            name="Calculator",
            description="Adds two numbers.",
            handler=add_numbers,
            capabilities=["calculate"],
        )
    )

    with pytest.raises(PermissionError):
        registry.execute(
            agent_id="untrusted-agent",
            capability="calculate",
            request_id="req-security-denied",
            a=2,
            b=3,
        )

    events = registry.get_audit_log("req-security-denied")
    assert len(events) == 1
    assert events[0]["outcome"] == "denied"
    assert events[0]["error_type"] == "PermissionError"


def test_skill_preflight_prevents_partial_execution():
    registry = CapabilityRegistry()
    executed = []

    registry.register_tool(
        Tool(
            tool_id="first-tool",
            name="First tool",
            description="Records the first operation.",
            handler=lambda: executed.append("first"),
            capabilities=["first_capability"],
        )
    )
    registry.register_tool(
        Tool(
            tool_id="second-tool",
            name="Second tool",
            description="Records the second operation.",
            handler=lambda: executed.append("second"),
            capabilities=["second_capability"],
        )
    )

    registry.grant_permission("executor-agent", "first_capability")

    skills = SkillLibrary()
    skills.register_skill(
        Skill(
            skill_id="two-step-skill",
            name="Two-step skill",
            description="Requires two capabilities.",
            capabilities=["first_capability", "second_capability"],
        )
    )
    service = CapabilityService(registry, skills)

    with pytest.raises(PermissionError):
        service.execute_skill(
            agent_id="executor-agent",
            skill_id="two-step-skill",
        )

    assert executed == []

def test_skill_permission_denial_is_audited():
    registry = CapabilityRegistry()

    registry.register_tool(
        Tool(
            tool_id="private-tool",
            name="Private tool",
            description="A tool requiring explicit permission.",
            handler=lambda: "executed",
            capabilities=["private_capability"],
        )
    )

    skills = SkillLibrary()
    skills.register_skill(
        Skill(
            skill_id="private-skill",
            name="Private skill",
            description="Requires private access.",
            capabilities=["private_capability"],
        )
    )

    service = CapabilityService(registry, skills)

    with pytest.raises(PermissionError):
        service.execute_skill(
            agent_id="untrusted-agent",
            skill_id="private-skill",
            request_id="req-skill-denied",
        )

    events = registry.get_audit_log("req-skill-denied")

    assert len(events) == 1
    assert events[0]["outcome"] == "denied"
    assert events[0]["agent_id"] == "untrusted-agent"
    assert events[0]["capability"] == "private_capability"
    assert events[0]["tool_id"] == "private-tool"
    assert events[0]["error_type"] == "PermissionError"

from src.capability.connector import FunctionConnector


def test_connector_permission_denial_is_audited():
    registry = CapabilityRegistry()
    registry.register_tool(
        Tool(
            tool_id="system-tool",
            name="System tool",
            description="Represents an authorized connector capability.",
            handler=lambda: "ok",
            capabilities=["system.read"],
        )
    )

    skills = SkillLibrary()
    service = CapabilityService(registry, skills)

    connector = FunctionConnector(
        connector_id="system-connector",
        name="System connector",
    )
    connector.register_operation(
        "read",
        lambda: "secret",
    )
    connector.connect()
    service.register_connector(connector)

    with pytest.raises(PermissionError):
        service.execute_connector(
            agent_id="untrusted-agent",
            connector_id="system-connector",
            capability="system.read",
            operation="read",
            request_id="req-connector-denied",
        )

    events = registry.get_audit_log("req-connector-denied")

    assert len(events) == 1
    assert events[0]["outcome"] == "denied"
    assert events[0]["agent_id"] == "untrusted-agent"
    assert events[0]["capability"] == "system.read"
    assert events[0]["tool_id"] == "system-tool"
    assert events[0]["error_type"] == "PermissionError"


def test_connector_execution_failure_is_audited():
    registry = CapabilityRegistry()
    registry.register_tool(
        Tool(
            tool_id="system-tool",
            name="System tool",
            description="Represents a connector capability.",
            handler=lambda: "ok",
            capabilities=["system.read"],
        )
    )
    registry.grant_permission("executor-agent", "system.read")

    service = CapabilityService(registry, SkillLibrary())

    connector = FunctionConnector(
        connector_id="system-connector",
        name="System connector",
    )

    def fail_operation(**kwargs):
        raise RuntimeError("connector operation failed")

    connector.register_operation("read", fail_operation)
    connector.connect()
    service.register_connector(connector)

    with pytest.raises(RuntimeError, match="connector operation failed"):
        service.execute_connector(
            agent_id="executor-agent",
            connector_id="system-connector",
            capability="system.read",
            operation="read",
            request_id="req-connector-failure",
        )

    events = registry.get_audit_log("req-connector-failure")

    assert len(events) == 1
    assert events[0]["outcome"] == "failed"
    assert events[0]["agent_id"] == "executor-agent"
    assert events[0]["capability"] == "system.read"
    assert events[0]["tool_id"] == "system-tool"
    assert events[0]["error_type"] == "RuntimeError"

def test_connector_request_id_is_not_forwarded_to_operation():
    registry = CapabilityRegistry()
    registry.register_tool(
        Tool(
            tool_id="system-tool",
            name="System tool",
            description="Represents a connector capability.",
            handler=lambda: "ok",
            capabilities=["system.read"],
        )
    )
    registry.grant_permission("executor-agent", "system.read")

    service = CapabilityService(registry, SkillLibrary())
    connector = FunctionConnector(
        connector_id="system-connector",
        name="System connector",
    )

    received = {}

    def read_operation(path):
        received["path"] = path
        return "read complete"

    connector.register_operation("read", read_operation)
    connector.connect()
    service.register_connector(connector)

    result = service.execute_connector(
        agent_id="executor-agent",
        connector_id="system-connector",
        capability="system.read",
        operation="read",
        path="/tmp/example.txt",
        request_id="req-connector-arguments",
    )

    assert received == {"path": "/tmp/example.txt"}
    assert result["result"] == "read complete"

    events = registry.get_audit_log("req-connector-arguments")
    assert len(events) == 1
    assert events[0]["outcome"] == "success"