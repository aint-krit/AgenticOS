from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class PolicyAction:
    action: str
    value: float | int | bool | None = None
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PolicyDecision:
    status: str
    actions: tuple[PolicyAction, ...]
    reason: str
    reversible: bool = True

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["actions"] = [
            action.to_dict()
            for action in self.actions
        ]
        return result


class BoundedScheduler:
    """
    Safe scheduler-policy interface.

    This class does not replace Linux CFS and does not directly modify the
    host scheduler. It validates bounded resource policies and maintains the
    requested policy state. A future Linux adapter can translate these
    validated actions into cgroups/systemd operations.
    """

    ALLOWED_ACTIONS = {
        "set_cpu_limit",
        "set_memory_limit",
        "pause_workload",
        "resume_workload",
    }

    MAX_CPU_PERCENT = 100.0
    MIN_CPU_PERCENT = 1.0

    MAX_MEMORY_MB = 1024 * 1024
    MIN_MEMORY_MB = 16

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run
        self.applied_policies: dict[str, dict[str, Any]] = {}

    def recommend(
        self,
        snapshot: Any,
        workload_id: str = "default",
    ) -> PolicyDecision:
        cpu = getattr(snapshot, "cpu_percent", None)
        memory = getattr(snapshot, "memory_percent", None)

        actions: list[PolicyAction] = []

        if cpu is not None and cpu >= 90.0:
            actions.append(
                PolicyAction(
                    action="set_cpu_limit",
                    value=80.0,
                    reason="High CPU utilization detected.",
                )
            )

        if memory is not None and memory >= 90.0:
            actions.append(
                PolicyAction(
                    action="set_memory_limit",
                    value=512,
                    reason="High memory utilization detected.",
                )
            )

        if not actions:
            return PolicyDecision(
                status="no_change",
                actions=(),
                reason="Resource utilization is within configured limits.",
            )

        return PolicyDecision(
            status="recommended",
            actions=tuple(actions),
            reason=(
                f"Bounded policy recommendation generated for "
                f"workload '{workload_id}'."
            ),
        )

    def validate_action(
        self,
        action: PolicyAction,
    ) -> None:
        if action.action not in self.ALLOWED_ACTIONS:
            raise ValueError(
                f"Unsupported policy action: {action.action}"
            )

        if action.action == "set_cpu_limit":
            if not isinstance(action.value, (int, float)):
                raise ValueError(
                    "CPU limit must be numeric."
                )

            value = float(action.value)

            if not (
                self.MIN_CPU_PERCENT
                <= value
                <= self.MAX_CPU_PERCENT
            ):
                raise ValueError(
                    "CPU limit must be between 1 and 100 percent."
                )

        if action.action == "set_memory_limit":
            if not isinstance(action.value, (int, float)):
                raise ValueError(
                    "Memory limit must be numeric."
                )

            value = int(action.value)

            if not (
                self.MIN_MEMORY_MB
                <= value
                <= self.MAX_MEMORY_MB
            ):
                raise ValueError(
                    "Memory limit is outside the allowed bounds."
                )

        if action.action in {
            "pause_workload",
            "resume_workload",
        }:
            if action.value not in (None, True, False):
                raise ValueError(
                    f"{action.action} does not accept an arbitrary value."
                )

    def apply(
        self,
        workload_id: str,
        decision: PolicyDecision,
    ) -> dict[str, Any]:
        if not workload_id or not workload_id.strip():
            raise ValueError(
                "workload_id must be a non-empty string."
            )

        if decision.status not in {
            "recommended",
            "no_change",
        }:
            raise ValueError(
                f"Unsupported policy decision status: {decision.status}"
            )

        for action in decision.actions:
            self.validate_action(action)

        policy = {
            "workload_id": workload_id,
            "status": decision.status,
            "dry_run": self.dry_run,
            "reversible": decision.reversible,
            "actions": [
                action.to_dict()
                for action in decision.actions
            ],
            "reason": decision.reason,
        }

        if not self.dry_run:
            self.applied_policies[workload_id] = policy
        else:
            policy["execution"] = "simulated"

        return policy

    def rollback(
        self,
        workload_id: str,
    ) -> dict[str, Any]:
        if not workload_id or not workload_id.strip():
            raise ValueError(
                "workload_id must be a non-empty string."
            )

        previous = self.applied_policies.pop(
            workload_id,
            None,
        )

        return {
            "workload_id": workload_id,
            "status": "rolled_back",
            "had_policy": previous is not None,
            "reversible": True,
        }

    def get_policy(
        self,
        workload_id: str,
    ) -> dict[str, Any] | None:
        return self.applied_policies.get(workload_id)
