/*global opener */
"use strict";
{
  const initData = JSON.parse(
    document.getElementById("euphro-admin-popup-response-constants").dataset
      .popupResponse
  );
  opener.dismissViewObjectPopup(window, initData.obj, initData.new_value);
}
