const form = document.getElementById("credit-form");
const result = document.getElementById("result");
const childrenCheckbox = form.querySelector("input[name='has_children']");
const childrenWrapper = document.getElementById("children-count-wrapper");
const childrenInput = form.querySelector("input[name='children_count']");

function toggleChildren() {
  if (childrenCheckbox.checked) {
    childrenWrapper.classList.remove("is-hidden");
    childrenInput.required = true;
  } else {
    childrenWrapper.classList.add("is-hidden");
    childrenInput.required = false;
    childrenInput.value = 0;
  }
}

childrenCheckbox.addEventListener("change", toggleChildren);

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  result.textContent = "Отправляем заявку...";
  result.classList.remove("is-error");

  const formData = new FormData(form);
  const payload = {
    first_name: formData.get("first_name"),
    last_name: formData.get("last_name"),
    age: Number(formData.get("age")),
    gender: formData.get("gender"),
    salary: Number(formData.get("salary")),
    has_children: childrenCheckbox.checked,
    children_count: Number(formData.get("children_count")) || 0,
    debts: Number(formData.get("debts")) || 0,
    has_car: form.querySelector("input[name='has_car']").checked,
  };

  try {
    const response = await fetch("/api/applications", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error("Не удалось отправить заявку");
    }

    const data = await response.json();
    result.textContent = data.message;
    result.classList.toggle("is-error", !data.accepted);
  } catch (error) {
    result.textContent = "Ошибка отправки. Попробуйте позже.";
    result.classList.add("is-error");
  }
});

toggleChildren();
