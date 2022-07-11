import { jest } from "@jest/globals";

import { FileService } from "../assets/js/file-service.js";

describe("Test file service", () => {
  let fileService;

  beforeEach(() => {
    fileService = new FileService(
      "http://listfileurl",
      "https://fetchpresignedurl"
    );
  });

  describe("Test uploadFile", () => {
    it("uploads file in several batches", async () => {
      const createEmptyFileSpy = jest
          .spyOn(fileService, "createEmptyFile")
          .mockImplementation(() => Promise.resolve()),
        uploadBytesToFileSpy = jest
          .spyOn(fileService, "uploadBytesToFile")
          .mockImplementation(() => Promise.resolve());

      const { file } = await fileService.uploadFile({
        size: 6000000,
        slice: (start, end) => end - start,
        name: "hello",
      });

      expect(createEmptyFileSpy).toHaveBeenCalled();
      expect(uploadBytesToFileSpy).toHaveBeenNthCalledWith(
        1,
        undefined,
        4000000,
        0,
        4000000 - 1
      );
      expect(uploadBytesToFileSpy).toHaveBeenNthCalledWith(
        2,
        undefined,
        2000000,
        4000000,
        6000000 - 1
      );
      expect(file.name).toBe("hello");
    });

    it("throws error if one upload fail", async () => {
      jest
        .spyOn(fileService, "createEmptyFile")
        .mockImplementation(() => Promise.resolve());
      const uploadBytesToFileSpy = jest
        .spyOn(fileService, "uploadBytesToFile")
        .mockImplementation(() => Promise.resolve())
        .mockImplementationOnce(() => Promise.reject()); // Reject on second call

      const file = {
        size: 6000000,
        slice: (start, end) => end - start,
        name: "hello",
      };

      let hasError;
      try {
        await fileService.uploadFile(file);
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
      const fetchPresignedURLSpy = jest
          .spyOn(fileService, "fetchPresignedURL")
          .mockImplementation(() => Promise.resolve("url")),
        uploadFileSpy = jest
          .spyOn(fileService, "uploadFile")
          .mockImplementation((file) => Promise.resolve({ file }));

      const allSettledPromise = await fileService.uploadFiles([
        { name: "file-1.txt" },
        { name: "file-2.txt" },
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
