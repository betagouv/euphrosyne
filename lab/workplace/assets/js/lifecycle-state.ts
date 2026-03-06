export type LifecycleState = "HOT" | "COOLING" | "COOL" | "RESTORING" | "ERROR";
export type LifecycleOperationType = "COOL" | "RESTORE";

export const LIFECYCLE_STATE_CHANGED_EVENT = "workplace:lifecycle-state-changed";

export function isLifecycleState(value: unknown): value is LifecycleState {
  return (
    value === "HOT" ||
    value === "COOLING" ||
    value === "COOL" ||
    value === "RESTORING" ||
    value === "ERROR"
  );
}

export function dispatchLifecycleStateChanged(state: LifecycleState): void {
  window.dispatchEvent(
    new CustomEvent<LifecycleState>(LIFECYCLE_STATE_CHANGED_EVENT, {
      detail: state,
    }),
  );
}
