import { describe, expect, it } from "vitest";
import { parseRunningVMs } from "../components/running-vms";

const jsonResponse = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status });

describe("parseRunningVMs", () => {
  it("returns the VM list", async () => {
    await expect(
      parseRunningVMs(jsonResponse(["euphro-stg-vm-a"])),
    ).resolves.toEqual(["euphro-stg-vm-a"]);
  });

  it("rejects an error response", async () => {
    await expect(
      parseRunningVMs(jsonResponse({ detail: "Unauthorized" }, 401)),
    ).rejects.toThrow("status 401");
  });

  it("rejects a missing response", async () => {
    await expect(parseRunningVMs(undefined)).rejects.toThrow("status none");
  });

  it("rejects a body that is not a list", async () => {
    await expect(parseRunningVMs(jsonResponse({ vms: [] }))).rejects.toThrow(
      "Unexpected",
    );
  });
});
