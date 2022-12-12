import { getToken } from "../assets/js/jwt";
import { jest } from "@jest/globals";
describe("Test getToken", () => {
  describe("local storage usage", () => {
    // Mocks localStorage
    const getItemMock = jest.fn().mockReturnValue("local token");
    const setItemMock = jest.fn();
    Storage.prototype.getItem = getItemMock;
    Storage.prototype.setItem = setItemMock;

    const fetchTokenMock = jest.fn();
    global.fetch = fetchTokenMock;

    afterEach(() => {
      getItemMock.mockClear();
      setItemMock.mockClear();
      fetchTokenMock.mockClear();
    });

    it("uses localStorage when present", async () => {
      const token = await getToken();

      expect(token).toBe("local token");
      expect(getItemMock).toHaveBeenCalledTimes(1);
    });

    it("skips localStorage when checkLocalStorage set to false", async () => {
      fetchTokenMock.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({ access: "remote token" }),
      });
      const token = await getToken(false);

      expect(token).toBe("remote token");
      expect(getItemMock).not.toHaveBeenCalled();
      expect(fetchTokenMock).toHaveBeenCalled();
      expect(setItemMock).toHaveBeenCalledWith(
        "euphrosyne-jwt-access",
        "remote token"
      );
    });

    it("fetches token when not present", async () => {
      getItemMock.mockReturnValueOnce(null);
      fetchTokenMock.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({ access: "remote token" }),
      });
      const token = await getToken();
      expect(token).toBe("remote token");
      expect(getItemMock).toHaveBeenCalled();
      expect(fetchTokenMock).toHaveBeenCalled();
      expect(setItemMock).toHaveBeenCalledWith(
        "euphrosyne-jwt-access",
        "remote token"
      );
    });
  });
});
