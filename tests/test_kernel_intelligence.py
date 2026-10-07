from src.agent_bus.bus import AgentBus
from src.kernel_intelligence.agent import KernelIntelligenceAgent
from src.kernel_intelligence.monitor import ResourceMonitor
from src.kernel_intelligence.scheduler import (
    BoundedScheduler,
    PolicyAction,
    PolicyDecision,
)


def test_resource_monitor_injected_provider():
    monitor = ResourceMonitor(
        provider=lambda: {
            "timestamp": 123.0,
            "platform": "TestOS",
            "logical_cpus": 8,
            "cpu_percent": 42.5,
            "memory_total_mb": 16000,
            "memory_available_mb": 8000,
            "memory_percent": 50.0,
            "load_average": [1.0, 2.0, 3.0],
        }
    )

    snapshot = monitor.collect()

    assert snapshot.timestamp == 123.0
    assert snapshot.platform == "TestOS"
    assert snapshot.logical_cpus == 8
    assert snapshot.cpu_percent == 42.5
    assert snapshot.memory_total_mb == 16000
    assert snapshot.memory_available_mb == 8000
    assert snapshot.memory_percent == 50.0
    assert snapshot.load_average == (1.0, 2.0, 3.0)


def test_resource_snapshot_to_dict():
    monitor = ResourceMonitor(
        provider=lambda: {
            "platform": "TestOS",
            "logical_cpus": 4,
            "cpu_percent": 20,
            "memory_total_mb": 8000,
            "memory_available_mb": 6000,
            "memory_percent": 25,
            "load_average": [0.5, 0.4, 0.3],
        }
    )

    result = monitor.collect().to_dict()

    assert result["platform"] == "TestOS"
    assert result["logical_cpus"] == 4
    assert result["cpu_percent"] == 20.0
    assert result["memory_percent"] == 25.0


def test_scheduler_no_change_under_normal_load():
    monitor = ResourceMonitor(
        provider=lambda: {
            "cpu_percent": 40,
            "memory_percent": 50,
        }
    )

    snapshot = monitor.collect()
    scheduler = BoundedScheduler()

    decision = scheduler.recommend(snapshot)

    assert decision.status == "no_change"
    assert decision.actions == ()
    assert decision.reversible is True


def test_scheduler_recommends_cpu_limit_under_high_cpu():
    monitor = ResourceMonitor(
        provider=lambda: {
            "cpu_percent": 95,
            "memory_percent": 50,
        }
    )

    scheduler = BoundedScheduler()
    decision = scheduler.recommend(
        monitor.collect(),
        workload_id="compile-job",
    )

    assert decision.status == "recommended"
    assert len(decision.actions) == 1
    assert decision.actions[0].action == "set_cpu_limit"
    assert decision.actions[0].value == 80.0


def test_scheduler_recommends_memory_limit_under_high_memory():
    monitor = ResourceMonitor(
        provider=lambda: {
            "cpu_percent": 50,
            "memory_percent": 95,
        }
    )

    scheduler = BoundedScheduler()
    decision = scheduler.recommend(
        monitor.collect(),
        workload_id="memory-job",
    )

    assert decision.status == "recommended"
    assert len(decision.actions) == 1
    assert decision.actions[0].action == "set_memory_limit"
    assert decision.actions[0].value == 512


def test_scheduler_can_recommend_both_cpu_and_memory_limits():
    monitor = ResourceMonitor(
        provider=lambda: {
            "cpu_percent": 95,
            "memory_percent": 95,
        }
    )

    scheduler = BoundedScheduler()
    decision = scheduler.recommend(monitor.collect())

    actions = {
        action.action: action.value
        for action in decision.actions
    }

    assert actions == {
        "set_cpu_limit": 80.0,
        "set_memory_limit": 512,
    }


def test_scheduler_rejects_unknown_action():
    scheduler = BoundedScheduler()

    action = PolicyAction(
        action="disable_machine",
        value=True,
    )

    try:
        scheduler.validate_action(action)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Unsupported policy action" in str(exc)


def test_scheduler_rejects_cpu_limit_above_bound():
    scheduler = BoundedScheduler()

    action = PolicyAction(
        action="set_cpu_limit",
        value=150,
    )

    try:
        scheduler.validate_action(action)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "between 1 and 100" in str(exc)


def test_scheduler_rejects_cpu_limit_below_bound():
    scheduler = BoundedScheduler()

    action = PolicyAction(
        action="set_cpu_limit",
        value=0,
    )

    try:
        scheduler.validate_action(action)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "between 1 and 100" in str(exc)


def test_scheduler_rejects_memory_limit_below_bound():
    scheduler = BoundedScheduler()

    action = PolicyAction(
        action="set_memory_limit",
        value=1,
    )

    try:
        scheduler.validate_action(action)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "outside the allowed bounds" in str(exc)


def test_scheduler_dry_run_does_not_apply_policy():
    scheduler = BoundedScheduler(dry_run=True)

    decision = PolicyDecision(
        status="recommended",
        actions=(
            PolicyAction(
                action="set_cpu_limit",
                value=80,
                reason="test",
            ),
        ),
        reason="test policy",
    )

    result = scheduler.apply(
        workload_id="test-workload",
        decision=decision,
    )

    assert result["dry_run"] is True
    assert result["execution"] == "simulated"
    assert scheduler.get_policy("test-workload") is None


def test_scheduler_apply_and_rollback():
    scheduler = BoundedScheduler(dry_run=False)

    decision = PolicyDecision(
        status="recommended",
        actions=(
            PolicyAction(
                action="set_cpu_limit",
                value=80,
                reason="test",
            ),
        ),
        reason="test policy",
    )

    result = scheduler.apply(
        workload_id="test-workload",
        decision=decision,
    )

    assert result["status"] == "recommended"
    assert scheduler.get_policy("test-workload") is not None

    rollback = scheduler.rollback("test-workload")

    assert rollback["status"] == "rolled_back"
    assert rollback["had_policy"] is True
    assert scheduler.get_policy("test-workload") is None


def test_kernel_intelligence_agent_snapshot():
    monitor = ResourceMonitor(
        provider=lambda: {
            "platform": "TestOS",
            "logical_cpus": 8,
            "cpu_percent": 35,
            "memory_percent": 40,
        }
    )

    agent = KernelIntelligenceAgent(
        monitor=monitor,
    )

    agent.start()

    snapshot = agent.snapshot()

    assert snapshot["platform"] == "TestOS"
    assert snapshot["logical_cpus"] == 8
    assert snapshot["cpu_percent"] == 35.0


def test_kernel_intelligence_agent_recommendation():
    monitor = ResourceMonitor(
        provider=lambda: {
            "cpu_percent": 95,
            "memory_percent": 50,
        }
    )

    agent = KernelIntelligenceAgent(
        monitor=monitor,
    )

    agent.start()

    result = agent.recommend_policy(
        workload_id="test-workload",
    )

    assert result["decision"]["status"] == "recommended"
    assert result["decision"]["actions"][0]["action"] == (
        "set_cpu_limit"
    )


def test_kernel_intelligence_agent_bus_snapshot():
    bus = AgentBus()

    sender = KernelIntelligenceAgent(
        agent_id="sender-agent",
        monitor=ResourceMonitor(
            provider=lambda: {
                "cpu_percent": 30,
                "memory_percent": 40,
            }
        ),
    )

    receiver = KernelIntelligenceAgent(
        agent_id="kernel-agent",
        monitor=ResourceMonitor(
            provider=lambda: {
                "platform": "TestOS",
                "logical_cpus": 8,
                "cpu_percent": 30,
                "memory_percent": 40,
            }
        ),
    )

    sender.start()
    receiver.start()

    bus.register_agent(sender)
    bus.register_agent(receiver)

    response = sender.send_message(
        bus=bus,
        receiver_id="kernel-agent",
        message={
            "message_id": "kernel-msg-001",
            "request_id": "kernel-request-001",
            "message_type": "REQUEST",
            "timestamp": "2026-10-07T09:00:00+00:00",
            "payload": {
                "operation": "GET_SNAPSHOT",
            },
        },
    )

    assert response["message_type"] == "RESPONSE"
    assert response["request_id"] == "kernel-request-001"
    assert response["payload"]["status"] == "success"
    assert response["payload"]["result"]["platform"] == "TestOS"


def test_kernel_intelligence_agent_bus_recommendation():
    bus = AgentBus()

    sender = KernelIntelligenceAgent(
        agent_id="sender-agent",
    )

    receiver = KernelIntelligenceAgent(
        agent_id="kernel-agent",
        monitor=ResourceMonitor(
            provider=lambda: {
                "cpu_percent": 95,
                "memory_percent": 50,
            }
        ),
    )

    sender.start()
    receiver.start()

    bus.register_agent(sender)
    bus.register_agent(receiver)

    response = sender.send_message(
        bus=bus,
        receiver_id="kernel-agent",
        message={
            "message_id": "kernel-msg-002",
            "request_id": "kernel-request-002",
            "message_type": "REQUEST",
            "timestamp": "2026-10-07T09:00:00+00:00",
            "payload": {
                "operation": "RECOMMEND_POLICY",
                "workload_id": "compile-job",
            },
        },
    )

    assert response["message_type"] == "RESPONSE"
    assert response["payload"]["status"] == "success"

    decision = response["payload"]["result"]["decision"]

    assert decision["status"] == "recommended"
    assert decision["actions"][0]["action"] == "set_cpu_limit"


def test_kernel_intelligence_agent_rejects_unknown_operation():
    agent = KernelIntelligenceAgent()
    agent.start()

    response = agent.receive_message(
        {
            "message_id": "kernel-msg-003",
            "request_id": "kernel-request-003",
            "message_type": "REQUEST",
            "sender": "test-agent",
            "payload": {
                "operation": "FORMAT_DISK",
            },
        }
    )

    assert response["message_type"] == "ERROR"
    assert response["payload"]["status"] == "error"
    assert "Unsupported Kernel Intelligence operation" in (
        response["payload"]["error"]
    )
