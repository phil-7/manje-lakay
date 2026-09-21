const summaryEl = document.getElementById("planned-summary");
const resultsEl = document.getElementById("grocery-results");
const showRecipesCheckbox = document.getElementById("show-recipes-checkbox");
const resetChecklistBtn = document.getElementById("reset-checklist-btn");
const customGroceryForm = document.getElementById("custom-grocery-form");
const customGroceryName = document.getElementById("custom-grocery-name");
const SHOPPING_CHECKED_KEY = "manje-lakay-shopping-checked";
const SHOPPING_RESET_KEY = "manje-lakay-shopping-reset";
let groceryItems = [];

function getCheckedItems() {
  try {
    return JSON.parse(localStorage.getItem(SHOPPING_CHECKED_KEY) || "{}");
  } catch (_error) {
    return {};
  }
}

function saveCheckedItems(checkedItems) {
  localStorage.setItem(SHOPPING_CHECKED_KEY, JSON.stringify(checkedItems));
}

function formatAmount(entry) {
  const qty = entry.quantity != null ? formatAsFraction(entry.quantity) : "";
  return [qty, entry.unit].filter(Boolean).join(" ");
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[character]);
}

function renderGroceryList(items) {
  groceryItems = items;
  const checkedItems = getCheckedItems();
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

    // Each recipe's amount gets its own line, listed vertically. The toggle
    // controls both the amount and recipe name on each line.
    const entryLines = item.entries
      .map((entry) => {
        const amount = formatAmount(entry);
        return `<li><span class="entry-amount">${escapeHtml(amount)}</span><span class="entry-recipe">-- ${escapeHtml(entry.recipe)}</span></li>`;
      })
      .join("");

    row.innerHTML = `
      <input type="checkbox" class="have-it-checkbox" ${checkedItems[item.ingredient] ? "checked" : ""} />
      <div class="grocery-item-text">
        <span class="grocery-item-name">${escapeHtml(item.ingredient)} ${warning}</span>
        <ul class="grocery-item-entries">${entryLines}</ul>
      </div>
    `;
    if (item.custom_id) {
      const removeButton = document.createElement("button");
      removeButton.type = "button";
      removeButton.className = "remove-custom-grocery-btn";
      removeButton.textContent = "Remove";
      removeButton.addEventListener("click", async () => {
        await fetch(`/grocery-list/custom/${item.custom_id}`, { method: "DELETE" });
        loadGroceryList();
      });
      row.appendChild(removeButton);
    }
    const checkbox = row.querySelector(".have-it-checkbox");
    row.classList.toggle("checked-off", checkbox.checked);
    checkbox.addEventListener("change", (e) => {
      row.classList.toggle("checked-off", e.target.checked);
      const currentCheckedItems = getCheckedItems();
      if (e.target.checked) {
        currentCheckedItems[item.ingredient] = true;
      } else {
        delete currentCheckedItems[item.ingredient];
      }
      saveCheckedItems(currentCheckedItems);
    });
    resultsEl.appendChild(row);
  }
}

async function loadGroceryList() {
  resultsEl.innerHTML = `<p class="empty-state">Loading...</p>`;
  try {
    // Always pull the CURRENT plan fresh -- this is what makes the page
    // reflect whatever was most recently checked/unchecked on Planner.
    const [plannedResponse, customResponse] = await Promise.all([
      fetch("/recipes?planned=true"),
      fetch("/grocery-list/custom"),
    ]);
    const plannedRecipes = await plannedResponse.json();
    const customGroceries = await customResponse.json();

    if (plannedRecipes.length === 0 && customGroceries.length === 0) {
      summaryEl.innerHTML = `<p class="empty-state">Nothing planned yet. Add recipes to your Plan first.</p>`;
      resultsEl.innerHTML = "";
      return;
    }

    const summary = plannedRecipes.length
      ? `For: ${plannedRecipes.map((r) => escapeHtml(r.title)).join(", ")}`
      : "Custom groceries only";
    summaryEl.innerHTML = `<p class="hint">${summary}</p>`;

    const recipeIds = plannedRecipes.map((r) => r.id);
    const groceryResponse = await fetch("/grocery-list", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ recipe_ids: recipeIds }),
    });
    const items = await groceryResponse.json();
    const customItems = customGroceries.map((grocery) => ({
      ingredient: grocery.name,
      entries: [],
      mixed_units: false,
      custom_id: grocery.id,
    }));
    renderGroceryList([...items, ...customItems]);
  } catch (err) {
    resultsEl.innerHTML = `<p class="empty-state">Couldn't load your grocery list. Is the server running?</p>`;
  }
}

resetChecklistBtn.addEventListener("click", () => {
  localStorage.removeItem(SHOPPING_CHECKED_KEY);
  renderGroceryList(groceryItems);
});

window.addEventListener("storage", (event) => {
  if (event.key === SHOPPING_RESET_KEY) {
    localStorage.removeItem(SHOPPING_CHECKED_KEY);
    renderGroceryList(groceryItems);
  }
});

showRecipesCheckbox.addEventListener("change", () => {
  resultsEl.classList.toggle("hide-recipe-names", !showRecipesCheckbox.checked);
});

resultsEl.classList.toggle("hide-recipe-names", !showRecipesCheckbox.checked);

customGroceryForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const response = await fetch("/grocery-list/custom", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: customGroceryName.value }),
  });
  if (!response.ok) {
    const data = await response.json();
    window.alert(data.detail || "Couldn't add that grocery.");
    return;
  }
  customGroceryName.value = "";
  loadGroceryList();
});

loadGroceryList();