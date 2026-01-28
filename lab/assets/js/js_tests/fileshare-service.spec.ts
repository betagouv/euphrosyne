import { FileshareStorageClient } from "../fileshare-storage-client";

describe("Test document file service", () => {
  describe("Test uploadFile", () => {
    it("uploads file in several batches", async () => {
      const storageClient = new FileshareStorageClient();
      const fetchSpy = vi
        .spyOn(global, "fetch")
        .mockImplementation(() =>
          Promise.resolve(
            new Response("body", { status: 200, statusText: "OK" }),
          ),
        );
      const { file } = await storageClient.upload(
        new File([new ArrayBuffer(6000000)], "hello", {
          type: "text/plain",
        }),
        "url",
      );

      expect(fetchSpy).toHaveBeenNthCalledWith(1, "url", {
        method: "PUT",
        headers: {
          "Content-Length": "0",
          "x-ms-type": "file",
          "x-ms-content-length": file.size.toString(),
          "x-ms-version": "2021-08-06",
        },
      });
      expect(fetchSpy).toHaveBeenNthCalledWith(2, "url" + "&comp=range", {
        method: "PUT",
        body: file.slice(0, 4000000),
        headers: {
          "x-ms-range": `bytes=0-${4000000 - 1}`,
          "x-ms-write": "update",
          "x-ms-version": "2021-08-06",
        },
      });
      expect(fetchSpy).toHaveBeenNthCalledWith(3, "url" + "&comp=range", {
        method: "PUT",
        body: file.slice(file.size, 4000000),
        headers: {
          "x-ms-range": `bytes=4000000-${file.size - 1}`,
          "x-ms-write": "update",
          "x-ms-version": "2021-08-06",
        },
      });
      expect(file.name).toBe("hello");
    });
  });
});
