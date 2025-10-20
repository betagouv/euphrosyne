export interface ExternalImageProvider {
  getImagesURL(providerObjectId: string): Promise<string[]>;
  constructFromPath(path: string, token?: string): string;
}
