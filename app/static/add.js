// Same-origin now that FastAPI serves this frontend directly -- no need
// for an absolute URL or a hardcoded port.
const API_BASE = "";

const scrapeForm = document.getElementById("scrape-form");
const manualForm = document.getElementById("manual-form");
const tabScrape = document.getElementById("tab-scrape");
const tabManual = document.getElementById("tab-manual");
const messageEl = document.getElementById("message");
const ingredientRows = document.getElementById("ingredient-rows");
const addIngredientBtn = document.getElementById("add-ingredient");
enableTitleCase(document.getElementById("manual-title"));

// --- Tab switching ---
function showTab(tab) {
  const showingScrape = tab === "scrape";
  scrapeForm.classList.toggle("active", showingScrape);
  manualForm.classList.toggle("active", !showingScrape);
  tabScrape.classList.toggle("active", showingScrape);
  tabManual.classList.toggle("active", !showingScrape);
  clearMessage();
}
tabScrape.addEventListener("click", () => showTab("scrape"));
tabManual.addEventListener("click", () => showTab("manual"));

// --- Message display ---
function showMessage(text, type) {
  messageEl.textContent = text;
  messageEl.className = `message ${type}`;
}
function clearMessage() {
  messageEl.textContent = "";
  messageEl.className = "message";
}

// --- Dynamic ingredient rows: same structured quantity/unit/name fields
// used in the scrape-review popup and the edit modal (from
// ingredient-fields.js), so manual entry can't produce "weird lines"
// the parser might misread -- the user picks quantity/unit directly. ---
function addIngredientRow(ing) {
  const row = makeIngredientEditRow(ing);
  row.querySelector(".remove-ingredient").addEventListener("click", () => {
    // Always leave at least one row so the form never looks broken/empty.
    if (ingredientRows.children.length > 1) {
      row.remove();
    } else {
      row.querySelectorAll("input").forEach((input) => (input.value = ""));
      row.querySelector(".ing-unit-select").value = "";
    }
  });
  ingredientRows.appendChild(row);
}

function resetIngredientRows() {
  ingredientRows.innerHTML = "";
  addIngredientRow(null);
}

addIngredientBtn.addEventListener("click", () => addIngredientRow(null));
resetIngredientRows(); // start with one blank row

// --- Submit handlers ---
scrapeForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const url = document.getElementById("scrape-url").value.trim();
  const submitBtn = scrapeForm.querySelector(".submit-btn");

  submitBtn.disabled = true;
  clearMessage();
  try {
    const response = await fetch(`${API_BASE}/recipes/scrape-preview`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const preview = await response.json();
    if (!response.ok) {
      throw new Error(preview.detail || "Something went wrong.");
    }
    // Nothing is saved yet -- the popup lets the user review/fix/add
    // ingredients before anything touches the database.
    showScrapePreviewModal(preview, {
      onConfirmed: (savedRecipe) => {
        showMessage(
          `Saved "${savedRecipe.title}" with ${savedRecipe.ingredients.length} ingredients.`,
          "success"
        );
        scrapeForm.reset();
      },
    });
  } catch (err) {
    showMessage(err.message, "error");
  } finally {
    submitBtn.disabled = false;
  }
});

manualForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const title = document.getElementById("manual-title").value.trim();
  const instructions = document.getElementById("manual-instructions").value.trim();
  const servingsRaw = document.getElementById("manual-servings").value;
  const servings = servingsRaw ? parseInt(servingsRaw, 10) : null;
  const ingredients = Array.from(ingredientRows.querySelectorAll(".ingredient-edit-row"))
    .map(readIngredientEditRow)
    .filter(Boolean);
  const submitBtn = manualForm.querySelector(".submit-btn");

  submitBtn.disabled = true;
  clearMessage();
  try {
    const response = await fetch(`${API_BASE}/recipes/manual`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title,
        instructions: instructions || null,
        servings,
        ingredients,
      }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Something went wrong.");
    }
    showMessage(`Saved "${data.title}" with ${data.ingredients.length} ingredients.`, "success");
    manualForm.reset();
    resetIngredientRows();
  } catch (err) {
    showMessage(err.message, "error");
  } finally {
    submitBtn.disabled = false;
  }
});