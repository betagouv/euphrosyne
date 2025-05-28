import { useCallback } from "react";
import { CopperSelectionChangeEvent } from "../../../../typescript/cropper";
import { IImageTransform, IImagewithUrl } from "../IImageTransform";
import ImageCropper from "./ImageCropper";

export default function AddImageToObjectTransform({
  image,
  onTransform,
}: {
  image: IImagewithUrl;
  onTransform?: (data: IImageTransform) => void;
}) {
  const handleCrop = useCallback(
    (e: CopperSelectionChangeEvent) => {
      if (onTransform && e.detail) {
        onTransform(e.detail);
      }
    },
    [onTransform],
  );
  return (
    <div style={{ width: "100%", aspectRatio: "16 / 9" }}>
      <ImageCropper src={image.url} onCrop={handleCrop} />
    </div>
  );
}
