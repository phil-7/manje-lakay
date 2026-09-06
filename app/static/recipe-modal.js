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

  function openOverlay(renderFn) {
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
    renderFn();
  }

  // --- Ingredient rows: shared builder from ingredient-fields.js, plus
  // the add/remove wiring both the edit form and the scrape review popup need ---

  function buildIngredientRowsSection(modal, initialIngredients) {
    const rowsContainer = document.createElement("div");
    rowsContainer.className = "ingredient-edit-rows";

    function wireRemoveButton(row) {
      row.querySelector(".remove-ingredient").addEventListener("click", () => {
        if (rowsContainer.children.length > 1) {
          row.remove();
        } else {
          row.querySelectorAll("input").forEach((input) => (input.value = ""));
        }
      });
    }

    const seedIngredients = initialIngredients.length ? initialIngredients : [null];
    for (const ing of seedIngredients) {
      const row = makeIngredientEditRow(ing);
      wireRemoveButton(row);
      rowsContainer.appendChild(row);
    }
    modal.appendChild(rowsContainer);

    const addBtn = document.createElement("button");
    addBtn.type = "button";
    addBtn.className = "add-ingredient";
    addBtn.textContent = "+ Add ingredient";
    addBtn.addEventListener("click", () => {
      const row = makeIngredientEditRow(null);
      wireRemoveButton(row);
      rowsContainer.appendChild(row);
    });
    modal.appendChild(addBtn);

    return rowsContainer;
  }

  function readAllIngredientRows(rowsContainer) {
    return Array.from(rowsContainer.querySelectorAll(".ingredient-edit-row"))
      .map(readIngredientEditRow)
      .filter(Boolean);
  }

  function addFractionBanner(modal) {
    const banner = document.createElement("p");
    banner.className = "hint fraction-banner";
    banner.textContent =
      'Use standard fractions like "1/2" or "1 1/4", not decimals like ".5" or ".333".';
    modal.appendChild(banner);
  }

  // --- Read-only recipe view (Planner: no edit/delete; All Recipes: with them) ---

  function renderView(recipe, options) {
    const modal = clearModal();
    modal.appendChild(makeCloseButton());

    const h2 = document.createElement("h2");
    h2.textContent = recipe.title;
    modal.appendChild(h2);

    if (recipe.source_url) {
      try {
        const sourceUrl = new URL(recipe.source_url);
        if (sourceUrl.protocol === "http:" || sourceUrl.protocol === "https:") {
          const sourceLink = document.createElement("a");
          sourceLink.className = "modal-source-link";
          sourceLink.href = sourceUrl.href;
          sourceLink.target = "_blank";
          sourceLink.rel = "noopener noreferrer";
          sourceLink.textContent = recipe.title;
          sourceLink.setAttribute("aria-label", `Open ${recipe.title} source`);
          modal.appendChild(sourceLink);
        }
      } catch (_error) {}
    }

    if (recipe.servings) {
      const servingsP = document.createElement("p");
      servingsP.className = "modal-servings";
      servingsP.textContent = `Serves ${recipe.servings}`;
      modal.appendChild(servingsP);
    }

    const ingHeading = document.createElement("h3");
    ingHeading.textContent = "Ingredients";
    modal.appendChild(ingHeading);

    if (recipe.ingredients.length) {
      const ul = document.createElement("ul");
      ul.className = "modal-ingredient-list";
      for (const ing of recipe.ingredients) {
        const li = document.createElement("li");
        li.textContent = formatIngredientAmount(ing);
        ul.appendChild(li);
      }
      modal.appendChild(ul);
    } else {
      const p = document.createElement("p");
      p.textContent = "No ingredients listed";
      modal.appendChild(p);
    }

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
    titleInput.setAttribute("autocapitalize", "words");
    titleInput.value = recipe.title;
    enableTitleCase(titleInput);
    titleLabel.appendChild(titleInput);
    modal.appendChild(titleLabel);

    const urlLabel = document.createElement("label");
    urlLabel.textContent = "Recipe URL (optional)";
    const urlInput = document.createElement("input");
    urlInput.type = "url";
    urlInput.value = recipe.source_url || "";
    urlLabel.appendChild(urlInput);
    modal.appendChild(urlLabel);

    const servingsLabel = document.createElement("label");
    servingsLabel.textContent = "Servings";
    const servingsInput = document.createElement("input");
    servingsInput.type = "number";
    servingsInput.min = "1";
    servingsInput.step = "1";
    servingsInput.value = recipe.servings != null ? recipe.servings : "";
    servingsLabel.appendChild(servingsInput);
    modal.appendChild(servingsLabel);

    const ingLabel = document.createElement("label");
    ingLabel.textContent = "Ingredients";
    modal.appendChild(ingLabel);
    addFractionBanner(modal);
    const rowsContainer = buildIngredientRowsSection(modal, recipe.ingredients);

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
      const source_url = urlInput.value.trim() || null;
      const servingsRaw = servingsInput.value;
      const servings = servingsRaw ? parseInt(servingsRaw, 10) : null;
      const instructions = insTextarea.value.trim() || null;
      const ingredients = readAllIngredientRows(rowsContainer);

      try {
        const resp = await fetch(`/recipes/${recipe.id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title, source_url, instructions, servings, ingredients }),
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

  // --- Scrape review popup: shown after scraping, before anything is saved ---

  function renderScrapeReview(preview, options) {
    const modal = clearModal();
    modal.appendChild(makeCloseButton());

    const h2 = document.createElement("h2");
    h2.textContent = "Review Scraped Recipe";
    modal.appendChild(h2);

    const p = document.createElement("p");
    p.className = "hint";
    p.textContent = "Check what was pulled in below, fix anything that's wrong, and add anything that's missing.";
    modal.appendChild(p);

    const titleLabel = document.createElement("label");
    titleLabel.textContent = "Title";
    const titleInput = document.createElement("input");
    titleInput.type = "text";
    titleInput.setAttribute("autocapitalize", "words");
    titleInput.value = preview.title;
    enableTitleCase(titleInput);
    titleLabel.appendChild(titleInput);
    modal.appendChild(titleLabel);

    const servingsLabel = document.createElement("label");
    servingsLabel.textContent = "Servings";
    const servingsInput = document.createElement("input");
    servingsInput.type = "number";
    servingsInput.min = "1";
    servingsInput.step = "1";
    servingsInput.value = preview.servings != null ? preview.servings : "";
    servingsLabel.appendChild(servingsInput);
    modal.appendChild(servingsLabel);

    const urlLabel = document.createElement("label");
    urlLabel.textContent = "Recipe URL";
    const urlInput = document.createElement("input");
    urlInput.type = "url";
    urlInput.required = true;
    urlInput.value = preview.source_url || "";
    urlLabel.appendChild(urlInput);
    modal.appendChild(urlLabel);

    const ingLabel = document.createElement("label");
    ingLabel.textContent = "Ingredients";
    modal.appendChild(ingLabel);
    addFractionBanner(modal);
    const rowsContainer = buildIngredientRowsSection(modal, preview.ingredients);

    const insLabel = document.createElement("label");
    insLabel.textContent = "Instructions (optional)";
    const insTextarea = document.createElement("textarea");
    insTextarea.rows = 6;
    insTextarea.value = preview.instructions || "";
    insLabel.appendChild(insTextarea);
    modal.appendChild(insLabel);

    const messageEl = document.createElement("p");
    messageEl.className = "message";
    modal.appendChild(messageEl);

    const actions = document.createElement("div");
    actions.className = "modal-actions";

    const confirmBtn = document.createElement("button");
    confirmBtn.type = "button";
    confirmBtn.className = "submit-btn";
    confirmBtn.textContent = "Confirm & Save";
    confirmBtn.addEventListener("click", async () => {
      const title = titleInput.value;
      const source_url = urlInput.value.trim() || null;
      const servingsRaw = servingsInput.value;
      const servings = servingsRaw ? parseInt(servingsRaw, 10) : null;
      const instructions = insTextarea.value.trim() || null;
      const ingredients = readAllIngredientRows(rowsContainer);

      try {
        const resp = await fetch("/recipes/scrape-confirm", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            title,
            instructions,
            servings,
            source_url,
            ingredients,
          }),
        });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.detail || "Something went wrong.");
        closeModal();
        if (options.onConfirmed) options.onConfirmed(data);
      } catch (err) {
        messageEl.textContent = err.message;
        messageEl.className = "message error";
      }
    });

    const cancelBtn = document.createElement("button");
    cancelBtn.type = "button";
    cancelBtn.className = "modal-cancel-btn";
    cancelBtn.textContent = "Discard";
    cancelBtn.addEventListener("click", closeModal);

    actions.appendChild(confirmBtn);
    actions.appendChild(cancelBtn);
    modal.appendChild(actions);
  }

  // options: { editable: bool, onUpdated: fn(updatedRecipe), onDeleted: fn(id) }
  window.showRecipeModal = function (recipe, options = {}) {
    openOverlay(() => renderView(recipe, options));
  };

  // options: { onConfirmed: fn(savedRecipe) }
  window.showScrapePreviewModal = function (preview, options = {}) {
    openOverlay(() => renderScrapeReview(preview, options));
  };
})();