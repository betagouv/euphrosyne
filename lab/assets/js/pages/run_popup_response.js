"use strict";

import handleInitData from "../run-popup-response-handler.js";

{
  const initData = JSON.parse(
    document.getElementById("django-admin-popup-response-constants").dataset
      .popupResponse
  );
  handleInitData(initData);
}
