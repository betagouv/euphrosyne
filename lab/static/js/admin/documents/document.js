(function (projectId) {
  function displayProjectDocuments(documentXMLEls) {
    toggleLoading(false);
    const tableBodyEl = document.querySelector("table#document_list tbody");
    tableBodyEl.querySelectorAll(".document-row").forEach((el) => el.remove());
    if (documentXMLEls.length) {
      document.querySelector("tr.no_data").style.display = "none";
      documentXMLEls.forEach((documentEl) => {
        const rowEl = document.createElement("tr");
        rowEl.classList.add("document-row");
        const keyEl = document.createElement("td");
        keyEl.innerText = documentEl
          .querySelector("Key")
          .textContent.split("/")
          .pop();
        const lastModifiedEl = document.createElement("td");
        lastModifiedEl.innerText = new Date(
          documentEl.querySelector("LastModified").textContent
        ).toLocaleDateString();
        const sizeEl = document.createElement("td");
        sizeEl.innerText = formatBytes(
          parseInt(documentEl.querySelector("Size").textContent || "0")
        );
        rowEl.appendChild(keyEl);
        rowEl.appendChild(lastModifiedEl);
        rowEl.appendChild(sizeEl);
        tableBodyEl.appendChild(rowEl);
      });
    } else {
      document.querySelector("tr.no_data").style.display = "";
    }
  }
  function handleListObjectV2Response(event) {
    if (event.target.readyState == 4 && event.target.status == 200) {
      const { response } = event.target;
      const xml = new DOMParser().parseFromString(response, "application/xml");
      const keys = xml.querySelectorAll("Contents");
      displayProjectDocuments(keys);
    }
  }
  function handlePresignedURLResponse(event) {
    if (event.target.readyState == 4 && event.target.status == 200) {
      const { url } = JSON.parse(event.target.response);
      const request = new XMLHttpRequest();
      request.onreadystatechange = handleListObjectV2Response;
      request.open("GET", url, true);
      request.send();
    }
  }
  function fetchDocuments(projectId) {
    const request = new XMLHttpRequest();
    request.onreadystatechange = handlePresignedURLResponse;
    request.open(
      "GET",
      `/api/project/${projectId}/documents/presigned_list_url`,
      true
    );
    request.send();
  }

  function formatBytes(a, b = 2, k = 1024) {
    /**
     * Format bytes int size.
     * Taken from this SO answer : https://stackoverflow.com/a/18650828/7433420
     */
    with (Math) {
      let d = floor(log(a) / log(k));
      return 0 == a
        ? "0 Bytes"
        : parseFloat((a / pow(k, d)).toFixed(max(0, b))) +
            " " +
            ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"][d];
    }
  }

  function toggleLoading(active) {
    if (active) {
      document
        .querySelectorAll("table#document_list tbody tr:not(.loading)")
        .forEach((el) => (el.style.display = "none"));
      document.querySelector(
        "table#document_list tbody tr.loading"
      ).style.display = "";
    } else {
      document
        .querySelectorAll("table#document_list tbody tr:not(.loading)")
        .forEach((el) => (el.style.display = ""));
      document.querySelector(
        "table#document_list tbody tr.loading"
      ).style.display = "none";
    }
  }

  window.addEventListener("DOMContentLoaded", (event) => {
    toggleLoading(true);
    fetchDocuments(projectId);
  });

  document
    .getElementById("upload-form")
    .addEventListener("uploadCompleted", (event) => {
      toggleLoading(true);
      fetchDocuments(projectId);
    });
})(projectId);
