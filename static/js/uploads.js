const uploadForm = document.querySelector("[data-upload-form]");

if (uploadForm) {
  const input = uploadForm.querySelector("[data-upload-input]");
  const queue = uploadForm.querySelector("[data-upload-queue]");
  const maximumFiles = Number(uploadForm.dataset.maxFiles);

  const uploadKey = (file) => `${uploadForm.action}:${file.name}:${file.size}:${file.lastModified}`;
  const uploadId = (file) => {
    const key = uploadKey(file);
    let id = sessionStorage.getItem(key);
    if (!id) {
      id = crypto.randomUUID();
      sessionStorage.setItem(key, id);
    }
    return id;
  };

  const uploadFile = (file) => new Promise((resolve) => {
    const row = document.createElement("div");
    row.className = "upload-row";
    row.innerHTML = '<span class="upload-name"></span><progress max="100" value="0"></progress><span class="upload-status">Waiting</span>';
    row.querySelector(".upload-name").textContent = file.name;
    queue.append(row);

    const request = new XMLHttpRequest();
    const formData = new FormData();
    formData.append("csrfmiddlewaretoken", uploadForm.querySelector("[name=csrfmiddlewaretoken]").value);
    formData.append("upload_id", uploadId(file));
    formData.append("photos", file);
    request.open("POST", uploadForm.action);
    request.setRequestHeader("Accept", "application/json");
    request.upload.addEventListener("progress", (event) => {
      if (event.lengthComputable) row.querySelector("progress").value = (event.loaded / event.total) * 100;
    });
    request.addEventListener("load", () => {
      let message = request.status >= 200 && request.status < 300 ? "Ready" : "Upload failed";
      try {
        const result = JSON.parse(request.responseText);
        if (result.errors?.length) message = result.errors[0].message;
      } catch {}
      row.querySelector(".upload-status").textContent = message;
      row.classList.toggle("upload-error", request.status < 200 || request.status >= 300);
      sessionStorage.removeItem(uploadKey(file));
      resolve(request.status >= 200 && request.status < 300);
    });
    request.addEventListener("error", () => {
      row.querySelector(".upload-status").textContent = "Network error. Try again.";
      row.classList.add("upload-error");
      resolve(false);
    });
    request.send(formData);
  });

  input.addEventListener("change", async () => {
    const files = [...input.files];
    if (!files.length) return;
    queue.replaceChildren();
    queue.hidden = false;
    if (files.length > maximumFiles) {
      const row = document.createElement("div");
      row.className = "upload-row upload-error";
      row.innerHTML = '<span class="upload-name">Too many files selected</span><span class="upload-status"></span>';
      row.querySelector(".upload-status").textContent = `Choose no more than ${maximumFiles} at once.`;
      queue.append(row);
      input.value = "";
      return;
    }
    input.disabled = true;
    let succeeded = 0;
    for (const file of files) succeeded += Number(await uploadFile(file));
    const allSucceeded = succeeded === files.length;
    if (allSucceeded) location.reload();
    else if (succeeded) {
      const refresh = document.createElement("button");
      refresh.className = "button secondary upload-refresh";
      refresh.type = "button";
      refresh.textContent = `Show ${succeeded} uploaded photo${succeeded === 1 ? "" : "s"}`;
      refresh.addEventListener("click", () => location.reload());
      queue.append(refresh);
    }
    input.disabled = false;
    input.value = "";
  });
}