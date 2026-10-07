from __future__ import annotations

from typing import Any

from src.agent_runtime.agent import Agent
from src.kernel_intelligence.monitor import ResourceMonitor
from src.kernel_intelligence.scheduler import BoundedScheduler


class KernelIntelligenceAgent(Agent):
    """
    Agent-facing interface for Kernel Intelligence.

    It observes resource state and exposes bounded scheduler-policy operations.
    Actual Linux resource mutation is intentionally delegated to a future
    platform adapter.
    """

    def __init__(
        self,
        agent_id: str = "kernel-intelligence-agent",
        monitor: ResourceMonitor | None = None,
        scheduler: BoundedScheduler | None = None,
    ) -> None:
        super().__init__(
            agent_id=agent_id,
            name="Kernel Intelligence Agent",
            version="0.1.0",
            agent_type="system",
            capabilities=[
                "resource_monitoring",
                "scheduler_policy",
                "policy_recommendation",
                "policy_rollback",
            ],
        )

        self.monitor = monitor or ResourceMonitor()
        self.scheduler = scheduler or BoundedScheduler()

    def snapshot(self) -> dict[str, Any]:
        return self.monitor.collect().to_dict()

    def recommend_policy(
        self,
        workload_id: str = "default",
    ) -> dict[str, Any]:
        snapshot = self.monitor.collect()

        decision = self.scheduler.recommend(
            snapshot,
            workload_id=workload_id,
        )

        return {
            "snapshot": snapshot.to_dict(),
            "decision": decision.to_dict(),
        }

    def apply_policy(
        self,
        workload_id: str,
        decision: Any,
    ) -> dict[str, Any]:
        return self.scheduler.apply(
            workload_id=workload_id,
            decision=decision,
        )

    def rollback_policy(
        self,
        workload_id: str,
    ) -> dict[str, Any]:
        return self.scheduler.rollback(workload_id)

    def receive_message(
        self,
        message: dict[str, Any],
    ) -> dict[str, Any]:
        self.received_messages.append(message)

        operation = message.get("payload", {}).get(
            "operation"
        )

        try:
            if operation == "GET_SNAPSHOT":
                result = self.snapshot()

            elif operation == "RECOMMEND_POLICY":
                result = self.recommend_policy(
                    message.get("payload", {}).get(
                        "workload_id",
                        "default",
                    )
                )

            elif operation == "ROLLBACK_POLICY":
                result = self.rollback_policy(
                    message.get("payload", {}).get(
                        "workload_id",
                        "default",
                    )
                )

            else:
                raise ValueError(
                    f"Unsupported Kernel Intelligence operation: "
                    f"{operation}"
                )

            return {
                "message_id": message.get("message_id"),
                "request_id": message.get("request_id"),
                "sender": self.agent_id,
                "receiver": message.get("sender"),
                "message_type": "RESPONSE",
                "payload": {
                    "status": "success",
                    "operation": operation,
                    "result": result,
                },
            }

        except (TypeError, ValueError, RuntimeError) as exc:
            return {
                "message_id": message.get("message_id"),
                "request_id": message.get("request_id"),
                "sender": self.agent_id,
                "receiver": message.get("sender"),
                "message_type": "ERROR",
                "payload": {
                    "status": "error",
                    "operation": operation,
                    "error": str(exc),
                },
            }
