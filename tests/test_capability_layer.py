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