import { Fragment, useState } from "react";
import ImageLoading from "./components/ImageLoading";
import { css } from "@emotion/react";
import { IImageTransform } from "./IImageTransform";
import ImageCropper from "./components/ImageCropper";

const visiblePlaceholderStyle = css({
  position: "absolute",
  top: 0,
  left: 0,
});

const hiddenPlaceholderStyle = css({
  display: "none",
});

interface IImageWithPlaceholderProps extends React.HTMLProps<HTMLImageElement> {
  transform?: IImageTransform | null;
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
        <ImageCropper
          {...otherProps}
          onReady={() => setIsLoaded(true)}
          transform={transform}
          readonly={true}
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
