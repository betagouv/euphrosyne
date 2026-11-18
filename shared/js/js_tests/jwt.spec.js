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

describe("legacy storage", () => {
  it("removes tokens stored by previous versions on load", async () => {
    localStorage.setItem("euphrosyne-jwt-access", "old access");
    localStorage.setItem("euphrosyne-jwt-refresh", "old refresh");
    vi.resetModules();
    await import("../jwt");
    expect(localStorage.getItem("euphrosyne-jwt-access")).toBeNull();
    expect(localStorage.getItem("euphrosyne-jwt-refresh")).toBeNull();
  });
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

  it("follows the redirection of a session gate and throws", async () => {
    const assign = vi.fn();
    vi.spyOn(window, "location", "get").mockReturnValue({ assign });
    fetchMock.mockResolvedValueOnce(
      jsonResponse(403, {
        detail: "Multi-factor authentication is required.",
        code: "mfa_required",
        redirect_url: "/accounts/2fa/authenticate/",
      }),
    );

    await expect(jwt.getToken()).rejects.toThrow(
      "Multi-factor authentication is required.",
    );
    expect(assign).toHaveBeenCalledWith("/accounts/2fa/authenticate/");
    vi.restoreAllMocks();
  });

  it("throws a clear error when no token is returned", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(403, { detail: "Nope" }));

    await expect(jwt.getToken()).rejects.toThrow(
      "Failed to get token (status 403)",
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
