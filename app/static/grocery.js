const summaryEl = document.getElementById("planned-summary");
const resultsEl = document.getElementById("grocery-results");
const showRecipesCheckbox = document.getElementById("show-recipes-checkbox");

function formatAmount(entry) {
  const qty = entry.quantity != null ? formatAsFraction(entry.quantity) : "";
  return [qty, entry.unit].filter(Boolean).join(" ");
}

function renderGroceryList(items) {
  if (items.length === 0) {
    resultsEl.innerHTML = `<p class="empty-state">No ingredients yet -- your plan is either empty, or its recipes have none.</p>`;
    return;
  }

  resultsEl.innerHTML = "";
  for (const item of items) {
    const row = document.createElement("div");
    row.className = "grocery-item";

    const warning = item.mixed_units
      ? `<span class="mixed-units-badge" title="These use different unit types (e.g. volume vs. weight) and aren't combined automatically">Mixed units</span>`
      : "";

    // Each recipe's amount gets its own line, listed vertically -- the
    // "entry-recipe" span is what the show/hide toggle controls.
    const entryLines = item.entries
      .map((entry) => {
        const amount = formatAmount(entry);
        return `<li>${amount ? amount + " " : ""}<span class="entry-recipe">-- ${entry.recipe}</span></li>`;
      })
      .join("");

    row.innerHTML = `
      <input type="checkbox" class="have-it-checkbox" />
      <div class="grocery-item-text">
        <span class="grocery-item-name">${item.ingredient} ${warning}</span>
        <ul class="grocery-item-entries">${entryLines}</ul>
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

showRecipesCheckbox.addEventListener("change", () => {
  resultsEl.classList.toggle("hide-recipe-names", !showRecipesCheckbox.checked);
});

loadGroceryList();