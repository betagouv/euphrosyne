import {
  S3File,
  serializeS3ListObjectsV2Contents,
} from "../assets/js/s3-service";

describe("Test serializeS3ListObjectsV2Contents", () => {
  it("serializes xml correctly to an array of S3File", () => {
    const xml = `
        <ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Name>euphrosyne</Name><Prefix>projects/1/documents/</Prefix><KeyCount>2</KeyCount><MaxKeys>1000</MaxKeys><EncodingType>url</EncodingType><IsTruncated>false</IsTruncated><Contents><Key>projects/1/documents/IMG-20210313-WA0010.jpg</Key><LastModified>2022-01-14T09:29:56.000Z</LastModified><ETag>"fc581a799a411ac5f0917fbface8441a"</ETag><Size>465238</Size><StorageClass>STANDARD</StorageClass></Contents><Contents><Key>projects/1/documents/changed.pdf</Key><LastModified>2022-01-21T09:43:56.000Z</LastModified><ETag>"c95c6e91550d7e3800bd021a3234b880"</ETag><Size>33748</Size><StorageClass>STANDARD</StorageClass></Contents></ListBucketResult>`,
      parsedXml = new DOMParser().parseFromString(xml, "application/xml");

    const files = serializeS3ListObjectsV2Contents(
      parsedXml.querySelectorAll("Contents")
    );

    expect(files.length).toBe(2);
    expect(files[0] instanceof S3File).toBeTruthy();
    expect(files[0].key).toBe("projects/1/documents/IMG-20210313-WA0010.jpg");
    expect(files[0].name).toBe("IMG-20210313-WA0010.jpg");
    expect(files[0].lastModified).toBe("1/14/2022");
    expect(files[0].size).toBe("454.33 KB");
  });
});
