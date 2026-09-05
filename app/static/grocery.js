const summaryEl = document.getElementById("planned-summary");
const resultsEl = document.getElementById("grocery-results");

function renderGroceryList(items) {
  if (items.length === 0) {
    resultsEl.innerHTML = `<p class="empty-state">No ingredients yet -- your plan is either empty, or its recipes have none.</p>`;
    return;
  }

  resultsEl.innerHTML = "";
  for (const item of items) {
    const row = document.createElement("div");
    row.className = "grocery-item";
    row.innerHTML = `
      <input type="checkbox" class="have-it-checkbox" />
      <div class="grocery-item-text">
        <span class="grocery-item-name">${item.ingredient}</span>
        <span class="grocery-item-recipes">${item.recipes.join(", ")}</span>
      </div>
    `;
    // Purely visual, in-memory state for this shopping trip -- checking an
    // item off does not save anything, and resets on refresh/reload.
    row.querySelector(".have-it-checkbox").addEventListener("change", (e) => {
      row.classList.toggle("checked-off", e.target.checked);
    });
    resultsEl.appendChild(row);
  }
}

async function loadGroceryList() {
  resultsEl.innerHTML = `<p class="empty-state">Loading...</p>`;
  try {
    // Always pull the CURRENT plan fresh -- this is what makes the page
    // reflect whatever was most recently checked/unchecked on Planner.
    const plannedResponse = await fetch("/recipes?planned=true");
    const plannedRecipes = await plannedResponse.json();

    if (plannedRecipes.length === 0) {
      summaryEl.innerHTML = `<p class="empty-state">Nothing planned yet. Add recipes to your Plan first.</p>`;
      resultsEl.innerHTML = "";
      return;
    }

    summaryEl.innerHTML = `<p class="hint">For: ${plannedRecipes.map((r) => r.title).join(", ")}</p>`;

    const recipeIds = plannedRecipes.map((r) => r.id);
    const groceryResponse = await fetch("/grocery-list", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ recipe_ids: recipeIds }),
    });
    const items = await groceryResponse.json();
    renderGroceryList(items);
  } catch (err) {
    resultsEl.innerHTML = `<p class="empty-state">Couldn't load your grocery list. Is the server running?</p>`;
  }
}

loadGroceryList();