"use strict";
{
  const initData = JSON.parse(
    document.getElementById("django-admin-popup-response-constants").dataset
      .popupResponse
  );
  switch (initData.action) {
    case "change":
      opener.dismissChangeRelatedRunPopup(
        window,
        initData.value,
        initData.obj,
        initData.new_value,
        initData.new_data
      );
      break;
    case "delete":
      opener.dismissDeleteRelatedRunPopup(window, initData.value);
      break;
    default:
      opener.dismissAddRelatedRunPopup(
        window,
        initData.value,
        initData.obj,
        initData.data
      );
      break;
  }
}
