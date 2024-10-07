import { MouseEventHandler, useEffect, useState } from "react";
import ObjectSelect from "./ObjectSelect";
import type { RunObjectGroup } from "../../../../lab/objects/assets/js/types";
import type { IMeasuringPoint } from "../IMeasuringPoint";
import AddImageToObject from "./AddImageToObject";
import AddImageToObjectTransform from "./AddImageToObjectTransform";
import {
  IImageTransform,
  IImagewithUrl,
  IRunObjectImage,
} from "../IImageTransform";
import { RunObjectGroupImageServices } from "../notebook-image.services";
import AddMeasuringPointToImage from "./AddMeasuringPointToImage";

type StepNumber = 1 | 11 | 12 | 21;

interface IAddImageToMeasuringModalProps {
  runObjectGroups: RunObjectGroup[];
  measuringPoint?: IMeasuringPoint;
}

interface IFooterButton {
  title: string;
  onClick: MouseEventHandler<HTMLButtonElement>;
  frType: "primary" | "secondary" | "tertiary";
  disabled?: boolean;
}

interface IStep {
  title: string;
  buttons: IFooterButton[];
  content: () => React.ReactNode;
}

type ISteps = {
  [Key in StepNumber]: IStep;
};

export default function AddImageToMeasuringModal({
  runObjectGroups,
  measuringPoint,
}: IAddImageToMeasuringModalProps) {
  const t = {
    close: window.gettext("Close"),
    objectChoice: window.gettext("Object group / object choice"),
    imageChoice: window.gettext("Image choice"),
    imageChoiceWithAdjustment: window.gettext("Image choice (edit)"),
    continueAdjustImage: window.gettext("Edit image"),
    continueNoAdjustImage: window.gettext("Continue without editing"),
    pointSelection: window.gettext("Point selection on image"),
    next: window.gettext("Next"),
    back: window.gettext("Back"),
    save: window.gettext("Save"),
    changeImage: window.gettext("Change image"),
    backToEdit: window.gettext("Back to edit"),
    stepCount: window.gettext("Step %s of %s"),
    nextStep: window.gettext("Next step: "),
  };

  const runObjectGroup = runObjectGroups.find(
    (rog) => rog.objectGroup.id === measuringPoint?.objectGroupId,
  );
  const objectGroup = runObjectGroup?.objectGroup;

  // Can be either local path or blob path
  const [selectedObjectImageURL, setSelectedObjectImageURL] =
    useState<IImagewithUrl | null>();

  const [selectedImageTransform, setSelectedImageTransform] =
    useState<IImageTransform | null>();

  const [selectedObjectRunImage, setSelectedObjectRunImage] =
    useState<IRunObjectImage | null>();

  const addImageToRunObjectGroup = async () => {
    if (runObjectGroup && selectedObjectImageURL) {
      const path = new URL(selectedObjectImageURL.url).pathname;
      const savedImage = await new RunObjectGroupImageServices(
        runObjectGroup?.id,
      ).addRunObjectGroupImage({
        path,
        transform: selectedImageTransform || null,
      });
      setSelectedObjectRunImage(savedImage);
    }
  };

  const steps: ISteps = {
    1: {
      // Object choice
      title: t.objectChoice,
      buttons: [
        {
          title: t.next,
          onClick: () => setCurrentStep(11),
          frType: "primary",
        },
      ],
      content: () =>
        measuringPoint && (
          <ObjectSelect
            measuringPoint={measuringPoint}
            runObjectGroups={runObjectGroups}
          />
        ),
    },
    11: {
      // Images gallery
      title: t.imageChoice,
      content: () =>
        objectGroup && (
          <AddImageToObject
            runObjectGroup={runObjectGroup}
            onImageSelect={setSelectedObjectImageURL}
            onRunObjectImageSelect={setSelectedObjectRunImage}
          />
        ),
      buttons: [
        {
          title: t.continueNoAdjustImage,
          onClick: () => setCurrentStep(21),
          frType: "primary",
          disabled: !selectedObjectImageURL || !selectedObjectRunImage,
        },
        {
          title: t.continueAdjustImage,
          onClick: () => setCurrentStep(12),
          frType: "primary",
          disabled: !selectedObjectImageURL || !!selectedObjectRunImage,
        },
        {
          title: t.back,
          onClick: () => setCurrentStep(1),
          frType: "secondary",
        },
      ],
    },
    12: {
      // Adjust selected image
      title: t.imageChoiceWithAdjustment,
      content: () =>
        selectedObjectImageURL && (
          <AddImageToObjectTransform
            image={selectedObjectImageURL}
            onTransform={setSelectedImageTransform}
          />
        ),
      buttons: [
        {
          title: t.next,
          onClick: () => {
            addImageToRunObjectGroup().then(() => setCurrentStep(21));
          },
          frType: "primary",
          disabled: !selectedImageTransform,
        },
        {
          title: t.back,
          onClick: () => {
            setCurrentStep(11);
            setSelectedObjectImageURL(null);
            setSelectedImageTransform(null);
          },
          frType: "secondary",
        },
      ],
    },
    21: {
      // Select measuring point on image
      title: t.pointSelection,
      content: () => (
        <AddMeasuringPointToImage image={selectedObjectImageURL} />
      ),
      buttons: [
        {
          title: t.changeImage,
          onClick: () => setCurrentStep(11),
          frType: "secondary",
        },
        {
          title: t.backToEdit,
          onClick: () => setCurrentStep(12),
          frType: "secondary",
        },
        {
          title: t.save,
          onClick: () => null,
          frType: "primary",
        },
      ],
    },
  };

  const initialStep = measuringPoint?.objectGroupId ? 11 : 1;

  const [currentStep, setCurrentStep] = useState<StepNumber>(initialStep);

  const getNextStepTitle = () => {
    if (
      currentStep >= Math.max(...Object.keys(steps).map((k) => parseInt(k)))
    ) {
      return null;
    }
    const nextStepIndex =
      currentStep < 11 ? 11 : currentStep - (currentStep % 10) + 11;
    return steps[nextStepIndex as StepNumber].title;
  };

  const nextStepTitle = getNextStepTitle();

  const modalId = `add-measuring-point-image-modal`;

  useEffect(() => {
    // Go to second step if object group is set
    if (objectGroup && currentStep === 1) {
      setCurrentStep(11);
    }
  }, [objectGroup]);

  return (
    <dialog
      aria-labelledby={`${modalId}-title`}
      role="dialog"
      id={modalId}
      className="fr-modal"
    >
      <div className="fr-container fr-container--fluid fr-container-md">
        <div className="fr-grid-row fr-grid-row--center">
          <div className="fr-col-12 fr-col-md-8">
            <div className="fr-modal__body">
              <div className="fr-modal__header">
                <button
                  className="fr-btn--close fr-btn"
                  title={t.close}
                  aria-controls={modalId}
                >
                  {t.close}
                </button>
              </div>
              <div className="fr-modal__content">
                <div className="fr-stepper" id={`${modalId}-title`}>
                  <h2 className="fr-stepper__title">
                    {steps[currentStep].title}
                    <span className="fr-stepper__state">
                      {window.interpolate(t.stepCount, [
                        Math.ceil(currentStep / 10).toString(),
                        "3",
                      ])}
                    </span>
                  </h2>
                  <div
                    className="fr-stepper__steps"
                    data-fr-current-step={Math.ceil(currentStep / 10)}
                    data-fr-steps={3}
                  ></div>
                  {nextStepTitle && (
                    <p className="fr-stepper__details">
                      <span className="fr-text--bold">{t.nextStep}</span>
                      {nextStepTitle}
                    </p>
                  )}
                </div>
                {steps[currentStep].content()}
              </div>
              <div className="fr-modal__footer">
                <div className="fr-btns-group fr-btns-group--right fr-btns-group--inline-reverse fr-btns-group--inline-lg fr-btns-group--icon-left">
                  <FooterButtons buttons={steps[currentStep].buttons} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </dialog>
  );
}

function FooterButtons({ buttons }: { buttons: IFooterButton[] }) {
  return (
    <div className="fr-btns-group fr-btns-group--right fr-btns-group--inline-reverse fr-btns-group--inline-lg fr-btns-group--icon-left">
      {buttons.map((button) => (
        <button
          key={`footer-button-${button.title}`}
          className={`fr-btn fr-btn--${button.frType}`}
          onClick={button.onClick}
          disabled={button.disabled}
        >
          {button.title}
        </button>
      ))}
    </div>
  );
}
