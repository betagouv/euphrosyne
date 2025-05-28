import { Fragment, useState } from "react";
import ImageLoading from "./components/ImageLoading";
import { css } from "@emotion/react";
import { IImageTransform } from "./IImageTransform";
import CroppedImage from "./components/CroppedImage";

const visiblePlaceholderStyle = css({
  position: "absolute",
  top: 0,
  left: 0,
});

const hiddenPlaceholderStyle = css({
  display: "none",
});

interface IImageWithPlaceholderProps
  extends Omit<React.HTMLProps<HTMLImageElement>, "src"> {
  transform?: IImageTransform | null;
  src: string;
}

export default function ImageWithPlaceholder(
  props: IImageWithPlaceholderProps,
) {
  const { transform, ...otherProps } = props;

  const [isLoaded, setIsLoaded] = useState<boolean>(false);

  const onImageLoad = () => {
    setIsLoaded(true);
  };

  return (
    <Fragment>
      {transform ? (
        <CroppedImage
          {...otherProps}
          onImageLoaded={() => setIsLoaded(true)}
          imageTransform={transform}
        />
      ) : (
        <img {...otherProps} onLoad={onImageLoad} />
      )}
      <ImageLoading
        css={isLoaded ? hiddenPlaceholderStyle : visiblePlaceholderStyle}
      />
    </Fragment>
  );
}
