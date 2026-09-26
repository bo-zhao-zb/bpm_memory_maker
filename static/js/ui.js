for (const button of document.querySelectorAll("[data-password-toggle]")) {
  const input = document.getElementById(button.getAttribute("aria-controls"));
  if (!(input instanceof HTMLInputElement) || input.type !== "password") continue;

  button.hidden = false;
  button.addEventListener("click", () => {
    const visible = input.type === "password";
    input.type = visible ? "text" : "password";
    button.setAttribute("aria-pressed", String(visible));
    button.setAttribute("aria-label", visible ? "Hide password" : "Show password");
    button.title = visible ? "Hide password" : "Show password";
    button.querySelector("[data-password-show]").hidden = visible;
    button.querySelector("[data-password-hide]").hidden = !visible;
  });
}

for (const form of document.querySelectorAll("form[data-confirm]")) {
  form.addEventListener("submit", (event) => {
    if (!confirm(form.dataset.confirm)) event.preventDefault();
  });
}