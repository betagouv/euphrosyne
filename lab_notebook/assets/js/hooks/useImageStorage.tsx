import { useEffect, useState } from "react";
import { StorageImageServices } from "../notebook-image.services";
import { useClientContext } from "../../../../shared/js/EuphrosyneToolsClient.context";

export interface ImageStorage {
  baseUrl: string;
  token: string;
}

function getTokenExpiration(signedToken: string): Date | null {
  const expirationString = new URLSearchParams(signedToken).get("se");
  if (!expirationString) return null;
  return new Date(expirationString);
}
function tryGetValidImageStorageFromLocalStorage(
  localStorageKey: string,
): ImageStorage | null {
  const imageStorageInLocalStorage = localStorage.getItem(localStorageKey);
  if (!imageStorageInLocalStorage) return null;
  const parsedImageStorage = JSON.parse(
    imageStorageInLocalStorage,
  ) as ImageStorage;
  const signedUrlExpiration = getTokenExpiration(parsedImageStorage.token);
  if (!signedUrlExpiration || signedUrlExpiration < new Date()) return null;
  return parsedImageStorage;
}

export const useImageStorage = (projectSlug: string) => {
  const localStorageKey = `${projectSlug}-imageStorage`;
  const toolsClient = useClientContext();

  const [imageStorage, setImageStorage] = useState<ImageStorage | null>(null);

  const onImageStorageChange = (newImageStorage: ImageStorage) => {
    setImageStorage(newImageStorage);
    localStorage.setItem(localStorageKey, JSON.stringify(newImageStorage));
  };

  useEffect(() => {
    const localStorageImageStorage =
      tryGetValidImageStorageFromLocalStorage(localStorageKey);
    const imageService = new StorageImageServices(
      projectSlug,
      toolsClient.fetchFn,
    );

    let timeout: number = 0;

    if (localStorageImageStorage) {
      setImageStorage(localStorageImageStorage);
      const expiration = getTokenExpiration(
        localStorageImageStorage.token,
      ) as Date;
      timeout = expiration.getTime() - new Date().getTime();
    }

    // If we did not get the image storage from local storage or it is expired, we fetch it immediately,
    // otherwise we fetch it after the expiration time.
    const timeoutId = setTimeout(
      () => imageService.getImagesUrlAndToken().then(onImageStorageChange),
      timeout,
    );

    // Fetch the image storage every 50 minutes
    const intervalId = setInterval(
      () => imageService.getImagesUrlAndToken().then(onImageStorageChange),
      50 * 60 * 1000,
    );

    return () => {
      clearInterval(intervalId);
      clearTimeout(timeoutId);
    };
  }, [projectSlug]);

  return imageStorage;
};
