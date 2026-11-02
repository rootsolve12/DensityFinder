# ForestMesh

A wildlife sensor network command center: a reproducible digital twin of a 1 km² forest, with graph-based radio connectivity, failure experiments, wildlife events, and deployment comparison.

## Launch

Requires Python 3.12+ and Node.js 22+ (validated with Python 3.12.14 / Node 24.19.0). Run from the repository root:

```bash
python -m venv .venv
.venv/bin/pip install -r backend/requirements.lock
npm --prefix frontend ci
npm --prefix frontend run build
.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

The backend serves the production dashboard on port 8000. Open that port through your development environment. API reference: `/docs`; health: `/api/health`. For hot reload, run the API with `--reload` and `npm --prefix frontend run dev` in another terminal; Vite proxies API and WebSocket requests to port 8000.

No external API key, map service, or hardware is required. SQLite is created at `forestmesh.sqlite3`; set `FORESTMESH_DB` to change its path. Run **one API worker**: the active scenario is shared in process memory, not synchronized across workers. Events persist; scenario positions and failures reset on restart.

## Hackathon walkthrough

1. The default seed 42 deploys 50 nodes across a 1,000 × 1,000 m square, with a gateway at sensor 01. Inspect the density cards: **50 nodes/km²**, **9.82 expected nodes per transmission region**.
2. Click a node to inspect actual degree, health, position, and synthetic telemetry. Toggle Range to inspect its footprint. Its current gateway route recalculates after any failure. Wheel to zoom; drag the map to pan.
3. Trigger a wildlife event. The amber path traces the selected sensor's current gateway route, or the latest event's route when no sensor is selected. A moving packet illustrates information transport. Delivery and latency use an explicit radio simulation, not real hardware measurements.
4. Disable a relay, then trigger an event from the same node. The graph recalculates immediately; a new event uses an alternative shortest path when available. For guaranteed failure, disable gateway 01: reachability becomes zero and events cannot be delivered. Restore it to recover.
5. Use clustered placement and dense canopy for a challenging scenario. Apply resets the experiment. Optimize deployment searches grid candidates and shows before/after coverage and connectivity. If no candidate improves both, positions are retained.
6. Review the event ledger, graph-state chart, or export a JSON experiment snapshot. Auto events generate one event every five seconds while enabled.

## Architecture

```text
backend/
  engine.py          Seeded placement, graph analysis, coverage, routing, optimization
  main.py            FastAPI REST, live WebSocket snapshots, SQLite audit history
  tests/             Numerical, resilience, persistence, and API integration tests
frontend/
  src/main.tsx       Command center and experiment controls
  src/Topology.tsx   Cytoscape interactive radio graph and illustrative terrain
  src/style.css      Responsive dashboard, Tailwind entry point
  e2e/               Playwright complete-demo browser test
```

React + TypeScript + Vite + Tailwind, Cytoscape, Recharts; Python + FastAPI + WebSockets, NetworkX + NumPy, SQLite. The UI uses a same-origin API and needs no CORS override.

## Models and scientific limits

- **Spatial density:** active nodes / 1 km². The baseline has 50 active sensors.
- **Transmission-region density:** active density × π × nominal radius² in km. Baseline: 50 × π × 0.25² = 9.817… = 9.82. This is an ideal continuum expectation, not actual mean node degree; it ignores forest boundaries, the fixed sensor itself, and radio obstacles.
- **Actual adjacency:** undirected edges between active sensors within the effective Euclidean radio range. NetworkX calculates exact components, degree, and gateway reachability for these positions.
- **Routing:** unweighted shortest paths minimize hops; a fresh graph is used for every event. There is no radio contention, routing protocol convergence delay, packet queue, or field-calibrated link budget.
- **Coverage:** union of active radio discs within the square sampled at 10 m cell centers (10,000 points). This is an approximation to communication footprint, **not PIR detection coverage or animal detection probability**. Gaps indicate sampled uncovered cells. The illustrative terrain is not GIS data; coordinates in the map decoration are not sensor geolocation.
- **Environment:** clear = nominal range, heavy rain = 85%, dense canopy = 72%. These are demonstration assumptions, not propagation measurements.
- **Delivery:** a seeded Bernoulli trial at 98% success per hop in clear conditions, 92% otherwise. PDR is delivered / generated events in the current scenario. No events means no PDR value.
- **Latency:** successful events receive 18 ms per hop + seeded 4–12 ms jitter. This is simulated end-to-end latency, not API request latency. Undelivered events have no latency measurement.
- **Telemetry:** initial battery, temperature, and humidity are synthetic. Routed events consume 0.02 percentage points of battery at each node in the computed route; this is an illustrative energy model. Battery exhaustion does not automatically disable radios.
- **Optimization:** deterministic search over three regular-grid extents (650, 750, 850 m). Candidates must not reduce coverage or gateway reachability; ranking prefers reachability then coverage then fewer components. Disabled sensors stay disabled. This is a constrained heuristic, not a global optimum, and may propose moving the gateway. Physical relocation costs, terrain and conservation constraints are future work.
- Position generation and event outcomes repeat for a given seed, configuration and action sequence. Wall-clock event timestamps do not repeat. The chart records graph state at actions in this browser session, not continuous measurements.

## API

| Method | Path | Behavior |
| --- | --- | --- |
| GET | `/api/health` | Process health and simulation mode |
| GET | `/api/state` | Current configuration, graph, metrics, recent events, comparison |
| POST | `/api/scenario` | Reset with `{count, range, seed, placement, environment}` |
| POST | `/api/nodes/{id}/toggle` | Disable/restore a zero-based sensor ID |
| POST | `/api/events` | Generate event; `{}` selects seeded source, `{"node": 10}` selects ID 10 |
| POST | `/api/optimize` | Search placements and retain non-regressing improvement |
| GET | `/api/events/history` | Last 100 persisted events across experiments |
| WS | `/ws` | Current state snapshot every 2 seconds; browser reconnects automatically |

Scenario bounds: 5–150 nodes, nominal range 80–400 m, seed 0–1,000,000; placements `organic`, `grid`, `clustered`; environments `clear`, `rain`, `dense`. Interactive labels are 1-based; API IDs are 0-based. Apply scenario clears current events but preserves the SQLite audit history.

## Validation

```bash
.venv/bin/python -m pytest backend/tests -q
npm --prefix frontend test
npm --prefix frontend run build
# With the production backend running on port 8000:
npm --prefix frontend run test:e2e
```

The browser test uses `/usr/bin/chromium`; override `CHROMIUM_PATH` for another installed Chromium. It verifies event delivery, gateway failure, optimization comparison, scenario controls, mobile overflow, and absence of browser runtime errors. In a socket-restricted execution sandbox, run API/browser tests with the environment's supported elevated command execution; do not bypass the network proxy or disable TLS validation.

## Milestones delivered and next work

- [x] End-to-end seeded scenario → API → live digital twin.
- [x] Graph calculations and failure/recovery experiments.
- [x] Candidate placement optimization with before/after evidence.
- [x] Simulated events, per-hop route display, SQLite audit history.
- [x] Responsive analytics, export, automated checks and demo guide.
- [ ] Hardware ingestion: add authenticated ESP32/LoRa adapters with stable device IDs, timestamps, measured RSSI/SNR and acknowledgments. Keep measured packets separate from simulated events.
- [ ] Persistent multi-user experiments, authorization, migrations and deployment hardening.
- [ ] Calibrated propagation, ecological detection models, and constrained optimization.

This is a single-operator hackathon prototype. The unauthenticated mutation API is for a trusted development environment. It is not a production wildlife alerting system or a claim of verified field performance.
