const { uploadDataSpy, blockBlobClientCtor, MockBlockBlobClient } =
  vi.hoisted(() => {
    const uploadDataSpy = vi.fn().mockResolvedValue(undefined);
    const blockBlobClientCtor = vi.fn();
    class MockBlockBlobClient {
      constructor(url: string) {
        blockBlobClientCtor(url);
      }
      uploadData = uploadDataSpy;
    }
    return { uploadDataSpy, blockBlobClientCtor, MockBlockBlobClient };
  });

vi.mock("@azure/storage-blob", () => ({
  BlockBlobClient: MockBlockBlobClient,
}));

import { BlobStorageClient } from "../blob-storage-client";

describe("BlobStorageClient", () => {
  it("uploads file using BlockBlobClient", async () => {
    const client = new BlobStorageClient();
    const arrayBuffer = new ArrayBuffer(10);
    const file = {
      arrayBuffer: vi.fn().mockResolvedValue(arrayBuffer),
    } as unknown as File;

    const result = await client.upload(file, "https://example.com/upload");

    expect(blockBlobClientCtor).toHaveBeenCalledWith(
      "https://example.com/upload",
    );
    expect(file.arrayBuffer).toHaveBeenCalledTimes(1);
    expect(uploadDataSpy).toHaveBeenCalledWith(arrayBuffer);
    expect(result).toEqual({ file });
  });
});
