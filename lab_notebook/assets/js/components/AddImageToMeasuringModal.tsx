import {
  MouseEventHandler,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import ObjectSelect from "./ObjectSelect";
import type { RunObjectGroup } from "../../../../lab/objects/assets/js/types";
import type { IMeasuringPoint } from "../../../../shared/js/images/types";
import AddImageToObject from "./AddImageToObject";
import AddImageToObjectTransform from "./AddImageToObjectTransform";
import {
  IImageTransform,
  IImagewithUrl,
  IRunObjectImage,
  IRunObjectImageWithUrl,
} from "../../../../shared/js/images/types";
import { RunObjectGroupImageServices } from "../notebook-image.services";
import AddMeasuringPointToImage from "./AddMeasuringPointToImage";
import { IPointLocation } from "../../../../shared/js/images/types";
import {
  addMeasuringPointImage,
  deleteMeasuringPointImage,
} from "../../../../lab/assets/js/measuring-point.services";
import { NotebookContext } from "../Notebook.context";
import {
  constructImageStorageUrl,
  extractPath,
  extractProviderFromPath,
} from "../utils";
import { getToken } from "../../../../shared/js/jwt";

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
    continueAdjustImage: window.gettext("Resize image"),
    continueNoAdjustImage: window.gettext("Continue"),
    pointSelection: window.gettext("Point selection on image"),
    next: window.gettext("Next"),
    back: window.gettext("Back"),
    save: window.gettext("Save"),
    changeImage: window.gettext("Change image"),
    backToEdit: window.gettext("Back to edit"),
    stepCount: window.gettext("Step %s of %s"),
    nextStep: window.gettext("Next step: "),
    delete: window.gettext("Delete"),
  };

  const runObjectGroup = runObjectGroups.find(
    (rog) => rog.objectGroup.id === measuringPoint?.objectGroupId,
  );
  const objectGroup = runObjectGroup?.objectGroup;

  const { imageStorage, updateMeasuringPointImage } =
    useContext(NotebookContext);

  const [isAddingRunObjectImage, setIsAddingRunObjectImage] = useState(false);
  const [isDeletingMeasuringPointImage, setIsDeletingMeasuringPointImage] =
    useState(false);

  const closeButtonRef = useRef<HTMLButtonElement>(null);

  const resetModal = () => {
    if (pointLocation) {
      setPointLocation(undefined);
    }
    if (selectedObjectImage) {
      setSelectedObjectImage(null);
    }
    if (selectedImageTransform) {
      setSelectedImageTransform(undefined);
    }
    if (selectedRunObjectImage) {
      setSelectedRunObjectImage(null);
    }
  };

  // Represents an image accessible somewhere with its `url` property.
  // This image will be saved as a Run-Object image in the database,
  // where data about measurement points will be linked to it.
  const [selectedObjectImage, setSelectedObjectImage] =
    useState<IImagewithUrl | null>(null);

  // Represents the transformation properties (e.g., zoom, rotation, etc.)
  // related to the selectedObjectImage. Can be object, null (i.e no transform)
  // or undefined (unknown / not specified).
  const [selectedImageTransform, setSelectedImageTransform] =
    useState<IImageTransform | null>();

  // Represents the final state of the image that will be saved in the database.
  // It links the web url accessible image and its transformation information.
  const [selectedRunObjectImage, setSelectedRunObjectImage] =
    useState<IRunObjectImageWithUrl | null>(null);

  // Image selection
  const onImageSelect = (image: IImagewithUrl) => {
    setSelectedObjectImage(image);
    setSelectedRunObjectImage(null);
  };
  const onRunObjectImageSelect = (image: IRunObjectImageWithUrl) => {
    setSelectedObjectImage(null);
    setSelectedRunObjectImage(image);
  };

  // Adding image & transformation to DB
  const addImageToRunObjectGroup = async () => {
    if (runObjectGroup && selectedObjectImage) {
      const path = extractPath(
        new URL(selectedObjectImage.url).pathname,
        selectedObjectImage.provider,
      );
      const savedImage = await new RunObjectGroupImageServices(
        runObjectGroup?.id,
      ).addRunObjectGroupImage({
        path,
        transform: selectedImageTransform || null,
      });
      onRunObjectImageSelect({
        ...savedImage,
        url: selectedObjectImage.url,
        provider: selectedObjectImage.provider,
      });
    }
  };

  // Adding measuring point on image info to DB

  const [pointLocation, setPointLocation] = useState<IPointLocation>();

  const addImageToPoint = async () => {
    if (!measuringPoint || !selectedRunObjectImage?.id || !pointLocation) {
      return;
    }
    return addMeasuringPointImage(
      measuringPoint?.id,
      selectedRunObjectImage?.id,
      pointLocation,
      !measuringPoint.image,
    );
  };

  // Steps

  const steps: ISteps = {
    1: {
      // Object choice
      title: t.objectChoice,
      buttons: [
        {
          title: t.next,
          onClick: () => setCurrentStep(11),
          frType: "primary",
          disabled: !measuringPoint?.objectGroupId,
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
            selectedObjectImage={selectedObjectImage}
            selectedRunObjectImage={selectedRunObjectImage}
            onImageSelect={onImageSelect}
            onRunObjectImageSelect={onRunObjectImageSelect}
          />
        ),
      buttons: [
        {
          title: t.continueNoAdjustImage,
          onClick: () => {
            if (!selectedRunObjectImage)
              addImageToRunObjectGroup().then(() => setCurrentStep(21));
            else setCurrentStep(21);
          },
          frType: "primary",
          disabled: !selectedObjectImage && !selectedRunObjectImage,
        },
        {
          title: t.continueAdjustImage,
          onClick: () => setCurrentStep(12),
          frType: "secondary",
          disabled:
            !selectedObjectImage ||
            selectedObjectImage.url.includes("eros/iiif"), // Hack to prevent resizing eros images while it is not implemented
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
        selectedObjectImage && (
          <AddImageToObjectTransform
            image={selectedObjectImage}
            onTransform={setSelectedImageTransform}
          />
        ),
      buttons: [
        {
          title: t.next,
          onClick: () => {
            setIsAddingRunObjectImage(true);
            addImageToRunObjectGroup()
              .then(() => {
                setCurrentStep(21);
              })
              .finally(() => setIsAddingRunObjectImage(false));
          },
          frType: "primary",
          disabled: !selectedImageTransform || isAddingRunObjectImage,
        },
        {
          title: t.back,
          onClick: () => {
            setCurrentStep(11);
            setSelectedObjectImage(null);
            setSelectedImageTransform(null);
          },
          frType: "secondary",
        },
      ],
    },
    21: {
      // Select measuring point on image
      title: t.pointSelection,
      content: () =>
        selectedRunObjectImage && (
          <AddMeasuringPointToImage
            runObjectImage={selectedRunObjectImage}
            onLocate={setPointLocation}
            measuringPoint={measuringPoint}
          />
        ),
      buttons: [
        ...([
          {
            title: t.save,
            onClick: () =>
              addImageToPoint().then((image) => {
                if (
                  image &&
                  measuringPoint &&
                  (selectedRunObjectImage ||
                    measuringPoint?.image?.runObjectGroupImage)
                )
                  updateMeasuringPointImage(measuringPoint.id, {
                    ...image,
                    runObjectGroupImage:
                      selectedRunObjectImage ||
                      (measuringPoint.image
                        ?.runObjectGroupImage as IRunObjectImage),
                  });
                closeButtonRef.current?.click();
              }),
            frType: "primary",
            disabled: !pointLocation,
          },
          {
            title: t.changeImage,
            onClick: () => setCurrentStep(11),
            frType: "secondary",
          },
        ] as IFooterButton[]),
        ...((measuringPoint?.image
          ? [
              {
                title: t.delete,
                onClick: async () => {
                  setIsDeletingMeasuringPointImage(true);
                  deleteMeasuringPointImage(measuringPoint.id)
                    .then(() => {
                      updateMeasuringPointImage(measuringPoint.id, undefined);
                      closeButtonRef.current?.click();
                    })
                    .finally(() => {
                      setIsDeletingMeasuringPointImage(false);
                    });
                },
                frType: "secondary",
                disabled: isDeletingMeasuringPointImage,
              },
            ]
          : []) as IFooterButton[]),
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
    // Go to 3rd step if has measuring point location
    if (objectGroup) {
      if (currentStep !== 21 && measuringPoint?.image && imageStorage) {
        const { runObjectGroupImage } = measuringPoint.image;
        setPointLocation(measuringPoint.image.pointLocation);
        getToken(true).then((token) => {
          setSelectedRunObjectImage({
            ...runObjectGroupImage,
            url: constructImageStorageUrl(
              runObjectGroupImage.path,
              imageStorage.baseUrl,
              imageStorage.token,
              token,
            ),
            provider: extractProviderFromPath(runObjectGroupImage.path),
          });
          setCurrentStep(21);
        });
      }
      // Go to second step if object group is set
      else if (currentStep !== 11) {
        setCurrentStep(11);
      }
    } else if (currentStep !== 1) {
      resetModal();
      setCurrentStep(1);
    }
  }, [objectGroup, imageStorage, measuringPoint]);

  return (
    <dialog
      aria-labelledby={`${modalId}-title`}
      role="dialog"
      id={modalId}
      className="fr-modal"
    >
      <div className="fr-container fr-container--fluid fr-container-md">
        <div className="fr-grid-row fr-grid-row--center">
          <div>
            <div className="fr-modal__body">
              <div className="fr-modal__header">
                <button
                  className="fr-btn--close fr-btn"
                  title={t.close}
                  aria-controls={modalId}
                  ref={closeButtonRef}
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
