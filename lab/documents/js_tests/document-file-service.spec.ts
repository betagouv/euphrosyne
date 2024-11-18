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
});
