import { useRef, useEffect } from "react";
import { IImageTransform } from "../IImageTransform";
import Cropper from "cropperjs";

interface ICroppedImageProps extends React.HTMLProps<HTMLImageElement> {
  transform?: IImageTransform | null;
  onReady: (dataURL: string) => void;
}

export default function CroppedImage({
  transform,
  onReady,
  ...props
}: ICroppedImageProps) {
  const originalImageRef = useRef<HTMLImageElement>(null);

  // INIT ORIGINAL (to crop image)
  useEffect(() => {
    if (originalImageRef.current) {
      const _cropper = new Cropper(originalImageRef.current, {
        checkCrossOrigin: false,
        viewMode: 1,
        ready: () => {
          if (!props.src) {
            throw new Error("src is not defined");
          }
          if (transform) {
            _cropper.setData(transform);
            onReady(_cropper.getCroppedCanvas().toDataURL());
          } else {
            onReady(props.src);
          }
        },
      });
      _cropper.disable();
      return () => {
        _cropper.destroy();
      };
    }
  }, [props.src]);

  return (
    <img
      ref={originalImageRef}
      {...props}
      crossOrigin="anonymous"
      css={{ maxWidth: "100%" }}
    />
  );
}
