# Lifecycle runtime

The lifecycle package adds durable wakeups and observable, deterministic runtime
cycles without introducing a continuously running model loop.

## Boundaries

- A host scheduler calls LifecycleSchedulerAdapter.tick; the adapter never starts a
  hidden polling task.
- WakeupManager persists manual and scheduled wakeups and atomically claims due work
  through LifecycleStore.
- LifecycleRuntime owns lifecycle state transitions. The first sprint observes,
  persists, schedules, and sleeps without invoking a model.
- TaskScheduler remains the sole owner of durable task execution. Lifecycle does not
  duplicate worker, retry, dependency, or resource-lock behavior.
- Product applications own authentication and HTTP routes. They may map
  LifecycleControlService to authenticated status, wake, pause, and resume routes.

## Reference usage

Create an InMemoryLifecycleStore, pass it to LifecycleRuntime with a stable agent ID,
start the runtime, and use manual_wake for an operator-triggered cycle. For local
durability, SQLitePersistence implements LifecycleStore.

Production multi-instance consumers should supply a transactional store with an
atomic due-wakeup claim.

## Deliberately deferred

Reasoning, policy-controlled self-scheduling, memory, objectives, watches, jobs, and
subagent delegation are not part of this skeleton. If an observer requests reasoning
before a reasoner is integrated, the cycle fails closed and records a failed state.
