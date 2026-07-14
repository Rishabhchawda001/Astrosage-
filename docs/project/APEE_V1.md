# ASTROSAGE PARALLEL EXECUTION ENGINE (APEE v1)

**Status:** PERMANENT EXECUTION POLICY
**Effective:** 2026-07-12
**Applies to:** Every future phase unless explicitly sequential

---

## EXECUTION MODEL

Every phase is divided into independent work packages.

10 IMPLEMENTATION WORKERS + 5 VALIDATION WORKERS run simultaneously.

### Implementation Team

| Worker | Area |
|--------|------|
| Worker 01 | Architecture |
| Worker 02 | Core Engine |
| Worker 03 | Plugin System |
| Worker 04 | Skills |
| Worker 05 | Registries |
| Worker 06 | Interfaces |
| Worker 07 | Adapters |
| Worker 08 | Testing |
| Worker 09 | Performance |
| Worker 10 | Git Integration |

### Validation Team

| Validator | Scope |
|-----------|-------|
| Validator 01 | Architecture consistency |
| Validator 02 | Typing, Lint, Imports |
| Validator 03 | Tests, Regression, Coverage |
| Validator 04 | Knowledge correctness, Standards, Constitution |
| Validator 05 | Git, Dependency, Build, Integration |

Validators NEVER implement. Validators only verify.

---

## PARALLEL EXECUTION RULES

1. Every task must first be dependency-analysed.
2. If independent → RUN IN PARALLEL.
3. Dynamic task scheduler maintains internal task graph: READY / RUNNING / WAITING / BLOCKED / COMPLETE.
4. Never leave a worker idle.

## CHECKPOINTS

Every 5–10 minutes or after every logical milestone:
- Save checkpoint
- Commit if milestone complete
- Push immediately
- Never accumulate large uncommitted changes

## QUALITY GATES

Nothing merges until ALL 5 validators approve. If ANY fails → return to implementation.

## SELF REVIEW

Before declaring completion, every worker asks:
- What can break?
- What have I missed?
- What assumptions did I make?
- What edge cases exist?
- What conflicts exist?

## CORRECTNESS POLICY

Speed is secondary. Correctness is mandatory.

Every generated object must have:
UUID, Version, Checksum, Provenance, Traceability, Validation, Confidence.

## FAILURE POLICY

If one worker fails, do NOT stop the entire phase. Continue independent workers. Retry failed work separately.

## SUCCESS CRITERIA

A phase is COMPLETE only when:
- All implementation workers complete
- All validators approve
- All tests pass
- Typecheck passes
- Lint passes
- Build passes
- GitHub push succeeds
- Working tree is clean
- No TODOs, placeholders, broken imports, dead code, merge conflicts, regression
