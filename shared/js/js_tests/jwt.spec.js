import { jwtDecode } from "jwt-decode";

vi.mock("jwt-decode", () => ({
  jwtDecode: vi.fn(),
}));

const VALID = { exp: Date.now() / 1000 + 1000 };
const EXPIRED = { exp: Date.now() / 1000 - 10 };

function jsonResponse(status, body) {
  const response = {
    ok: status >= 200 && status < 300,
    status,
    json: vi.fn().mockResolvedValue(body),
  };
  response.clone = () => response;
  return response;
}

function calledUrls(fetchMock) {
  return fetchMock.mock.calls.map(([url]) => url);
}

let jwt;
let fetchMock;

beforeEach(async () => {
  vi.resetModules();
  jwtDecode.mockReset();
  jwtDecode.mockReturnValue(VALID);
  fetchMock = vi.fn();
  global.fetch = fetchMock;
  localStorage.clear();
  jwt = await import("../jwt");
});

describe("getToken", () => {
  it("fetches an access token from the session endpoint", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(200, { access: "token 1" }));

    expect(await jwt.getToken()).toBe("token 1");
    expect(calledUrls(fetchMock)).toEqual(["/api/auth/token/"]);
    expect(localStorage.length).toBe(0);
  });

  it("reuses the cached token until it expires", async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse(200, { access: "token 1" }))
      .mockResolvedValueOnce(jsonResponse(200, { access: "token 2" }));

    expect(await jwt.getToken()).toBe("token 1");
    expect(await jwt.getToken()).toBe("token 1");
    expect(fetchMock).toHaveBeenCalledTimes(1);

    jwtDecode.mockReturnValue(EXPIRED);
    expect(await jwt.getToken()).toBe("token 2");
    expect(calledUrls(fetchMock)).toEqual([
      "/api/auth/token/",
      "/api/auth/token/",
    ]);
  });

  it("fetches a new token when checkCache is false", async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse(200, { access: "token 1" }))
      .mockResolvedValueOnce(jsonResponse(200, { access: "token 2" }));

    await jwt.getToken();
    expect(await jwt.getToken(false)).toBe("token 2");
  });

  it("throws the detail of a session gate", async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse(403, {
        detail: "You must accept the Terms and Conditions to continue.",
        code: "cgu_acceptance_required",
        redirect_url: "/cgu/",
      }),
    );

    await expect(jwt.getToken()).rejects.toThrow(
      "Failed to get token: You must accept the Terms and Conditions to continue.",
    );
  });

  it("throws the status when the response has no detail", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 502,
      json: vi.fn().mockRejectedValue(new SyntaxError("not JSON")),
    });

    await expect(jwt.getToken()).rejects.toThrow(
      "Failed to get token: status 502",
    );
  });
});

describe("jwtFetch", () => {
  it("retries once with a new token after an unauthorized status", async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse(200, { access: "token 1" }))
      .mockResolvedValueOnce(jsonResponse(401, { code: "token_not_valid" }))
      .mockResolvedValueOnce(jsonResponse(200, { access: "token 2" }))
      .mockResolvedValueOnce(jsonResponse(200, { ok: true }));

    const response = await jwt.jwtFetch("/api/data", { method: "GET" });

    expect(response.status).toBe(200);
    expect(calledUrls(fetchMock)).toEqual([
      "/api/auth/token/",
      "/api/data",
      "/api/auth/token/",
      "/api/data",
    ]);
    expect(fetchMock.mock.calls[3][1].headers.get("Authorization")).toBe(
      "Bearer token 2",
    );
  });

  it("does not retry on forbidden responses", async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse(200, { access: "token 1" }))
      .mockResolvedValueOnce(jsonResponse(403, { code: "permission_denied" }));

    const response = await jwt.jwtFetch("/api/data", { method: "GET" });

    expect(response.status).toBe(403);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
