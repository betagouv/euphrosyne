import { tabClickHandler, handleModalClose } from "./tabs.js";

describe("Test tabClickHandler", () => {
  describe("Nothing has changed", () => {
    it("returns !false when nothing has changed", () => {
      const newFormData = "a",
        initialFormData = "a";

      expect(tabClickHandler(initialFormData, newFormData, {}, {})).toEqual(
        undefined,
      );
    });
  });
  describe("Form data has changed", () => {
    let newFormData, initialFormData, modalMock, eventMock, discloseFn, dsfr;
    beforeEach(() => {
      newFormData = "a";
      initialFormData = "b";
      modalMock = {
        dataset: {
          nextUrl: "some url",
        },
      };
      eventMock = {
        preventDefault: vi.fn(),
        target: {
          href: "href",
        },
      };
      discloseFn = vi.fn();
      dsfr = global.dsfr;
      global.dsfr = vi.fn();
      global.dsfr.mockReturnValue({
        modal: {
          disclose: discloseFn,
        },
      });
    });
    afterEach(() => {
      global.dsfr = dsfr;
    });

    it("returns false when form data changed", () => {
      expect(
        tabClickHandler(initialFormData, newFormData, modalMock, eventMock),
      ).toEqual(false);
    });
    it("calls dsfr modal disclose", () => {
      tabClickHandler(initialFormData, newFormData, modalMock, eventMock);
      expect(discloseFn).toHaveBeenCalled();
    });
  });
});

describe("Test handleModalClose", () => {
  it("conceals the modal", () => {
    const modal = {},
      concealMock = vi.fn();
    global.dsfr = vi.fn();
    global.dsfr.mockReturnValue({
      modal: {
        conceal: concealMock,
      },
    });

    handleModalClose(modal);

    expect(concealMock).toHaveBeenCalled();
  });
});
