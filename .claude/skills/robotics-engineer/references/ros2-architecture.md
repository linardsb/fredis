# ROS2 Architecture Primer

## Core abstractions

- **Node** — an executable that performs computation. Usually one node per logical concern (driver, controller, planner).
- **Topic** — async pub/sub channel. Multiple publishers, multiple subscribers. Best for continuous data (sensor streams, odometry, TF frames).
- **Service** — synchronous request/response. One server per service name. Best for stateless queries (get map, query parameter).
- **Action** — long-running goal with feedback and result. Best for "do this and tell me when you're done or how far along" semantics (navigate to waypoint, execute trajectory).
- **Parameter** — named runtime value per node; supports declare, get, set with callbacks on change.

## Quality-of-Service (QoS) profiles

ROS2 requires explicit QoS choice. Key settings:

- **Reliability** — `reliable` (retransmit on loss) vs `best_effort` (drop on loss). Sensor streams usually best_effort; control commands usually reliable.
- **Durability** — `volatile` (no history kept) vs `transient_local` (late joiners get the last N messages). Static map → transient_local. Velocity commands → volatile.
- **History** — `keep_last N` vs `keep_all`. Almost always keep_last.
- **Deadline** — publisher must publish within T or event fires.
- **Liveliness** — declares who is responsible for signalling alive (automatic / manual_by_topic).

QoS profiles between publisher and subscriber must be *compatible* (not identical) for messages to flow. A subscriber with reliable+transient_local can receive from publishers with any equal-or-stronger settings.

## Lifecycle nodes

Managed state machine: `unconfigured → inactive → active → finalized`. Useful for drivers and controllers that need ordered startup/shutdown (e.g., "don't activate planner until map server is active").

## Composition

Nodes can run as separate processes (standard) or composed into one process for intra-process zero-copy messaging (low-latency control loops).

## Typical architecture pattern

```
sensor_drivers (nodes, publishing topics)
    ↓
perception (nodes subscribing to sensors, publishing features/state)
    ↓
planning (nodes subscribing to state, publishing goals via actions)
    ↓
control (lifecycle nodes subscribing to goals, publishing commands)
    ↓
actuators (drivers, subscribing to commands)
```

With cross-cutting concerns:
- `tf2` transform tree (topic-based, transient_local for static TF)
- Parameter server (per-node, supports remote get/set)
- Diagnostics (standard `/diagnostics` topic)

## Common anti-patterns

- Using topics for request/response (use services).
- Using services for long-running work (use actions).
- Using reliable QoS on high-rate sensor data (network pressure).
- Using volatile+keep_last_1 for configuration (late subscribers miss the value).
- One god-node that does sensing, planning, and control (untestable, hard to timing-analyse).
