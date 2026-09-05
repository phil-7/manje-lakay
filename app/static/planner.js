const plannedListEl = document.getElementById("recipe-list");
const availableListEl = document.getElementById("available-recipe-list");

function renderPlanned(recipes) {
  if (recipes.length === 0) {
    plannedListEl.innerHTML = `<p class="empty-state">Nothing planned yet -- add some below.</p>`;
    return;
  }

  plannedListEl.innerHTML = "";
  for (const recipe of recipes) {
    const item = document.createElement("div");
    item.className = "recipe-item";
    item.innerHTML = `
      <span class="recipe-name">${recipe.title}</span>
      <button type="button" class="unplan-btn" data-id="${recipe.id}">Unplan</button>
    `;
    item.querySelector(".recipe-name").addEventListener("click", () =>
      showRecipeModal(recipe, { editable: false })
    );
    item.querySelector(".unplan-btn").addEventListener("click", () => togglePlan(recipe.id));
    plannedListEl.appendChild(item);
  }
}

function renderAvailable(recipes) {
  if (recipes.length === 0) {
    availableListEl.innerHTML = `<p class="empty-state">Everything you've saved is already planned.</p>`;
    return;
  }

  availableListEl.innerHTML = "";
  for (const recipe of recipes) {
    const item = document.createElement("div");
    item.className = "recipe-item";
    item.innerHTML = `
      <span class="recipe-name">${recipe.title}</span>
      <button type="button" class="toggle-plan-btn" data-id="${recipe.id}">Add to Plan</button>
    `;
    item.querySelector(".recipe-name").addEventListener("click", () =>
      showRecipeModal(recipe, { editable: false })
    );
    item.querySelector(".toggle-plan-btn").addEventListener("click", () => togglePlan(recipe.id));
    availableListEl.appendChild(item);
  }
}

async function loadBothLists() {
  try {
    const [plannedResponse, availableResponse] = await Promise.all([
      fetch("/recipes?planned=true"),
      fetch("/recipes?planned=false"),
    ]);
    renderPlanned(await plannedResponse.json());
    renderAvailable(await availableResponse.json());
  } catch (err) {
    plannedListEl.innerHTML = `<p class="empty-state">Couldn't load your plan. Is the server running?</p>`;
    availableListEl.innerHTML = "";
  }
}

async function togglePlan(id) {
  await fetch(`/recipes/${id}/toggle-plan`, { method: "POST" });
  loadBothLists();
}

loadBothLists();