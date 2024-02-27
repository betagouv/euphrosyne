interface Window {
  gettext: (text: string) => string;
  interpolate: (text: string, values: string[]) => string;
  dismissAddRelatedObjectGroupPopup?: (win: Window) => void;
}
