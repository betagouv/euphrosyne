import "../../../js_tests/_jsdom_mocks/gettext";
import euphrosyneToolsService from "../../assets/js/euphrosyne-tools-service";
import VMSizeSelect from "../../assets/js/components/vm-size-select";

describe("Test VMSizeSelect", () => {
  let vmSizeSelect;
  VMSizeSelect.init();

  beforeEach(() => {
    vi.spyOn(euphrosyneToolsService, "fetchProjectVmSize");
    vi.spyOn(euphrosyneToolsService, "setProjectVmSize");

    vmSizeSelect = new VMSizeSelect();
    vmSizeSelect.setAttribute("project-name", "projet tango");
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("creates the button properly", async () => {
    euphrosyneToolsService.fetchProjectVmSize.mockImplementation(() =>
      Promise.resolve()
    );
    vmSizeSelect.connectedCallback();
    expect(euphrosyneToolsService.fetchProjectVmSize).toHaveBeenCalled();
  });

  it("calls service on change", async () => {
    euphrosyneToolsService.setProjectVmSize.mockImplementation(() =>
      Promise.resolve()
    );
    await vmSizeSelect.onSelectChange({ target: { value: "value" } });
    expect(euphrosyneToolsService.setProjectVmSize).toHaveBeenCalledWith(
      "projet tango",
      "value"
    );
  });
});
