from src.capability.connector import FunctionConnector
from src.capability.registry import CapabilityRegistry
from src.capability.service import CapabilityService
from src.capability.skill import Skill, SkillLibrary
from src.capability.tool import Tool


def create_file(filename: str, content: str) -> dict:
    return {
        "filename": filename,
        "content": content,
        "created": True,
    }


def verify_file(filename: str) -> dict:
    return {
        "filename": filename,
        "exists": True,
    }


def main() -> None:
    print("=" * 70)
    print("AgenticOS Capability Layer Demo")
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. Capability Registry
    # ---------------------------------------------------------

    registry = CapabilityRegistry()

    create_tool = Tool(
        tool_id="file-create-tool",
        name="File Creation Tool",
        description="Creates a file.",
        handler=create_file,
        capabilities=["create_file"],
    )

    verify_tool = Tool(
        tool_id="file-verify-tool",
        name="File Verification Tool",
        description="Verifies a file operation.",
        handler=verify_file,
        capabilities=["verify_file"],
    )

    registry.register_tool(create_tool)
    registry.register_tool(verify_tool)

    print("\n[1] Tools registered")
    print(
        "Capabilities:",
        registry.discover_capabilities(),
    )

    # ---------------------------------------------------------
    # 2. Permission Layer
    # ---------------------------------------------------------

    agent_id = "executor-agent"

    registry.grant_permission(
        agent_id=agent_id,
        capability="create_file",
    )

    registry.grant_permission(
        agent_id=agent_id,
        capability="verify_file",
    )

    print("\n[2] Permissions granted")
    print(
        "Agent:",
        agent_id,
    )

    # ---------------------------------------------------------
    # 3. Skill Library
    # ---------------------------------------------------------

    skill_library = SkillLibrary()

    file_management_skill = Skill(
        skill_id="file_management",
        name="File Management",
        description="Create and verify files.",
        capabilities=[
            "create_file",
            "verify_file",
        ],
    )

    skill_library.register_skill(
        file_management_skill
    )

    print("\n[3] Skill registered")
    print(
        "Skills:",
        skill_library.discover_skills(),
    )

    # ---------------------------------------------------------
    # 4. Capability Service
    # ---------------------------------------------------------

    service = CapabilityService(
        registry=registry,
        skill_library=skill_library,
    )

    # ---------------------------------------------------------
    # 5. Connector
    # ---------------------------------------------------------

    connector = FunctionConnector(
        connector_id="local-system",
        name="Local System Connector",
    )

    connector.register_operation(
        "system_verify",
        lambda target: {
            "target": target,
            "system_available": True,
        },
    )

    connector.connect()

    service.register_connector(
        connector
    )

    print("\n[4] Connector registered")
    print(
        "Connectors:",
        service.discover_connectors(),
    )

    # ---------------------------------------------------------
    # 6. Agent → Capability → Permission → Tool
    # ---------------------------------------------------------

    create_result = service.execute_capability(
        agent_id=agent_id,
        capability="create_file",
        filename="AgenticOS.txt",
        content="Capability Layer operational.",
    )

    print("\n[5] Tool execution")
    print(create_result)

    # ---------------------------------------------------------
    # 7. Skill execution
    # ---------------------------------------------------------

    # Each capability receives the same kwargs in this v0.1
    # demonstration, so execute the capabilities individually
    # where their input contracts differ.
    verify_result = service.execute_capability(
        agent_id=agent_id,
        capability="verify_file",
        filename="AgenticOS.txt",
    )

    print("\n[6] Verification")
    print(verify_result)

    # ---------------------------------------------------------
    # 8. Connector execution
    # ---------------------------------------------------------

    connector_result = service.execute_connector(
        agent_id=agent_id,
        capability="verify_file",
        connector_id="local-system",
        operation="system_verify",
        target="AgenticOS.txt",
    )

    print("\n[7] Connector execution")
    print(connector_result)

    # ---------------------------------------------------------
    # 9. Final verification
    # ---------------------------------------------------------

    assert create_result["verified"] is True
    assert verify_result["verified"] is True
    assert connector_result["verified"] is True

    print("\n" + "=" * 70)
    print("Capability Layer workflow completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    main()