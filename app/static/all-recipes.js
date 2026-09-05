const listEl = document.getElementById("recipe-list");

function renderRecipes(recipes) {
  if (recipes.length === 0) {
    listEl.innerHTML = `<p class="empty-state">No recipes saved yet. Add one to get started.</p>`;
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
        <span class="recipe-name">${recipe.title}</span>
        <button
          type="button"
          class="toggle-plan-btn ${recipe.is_planned ? "is-planned" : ""}"
          data-id="${recipe.id}"
        >
          ${recipe.is_planned ? "On your plan" : "Add to Plan"}
        </button>
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
    const recipes = await response.json();
    renderRecipes(recipes);
  } catch (err) {
    listEl.innerHTML = `<p class="empty-state">Couldn't load recipes. Is the server running?</p>`;
  }
}

async function togglePlan(id) {
  await fetch(`/recipes/${id}/toggle-plan`, { method: "POST" });
  loadRecipes();
}

loadRecipes();