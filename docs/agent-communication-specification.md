# Agent Communication Specification

**Project:** AgenticOS  
**Document:** Agent Communication Specification  
**Version:** v1.0  
**Status:** Draft  
**Owner:** Agent Platform / Agent Runtime

---

## 1. Purpose

This document defines the communication contract between agents in AgenticOS.

It specifies:

- Agent identity and registration
- Agent capabilities
- Agent Bus messages
- Request and message IDs
- Agent discovery
- Request/response communication
- Errors, timeouts, and retries
- Agent health and heartbeats

The specification is intended to provide a common communication contract
for the Agent Runtime, Agent Bus, Global Agent Manager, Knowledge Layer,
Capability Layer, and specialized agents.

---

## 2. Design Goals

The Agent Communication Layer must provide:

1. Unique identification of agents and requests.
2. Structured communication between agents.
3. Agent registration and discovery.
4. Capability-based agent selection.
5. Request/response communication.
6. Health monitoring.
7. Timeout and retry handling.
8. Traceability across the complete request lifecycle.
9. Extensibility for future AgenticOS versions.

---

## 3. Core Components

The communication system consists of:

### 3.1 Agent

An independently executable component that provides one or more
capabilities.

Examples:

- Planner Agent
- Executor Agent
- Monitor Agent
- Memory Agent
- Security Agent
- Application Agent
- File Agent

### 3.2 Agent Bus

The communication layer responsible for:

- Agent registration
- Agent discovery
- Message routing
- Request delivery
- Response delivery
- Health/heartbeat handling
- Timeout handling
- Retry handling

### 3.3 Agent Registry

The registry maintains information about currently registered agents,
their capabilities, status, and health.

### 3.4 Request

A logical user/system operation that may involve one or more messages
and multiple agents.

### 3.5 Message

A single communication unit transmitted through the Agent Bus.

---

## 4. Agent Identity

Every agent MUST have a unique `agent_id`.

### Proposed Agent Registration Format

```json
{
  "agent_id": "file-agent",
  "name": "File Agent",
  "version": "0.1.0",
  "type": "specialized",
  "status": "active",
  "capabilities": [
    "filesystem.create",
    "filesystem.read",
    "filesystem.list"
  ]
}
### Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `agent_id` | string | Yes | Unique identifier for the agent |
| `name` | string | Yes | Human-readable agent name |
| `version` | string | Yes | Agent version |
| `type` | string | Yes | Agent category |
| `status` | string | Yes | Current agent state |
| `capabilities` | array | Yes | Capabilities provided by the agent |
### Agent Types

Initial agent types may include:

- `core`
- `specialized`
- `system`
## 5. Agent Status

An agent may report one of the following states:

- `starting`
- `active`
- `busy`
- `paused`
- `unhealthy`
- `stopped`
The Agent Bus and Global Agent Manager SHOULD use agent status when selecting agents for work.
---

## 6. Agent Registration

When an agent starts, it registers itself with the Agent Bus.
### Registration Message

{
  "message_id": "msg-000001",
  "request_id": "req-000001",
  "sender": "file-agent",
  "receiver": "agent-bus",
  "message_type": "REGISTER",
  "timestamp": "2026-09-27T10:00:00Z",
  "payload": {
    "agent_id": "file-agent",
    "name": "File Agent",
    "version": "0.1.0",
    "type": "specialized",
    "capabilities": [
      "filesystem.create",
      "filesystem.read"
    ]
  }
}
The Agent Bus adds the agent to the Agent Registry after successful registration.
---

## 7. Agent Unregistration

When an agent shuts down normally, it SHOULD notify the Agent Bus.
### Unregistration Message

{
  "message_id": "msg-000002",
  "request_id": "req-000001",
  "sender": "file-agent",
  "receiver": "agent-bus",
  "message_type": "UNREGISTER",
  "timestamp": "2026-09-27T10:05:00Z",
  "payload": {
    "agent_id": "file-agent"
  }
}
The Agent Bus then removes or marks the agent as unavailable.
---

## 8. Agent Capabilities

A capability describes an operation that an agent can perform.
### Proposed Capability Format

{
  "capability_id": "filesystem.create",
  "name": "Create File or Folder",
  "description": "Creates a file or folder at a permitted filesystem location.",
  "input": {
    "path": "string",
    "type": "file|directory"
  },
  "output": {
    "success": "boolean",
    "path": "string"
  },
  "permissions": [
    "filesystem.write"
  ],
  "risk": "low"
}
### Capability Fields

| Field | Description |
|---|---|
| `capability_id` | Unique capability identifier |
| `name` | Human-readable capability name |
| `description` | What the capability does |
| `input` | Required input structure |
| `output` | Expected output structure |
| `permissions` | Permissions required |
| `risk` | Risk classification |
Capabilities will later be used by the Global Agent Manager and Capability Layer to select an appropriate agent/tool.
---

## 9. Message Envelope

All Agent Bus communication SHOULD use a common message envelope.
### Message Format
{
  "message_id": "msg-000123",
  "request_id": "req-000045",
  "sender": "planner-agent",
  "receiver": "file-agent",
  "message_type": "REQUEST",
  "timestamp": "2026-09-27T10:15:00Z",
  "payload": {}
}
### Message Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `message_id` | string | Yes | Unique ID for this message |
| `request_id` | string | Yes | ID of the overall operation |
| `sender` | string | Yes | Sending agent |
| `receiver` | string | Yes | Receiving agent |
| `message_type` | string | Yes | Type of communication |
| `timestamp` | string | Yes | Message creation time |
| `payload` | object | Yes | Message-specific data |
---

## 10. Message ID vs Request ID

These identifiers serve different purposes.

### Message ID

Identifies one specific message.

Example:

`msg-000123`

### Request ID

Identifies the complete operation.

Example:

`req-000045`

One request may contain multiple messages:

    req-000045
        |
        +-- msg-000123  Planner → Application Agent
        |
        +-- msg-000124  Application Agent → Linux Service
        |
        +-- msg-000125  Linux Service → Application Agent
        |
        +-- msg-000126  Application Agent → Planner

This allows the complete operation to be traced.

---

## 11. Message Types

The initial Agent Bus protocol defines:

- `REGISTER`
- `UNREGISTER`
- `HEARTBEAT`
- `REQUEST`
- `RESPONSE`
- `EVENT`
- `ERROR`

### REGISTER

Used when an agent joins the Agent Bus.

### UNREGISTER

Used when an agent leaves the Agent Bus.

### HEARTBEAT

Used to report agent health/aliveness.

### REQUEST

Used to request an operation from another agent.

### RESPONSE

Used to return the result of a request.

### EVENT

Used for asynchronous notifications.

### ERROR

Used to report communication or execution errors.

---

## 12. Request Message

Example:

{
  "message_id": "msg-000200",
  "request_id": "req-000100",
  "sender": "planner-agent",
  "receiver": "application-agent",
  "message_type": "REQUEST",
  "timestamp": "2026-09-27T10:20:00Z",
  "payload": {
    "action": "launch_application",
    "application": "chrome"
  }
}

---

## 13. Response Message

Successful response:

{
  "message_id": "msg-000201",
  "request_id": "req-000100",
  "sender": "application-agent",
  "receiver": "planner-agent",
  "message_type": "RESPONSE",
  "timestamp": "2026-09-27T10:20:02Z",
  "payload": {
    "status": "success",
    "result": {
      "application": "chrome",
      "state": "running"
    }
  }
}

---

## 14. Error Message

{
  "message_id": "msg-000202",
  "request_id": "req-000100",
  "sender": "application-agent",
  "receiver": "planner-agent",
  "message_type": "ERROR",
  "timestamp": "2026-09-27T10:20:02Z",
  "payload": {
    "error_code": "APPLICATION_NOT_FOUND",
    "message": "Requested application was not found.",
    "retryable": false
  }
}

---

## 15. Heartbeat

Agents SHOULD periodically send heartbeat information to the Agent Bus.

{
  "message_id": "msg-000300",
  "request_id": "req-system",
  "sender": "file-agent",
  "receiver": "agent-bus",
  "message_type": "HEARTBEAT",
  "timestamp": "2026-09-27T10:25:00Z",
  "payload": {
    "agent_id": "file-agent",
    "status": "active"
  }
}

If an agent stops responding to heartbeats, the Agent Bus SHOULD mark the agent as unhealthy or unavailable.

---

## 16. Agent Discovery

The Agent Bus maintains a live registry of agents.

A discovery operation SHOULD support capability-based lookup.

Example:

Find agent capable of:

`filesystem.create`

Possible result:

{
  "capability": "filesystem.create",
  "agents": [
    {
      "agent_id": "file-agent",
      "status": "active"
    }
  ]
}

---

## 17. Message Routing

The Agent Bus is responsible for routing messages.

Basic flow:

    Sender Agent
         |
         v
      Agent Bus
         |
         +--> Validate message
         |
         +--> Identify receiver
         |
         +--> Check receiver availability
         |
         +--> Deliver message
         |
         v
    Receiver Agent

The Agent Bus SHOULD reject malformed messages and unavailable receivers.

---

## 18. Timeout and Retry

If a request does not receive a response within its configured timeout:

1. The Agent Bus records the timeout.
2. The request is marked as failed or retryable.
3. A retry MAY be attempted if the request is retryable.
4. If retries are exhausted, an `ERROR` message is returned.

Example error:

{
  "error_code": "AGENT_TIMEOUT",
  "message": "Target agent did not respond within the configured timeout.",
  "retryable": true
}

---

## 19. Authorization

Before an agent performs a capability, the request SHOULD be checked against the required permissions.

Example:

    Request
       |
       v
    Capability
       |
       v
    Permission Check
       |
       +---- denied ----> ERROR
       |
       v
    Execute

The Security Agent and Capability Layer will provide the broader authorization and capability restrictions.

---

## 20. Request Traceability

Every operation MUST retain its `request_id` across agent communication.

Example:

    User
     |
     v
    LLM
     |
     v
    Intent
     |
     v
    Goal
     |
     v
    Workflow
     |
     v
    Global Agent Manager
     |
     v
    Application Agent
     |
     v
    Linux/System Service
     |
     v
    Result

All relevant logs SHOULD contain the same request ID so that one operation can be traced across the system.

---

## 21. Initial Agent Bus API

The implementation SHOULD expose the following logical operations:

- `register_agent()`
- `unregister_agent()`
- `discover_agents()`
- `send_message()`
- `route_message()`
- `handle_response()`
- `handle_timeout()`
- `retry_message()`
- `heartbeat()`

The exact programming-language API is implementation-specific.

---

## 22. Example End-to-End Communication

User request:

`Open Chrome`

The intended communication sequence is:

    User
      |
      v
    LLM / Intent Intelligence
      |
      v
    Goal
      |
      v
    Global Agent Manager
      |
      v
    Discover capability:
    application.launch
      |
      v
    Application Agent
      |
      v
    System Service / Linux
      |
      v
    Chrome
      |
      v
    Verification
      |
      v
    Result

All agent messages involved in the operation carry the same:

`request_id`

while each individual message receives a unique:

`message_id`

---

## 23. Validation Rules

The Agent Bus SHOULD validate:

- `message_id` exists and is unique.
- `request_id` exists.
- `sender` exists.
- `receiver` exists for directed messages.
- `message_type` is supported.
- `timestamp` is valid.
- `payload` matches the message type.
- Registered agents have valid identities.
- Requested capabilities exist.
- Required permissions are available.

Malformed messages SHOULD generate an `ERROR` response.

---

## 24. Initial v0.1 Scope

The initial AgenticOS v0.1 implementation should focus on:

- Agent registration
- Agent discovery
- Agent-to-agent messaging
- Request/response communication
- Agent capabilities
- Heartbeats/health
- Request IDs
- Message IDs
- Basic timeout handling
- Basic retry handling
- Capability-based routing

More advanced communication mechanisms may be added in later versions.

---

## 25. Status

**Version:** 1.0  
**Status:** Draft for team review

This document is the proposed communication contract for the AgenticOS Agent Runtime and Agent Bus implementation.