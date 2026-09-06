const listEl = document.getElementById("recipe-list");
const searchEl = document.getElementById("recipe-search");
const sortEl = document.getElementById("recipe-sort");
let allRecipes = [];

function formatIngredientAmount(ingredient) {
  const quantity = ingredient.quantity == null ? "" : formatAsFraction(ingredient.quantity);
  const amount = [quantity, ingredient.unit].filter(Boolean).join(" ");
  return amount ? `${amount} ${ingredient.name}` : ingredient.name;
}

function sortRecipes(recipes) {
  return [...recipes].sort((first, second) => {
    if (first.is_staple !== second.is_staple) return first.is_staple ? -1 : 1;
    if (sortEl.value === "ingredients") {
      return first.ingredients.length - second.ingredients.length ||
        first.title.localeCompare(second.title);
    }
    if (sortEl.value === "date") {
      return new Date(second.created_at) - new Date(first.created_at) ||
        first.title.localeCompare(second.title);
    }
    return first.title.localeCompare(second.title);
  });
}

function filteredRecipes() {
  const search = searchEl.value.trim().toLowerCase();
  if (!search) return sortRecipes(allRecipes);
  return sortRecipes(allRecipes.filter((recipe) => {
    const values = [recipe.title, ...recipe.ingredients.map((ingredient) => ingredient.name)];
    return values.some((value) => value.toLowerCase().includes(search));
  }));
}

function renderRecipes(recipes) {
  if (recipes.length === 0) {
    const message = searchEl.value.trim() ? "No matching recipes." : "No recipes saved yet. Add one to get started.";
    listEl.innerHTML = `<p class="empty-state">${message}</p>`;
    return;
  }

  listEl.innerHTML = "";
  for (const recipe of recipes) {
    const ingredientText = recipe.ingredients.map(formatIngredientAmount).join(", ");
    const servingsText = recipe.servings ? `Serves ${recipe.servings} · ` : "";
    const card = document.createElement("div");
    card.className = "recipe-card";
    card.innerHTML = `
      <div class="recipe-card-header">
        <div class="recipe-card-title">
          <span class="recipe-name">${recipe.title}</span>
          ${recipe.is_staple ? '<span class="staple-badge">Staples</span>' : ""}
        </div>
        <div class="recipe-card-actions">
          <button type="button" class="toggle-plan-btn ${recipe.is_planned ? "is-planned" : ""}" data-id="${recipe.id}">
            ${recipe.is_planned ? "On your plan" : "Add to Plan"}
          </button>
        </div>
      </div>
      <p class="recipe-ingredients">${servingsText}${ingredientText || "No ingredients listed"}</p>
    `;
    card.querySelector(".toggle-plan-btn").addEventListener("click", () => togglePlan(recipe.id));
    card.querySelector(".recipe-name").addEventListener("click", () =>
      showRecipeModal(recipe, {
        editable: true,
        onUpdated: () => loadRecipes(),
        onDeleted: () => loadRecipes(),
      })
    );
    listEl.appendChild(card);
  }
}

async function loadRecipes() {
  try {
    const response = await fetch("/recipes");
    if (!response.ok) throw new Error("Request failed");
    allRecipes = await response.json();
    renderRecipes(filteredRecipes());
  } catch (err) {
    listEl.innerHTML = `<p class="empty-state">Couldn't load recipes: ${err.message}</p>`;
  }
}

async function togglePlan(id) {
  await fetch(`/recipes/${id}/toggle-plan`, { method: "POST" });
  loadRecipes();
}

searchEl.addEventListener("input", () => renderRecipes(filteredRecipes()));
sortEl.addEventListener("change", () => renderRecipes(filteredRecipes()));

loadRecipes();