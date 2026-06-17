# Code organisation: Service, Workflow, and the request/execution split

Business logic lives in one of two layers:

**Service** (`src/modules/<name>/service.py`) — module-scoped logic that operates on one module's models. Default location for all business logic. A Service does not import from another module's Service.

**Workflow** (`src/workflows/<name>.py`) — cross-module orchestration that takes a single user intent and coordinates multiple Services to fulfil it. A Workflow is the only place that imports from more than one module. Class names match the file: `LinkInstitutionConnectionWorkflow`, not `OnboardingOrchestrator`.

**Request/execution split** — a module's service may be split into a `request_service.py` (synchronous path: enqueuing, validating, creating the job record) and an `execution_service.py` (asynchronous path: running the job in a background worker) when the two sides have entirely different consumers. This pattern is only justified when sync and async consumers genuinely diverge; it is not a default structure.

We chose this layering to make the answer to "where does new code go?" unambiguous: if it touches one module, it's a Service; if it spans modules, it's a Workflow; if it splits sync/async, it's a request/execution pair.
