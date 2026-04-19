# Motion-Planning Algorithm Selection

## RRT* (Rapidly-exploring Random Tree — optimal variant)

- **Best for:** high-dimensional configuration spaces (e.g. 6–7 DOF manipulator arms) where exhaustive search is infeasible.
- **Guarantees:** probabilistically complete + asymptotically optimal (given enough samples, converges to the optimal solution).
- **Cost:** single-query — each new goal restarts the tree. Slow for repeated queries in the same environment.
- **Typical implementation:** OMPL (Open Motion Planning Library), MoveIt, commercial arm-planner stacks.
- **Variants:** RRT-Connect (bidirectional — faster), BIT* (informed batch sampling — practically faster than RRT* at similar optimality), LazyRRT.

## MPC (Model-Predictive Control)

- **Best for:** constrained dynamic systems with short planning horizons (quadrotors, autonomous vehicles, dynamic manipulation).
- **Method:** at each control step, solve an optimisation problem over a short horizon, execute the first control input, re-plan next step.
- **Strengths:** handles state/input constraints natively; smoothly integrates dynamics; robust to disturbances (via receding horizon).
- **Costs:** real-time optimisation is expensive — needs solvers like ACADO, CasADi, IPOPT, or specialised code generation (e.g. acados for embedded deployment).
- **Variants:** Linear MPC (convex QP), nonlinear MPC (SQP or interior-point), learning-based MPC (value-function augmented).

## PRM (Probabilistic Roadmap)

- **Best for:** repeated planning in the *same* environment (e.g. factory pick-and-place, always-same workcell).
- **Method:** offline — sample many configurations, connect collision-free edges, build a graph. Online — query the graph for shortest path between start/goal.
- **Strengths:** amortises planning cost — online queries become fast graph searches.
- **Cost:** offline build phase is expensive; graph invalidated if environment changes meaningfully.

## A* / D* and grid-based planners

- **Best for:** 2D/3D navigation in known or incrementally-discovered gridded environments (warehouse AMRs, indoor mobile robots).
- **A*** — classic optimal graph search with an admissible heuristic.
- **D* / D* Lite** — handles dynamic replanning when new obstacles appear; well-suited to mobile robots in partly-known environments.
- **Hybrid A*** — continuous-space extension used in autonomous driving (accounts for vehicle kinematic constraints).

## Selection table

| Problem | Candidate | Why |
|---------|-----------|-----|
| 6-DOF arm in unknown cluttered scene | RRT* / BIT* | High-dim, single-query |
| Quadrotor trajectory with thrust limits | MPC (nonlinear) | Dynamics + constraints |
| Factory pick-and-place, same cell | PRM | Repeated queries, fixed env |
| AMR in known warehouse map | A* or D* Lite | 2D grid, possible dynamic obstacles |
| Autonomous car parking manoeuvre | Hybrid A* + MPC | Kinematic constraints + dynamic execution |

## Decision heuristic

1. **Is the environment known and static?** → PRM.
2. **Is the state space low-dim and gridded?** → A*/D*.
3. **Is the system dynamic with tight constraints and short horizon?** → MPC.
4. **Is the configuration space high-dim with variable obstacles?** → RRT*/BIT*.
5. **Combination?** → often: sampling-based global plan + MPC local tracking.
