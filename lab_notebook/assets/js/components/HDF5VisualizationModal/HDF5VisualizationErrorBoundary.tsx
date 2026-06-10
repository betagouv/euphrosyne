import { Component, ReactNode } from "react";

interface HDF5VisualizationErrorBoundaryProps {
  children: ReactNode;
}

export class HDF5VisualizationErrorBoundary extends Component<
  HDF5VisualizationErrorBoundaryProps,
  { error: Error | null }
> {
  constructor(props: HDF5VisualizationErrorBoundaryProps) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <div className="fr-alert fr-alert--error">
          <p>{window.gettext("The selected HDF5 data could not be loaded.")}</p>
        </div>
      );
    }
    return this.props.children;
  }
}
