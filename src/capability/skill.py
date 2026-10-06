from typing import Any


class Skill:
    """
    A higher-level capability composed of one or more capabilities.
    """

    def __init__(
        self,
        skill_id: str,
        name: str,
        description: str,
        capabilities: list[str],
    ):
        if not skill_id.strip():
            raise ValueError("skill_id must be a non-empty string.")

        if not capabilities:
            raise ValueError(
                "A skill must contain at least one capability."
            )

        self.skill_id = skill_id
        self.name = name
        self.description = description
        self.capabilities = list(capabilities)

    def get_registration(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
        }


class SkillLibrary:
    """
    Registry for higher-level AgenticOS skills.
    """

    def __init__(self):
        self.skills: dict[str, Skill] = {}

    def register_skill(
        self,
        skill: Skill,
    ) -> dict[str, Any]:
        if skill.skill_id in self.skills:
            raise ValueError(
                f"Skill '{skill.skill_id}' is already registered."
            )

        self.skills[skill.skill_id] = skill

        return {
            "status": "registered",
            "skill": skill.get_registration(),
        }

    def unregister_skill(
        self,
        skill_id: str,
    ) -> dict[str, Any]:
        if skill_id not in self.skills:
            raise ValueError(
                f"Skill '{skill_id}' is not registered."
            )

        del self.skills[skill_id]

        return {
            "status": "unregistered",
            "skill_id": skill_id,
        }

    def get_skill(
        self,
        skill_id: str,
    ) -> Skill:
        if skill_id not in self.skills:
            raise ValueError(
                f"Skill '{skill_id}' is not registered."
            )

        return self.skills[skill_id]

    def discover_skills(self) -> list[dict[str, Any]]:
        return [
            skill.get_registration()
            for skill in self.skills.values()
        ]

    def resolve_capabilities(
        self,
        skill_id: str,
    ) -> list[str]:
        return list(
            self.get_skill(skill_id).capabilities
        )