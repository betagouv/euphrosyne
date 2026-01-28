import { DocumentFileService } from "../assets/js/document-file-service";

describe("Test document file service", () => {
  let fileService: DocumentFileService;

  beforeEach(() => {
    fileService = new DocumentFileService(
      "http://listfileurl",
      "https://fetchpresignedurl",
    );
  });

  describe("Test uploadFiles", () => {
    it("fetches presigned URL and upload file", async () => {
      const fetchPresignedURLSpy = vi
          .spyOn(fileService, "fetchUploadPresignedURL")
          .mockImplementation(() => Promise.resolve("url")),
        uploadFileSpy = vi
          .spyOn(fileService, "uploadFile")
          .mockImplementation((file) => Promise.resolve({ file }));

      await fileService.uploadFiles([
        new File([], "file-1.txt"),
        new File([], "file-2.txt"),
      ]);

      expect(fetchPresignedURLSpy).toHaveBeenCalledTimes(2);
      expect(uploadFileSpy).toHaveBeenCalledTimes(2);
    });
  });

  describe("Test injected storage client", () => {
    it("uses provided storage client", async () => {
      const file = new File([], "file-1.txt");
      const uploadHandler = vi.fn().mockResolvedValue({ file });
      const storageClient = { upload: uploadHandler };
      fileService = new DocumentFileService("project", "slug", {
        storageClient,
      });

      await fileService.uploadFile(file, "https://example.com");

      expect(uploadHandler).toHaveBeenCalledWith(file, "https://example.com");
    });
  });
});
