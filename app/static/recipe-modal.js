(function () {
  let overlayEl = null;

  function closeModal() {
    if (overlayEl) {
      overlayEl.remove();
      overlayEl = null;
    }
  }

  function clearModal() {
    const modal = overlayEl.querySelector(".recipe-modal");
    modal.innerHTML = "";
    return modal;
  }

  function makeCloseButton() {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "modal-close";
    btn.setAttribute("aria-label", "Close");
    btn.textContent = "\u00d7";
    btn.addEventListener("click", closeModal);
    return btn;
  }

  function renderView(recipe, options) {
    const modal = clearModal();
    modal.appendChild(makeCloseButton());

    const h2 = document.createElement("h2");
    h2.textContent = recipe.title;
    modal.appendChild(h2);

    const ingHeading = document.createElement("h3");
    ingHeading.textContent = "Ingredients";
    modal.appendChild(ingHeading);

    const ingP = document.createElement("p");
    ingP.textContent = recipe.ingredients.length
      ? recipe.ingredients.map((i) => i.name).join(", ")
      : "No ingredients listed";
    modal.appendChild(ingP);

    const insHeading = document.createElement("h3");
    insHeading.textContent = "Instructions";
    modal.appendChild(insHeading);

    const insP = document.createElement("p");
    insP.className = "modal-instructions";
    insP.textContent = recipe.instructions || "No instructions yet.";
    modal.appendChild(insP);

    if (options.editable) {
      const actions = document.createElement("div");
      actions.className = "modal-actions";

      const editBtn = document.createElement("button");
      editBtn.type = "button";
      editBtn.className = "submit-btn";
      editBtn.textContent = "Edit";
      editBtn.addEventListener("click", () => renderEditForm(recipe, options));

      const deleteBtn = document.createElement("button");
      deleteBtn.type = "button";
      deleteBtn.className = "modal-delete-btn";
      deleteBtn.textContent = "Delete";
      deleteBtn.addEventListener("click", async () => {
        if (!window.confirm(`Delete "${recipe.title}"? This can't be undone.`)) return;
        const resp = await fetch(`/recipes/${recipe.id}`, { method: "DELETE" });
        if (resp.ok) {
          closeModal();
          if (options.onDeleted) options.onDeleted(recipe.id);
        } else {
          window.alert("Couldn't delete this recipe.");
        }
      });

      actions.appendChild(editBtn);
      actions.appendChild(deleteBtn);
      modal.appendChild(actions);
    }
  }

  function renderEditForm(recipe, options) {
    const modal = clearModal();
    modal.appendChild(makeCloseButton());

    const h2 = document.createElement("h2");
    h2.textContent = "Edit Recipe";
    modal.appendChild(h2);

    const titleLabel = document.createElement("label");
    titleLabel.textContent = "Title";
    const titleInput = document.createElement("input");
    titleInput.type = "text";
    titleInput.value = recipe.title;
    titleLabel.appendChild(titleInput);
    modal.appendChild(titleLabel);

    const ingLabel = document.createElement("label");
    ingLabel.textContent = "Ingredients (one per line)";
    const ingTextarea = document.createElement("textarea");
    ingTextarea.rows = 6;
    ingTextarea.value = recipe.ingredients.map((i) => i.name).join("\n");
    ingLabel.appendChild(ingTextarea);
    modal.appendChild(ingLabel);

    const insLabel = document.createElement("label");
    insLabel.textContent = "Instructions";
    const insTextarea = document.createElement("textarea");
    insTextarea.rows = 6;
    insTextarea.value = recipe.instructions || "";
    insLabel.appendChild(insTextarea);
    modal.appendChild(insLabel);

    const messageEl = document.createElement("p");
    messageEl.className = "message";
    modal.appendChild(messageEl);

    const actions = document.createElement("div");
    actions.className = "modal-actions";

    const saveBtn = document.createElement("button");
    saveBtn.type = "button";
    saveBtn.className = "submit-btn";
    saveBtn.textContent = "Save";
    saveBtn.addEventListener("click", async () => {
      const title = titleInput.value;
      const instructions = insTextarea.value.trim() || null;
      const ingredient_names = ingTextarea.value
        .split("\n")
        .map((s) => s.trim())
        .filter(Boolean);
      try {
        const resp = await fetch(`/recipes/${recipe.id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title, instructions, ingredient_names }),
        });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.detail || "Something went wrong.");
        closeModal();
        if (options.onUpdated) options.onUpdated(data);
      } catch (err) {
        messageEl.textContent = err.message;
        messageEl.className = "message error";
      }
    });

    const cancelBtn = document.createElement("button");
    cancelBtn.type = "button";
    cancelBtn.className = "modal-cancel-btn";
    cancelBtn.textContent = "Cancel";
    cancelBtn.addEventListener("click", () => renderView(recipe, options));

    actions.appendChild(saveBtn);
    actions.appendChild(cancelBtn);
    modal.appendChild(actions);
  }

  // options: { editable: bool, onUpdated: fn(updatedRecipe), onDeleted: fn(id) }
  window.showRecipeModal = function (recipe, options = {}) {
    closeModal();
    overlayEl = document.createElement("div");
    overlayEl.className = "modal-overlay";
    const modal = document.createElement("div");
    modal.className = "recipe-modal";
    overlayEl.appendChild(modal);
    overlayEl.addEventListener("click", (e) => {
      if (e.target === overlayEl) closeModal();
    });
    document.body.appendChild(overlayEl);
    renderView(recipe, options);
  };
})();