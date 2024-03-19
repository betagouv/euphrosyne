import { DocumentFileService } from "../assets/js/document-file-service";

describe("Test document file service", () => {
  let fileService: DocumentFileService;

  beforeEach(() => {
    fileService = new DocumentFileService(
      "http://listfileurl",
      "https://fetchpresignedurl"
    );
  });

  describe("Test uploadFile", () => {
    it("uploads file in several batches", async () => {
      const createEmptyFileSpy = vi
          .spyOn(fileService, "createEmptyFile")
          .mockImplementation(() => Promise.resolve()),
        uploadBytesToFileSpy = vi
          .spyOn(fileService, "uploadBytesToFile")
          .mockImplementation(() =>
            Promise.resolve(
              new Response("body", { status: 200, statusText: "OK" })
            )
          );

      const { file } = await fileService.uploadFile(
        new File([new ArrayBuffer(6000000)], "hello", {
          type: "text/plain",
        }),
        "url"
      );

      expect(createEmptyFileSpy).toHaveBeenCalled();
      expect(uploadBytesToFileSpy).toHaveBeenNthCalledWith(
        1,
        "url",
        new Blob(),
        0,
        4000000 - 1
      );
      expect(uploadBytesToFileSpy).toHaveBeenNthCalledWith(
        2,
        "url",
        new Blob(),
        4000000,
        6000000 - 1
      );
      expect(file.name).toBe("hello");
    });

    it("throws error if one upload fail", async () => {
      vi.spyOn(fileService, "createEmptyFile").mockImplementation(() =>
        Promise.resolve()
      );
      const uploadBytesToFileSpy = vi
        .spyOn(fileService, "uploadBytesToFile")
        .mockImplementation(() =>
          Promise.resolve(
            new Response("body", { status: 200, statusText: "OK" })
          )
        )
        .mockImplementationOnce(() => Promise.reject()); // Reject on second call

      const file = new File([new ArrayBuffer(6000000)], "hello");

      let hasError;
      try {
        await fileService.uploadFile(file, "url");
      } catch (error) {
        hasError = true;
        expect(error).toMatchObject({ file, value: undefined });
      }
      expect(hasError).toBe(true);
      expect(uploadBytesToFileSpy).toHaveBeenCalledTimes(2);
    });
  });

  describe("Test uploadFiles", () => {
    it("fetches presigned URL and upload file", async () => {
      const fetchPresignedURLSpy = vi
          .spyOn(fileService, "fetchUploadPresignedURL")
          .mockImplementation(() => Promise.resolve("url")),
        uploadFileSpy = vi
          .spyOn(fileService, "uploadFile")
          .mockImplementation((file) => Promise.resolve({ file }));

      const allSettledPromise = await fileService.uploadFiles([
        new File([], "file-1.txt"),
        new File([], "file-2.txt"),
      ]);

      expect(allSettledPromise).toBeInstanceOf(Array);
      expect(allSettledPromise).toMatchObject([
        { status: "fulfilled", value: { file: { name: "file-1.txt" } } },
        { status: "fulfilled", value: { file: { name: "file-2.txt" } } },
      ]);
      expect(fetchPresignedURLSpy).toHaveBeenCalledTimes(2);
      expect(uploadFileSpy).toHaveBeenCalledTimes(2);
    });
  });
});
