import { ExternalObjectProvider } from "../../../objects/assets/js/types";
import { erosImageService } from "./eros";
import { popImageService } from "./pop";
import { ExternalImageProvider } from "./types";

export function getExternalImageService(
  provider: ExternalObjectProvider,
): ExternalImageProvider {
  return {
    eros: erosImageService,
    pop: popImageService,
  }[provider];
}
