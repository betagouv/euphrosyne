import {
  dispatchLifecycleStateChanged,
  LIFECYCLE_STATE_CHANGED_EVENT,
  onLifecycleStateChanged,
} from "../assets/js/lifecycle-state";

describe("lifecycle-state", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("notifies registered listeners when lifecycle state changes", () => {
    const listener = vi.fn();

    const unsubscribe = onLifecycleStateChanged(listener);
    dispatchLifecycleStateChanged("HOT");

    expect(listener).toHaveBeenCalledTimes(1);
    expect(listener).toHaveBeenCalledWith("HOT");

    unsubscribe();
  });

  it("stops notifying listeners after unsubscribe", () => {
    const listener = vi.fn();

    const unsubscribe = onLifecycleStateChanged(listener);
    unsubscribe();
    dispatchLifecycleStateChanged("COOL");

    expect(listener).not.toHaveBeenCalled();
  });

  it("ignores invalid lifecycle state payloads", () => {
    const listener = vi.fn();

    const unsubscribe = onLifecycleStateChanged(listener);
    window.dispatchEvent(
      new CustomEvent(LIFECYCLE_STATE_CHANGED_EVENT, {
        detail: "INVALID_STATE",
      }),
    );

    expect(listener).not.toHaveBeenCalled();

    unsubscribe();
  });
});
