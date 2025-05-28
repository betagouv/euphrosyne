/**
 * crop.ts
 *
 * Provides a utility function to crop an image using a canvas element and return the cropped image as a data URL.
 *
 * Exports:
 *   - cropImage: Crops a given image source according to a specified transform and returns the result via a callback.
 *   - cropImageAsync: Crops a given image source according to a specified transform and returns the result as a Promise.
 *
 * Usage:
 *   cropImage(src, transform, (croppedSrc) => { ... });
 *   cropImageAsync(src, transform).then((croppedSrc) => { ... });
 *
 * If no transform is provided, the original image source is returned.
 *
 * @module crop
 */

import { IImageTransform } from "./IImageTransform";

/**
 * Crops an image using a canvas and resolves the cropped image as a data URL.
 *
 * @param src - The source URL or data URL of the image to crop.
 * @param transform - The cropping rectangle (x, y, width, height). If null, the original image is returned.
 * @returns A promise that resolves to the cropped image as a data URL.
 */
export async function cropImage(
  src: string,
  transform: IImageTransform | null,
): Promise<string> {
  if (!transform) {
    return src;
  }
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    throw new Error("Failed to get canvas context");
  }
  const { x, y, width, height } = transform;
  canvas.width = width;
  canvas.height = height;
  const image = new Image();
  image.crossOrigin = "anonymous";
  image.src = src;
  await new Promise<void>((resolve, reject) => {
    image.onload = () => resolve();
    image.onerror = reject;
  });
  ctx.drawImage(image, x, y, width, height, 0, 0, width, height);
  return canvas.toDataURL();
}
