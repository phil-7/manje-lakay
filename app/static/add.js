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

// --- Dynamic ingredient rows ---
function makeIngredientRow() {
  const row = document.createElement("div");
  row.className = "ingredient-row";
  row.innerHTML = `
    <input type="text" class="ingredient-input" placeholder="e.g. garlic" />
    <button type="button" class="remove-ingredient">&times;</button>
  `;
  row.querySelector(".remove-ingredient").addEventListener("click", () => {
    // Always leave at least one row so the form never looks broken/empty.
    if (ingredientRows.children.length > 1) {
      row.remove();
    } else {
      row.querySelector(".ingredient-input").value = "";
    }
  });
  return row;
}

addIngredientBtn.addEventListener("click", () => {
  ingredientRows.appendChild(makeIngredientRow());
});

// Wire up the remove button on the one row that ships in the HTML.
ingredientRows.querySelector(".remove-ingredient").addEventListener("click", () => {
  const inputs = ingredientRows.querySelectorAll(".ingredient-input");
  if (ingredientRows.children.length > 1) {
    ingredientRows.children[0].remove();
  } else {
    inputs[0].value = "";
  }
});

function getIngredientNames() {
  return Array.from(ingredientRows.querySelectorAll(".ingredient-input"))
    .map((input) => input.value.trim())
    .filter((value) => value.length > 0);
}

// --- Submit handlers ---
scrapeForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const url = document.getElementById("scrape-url").value.trim();
  const submitBtn = scrapeForm.querySelector(".submit-btn");

  submitBtn.disabled = true;
  clearMessage();
  try {
    const response = await fetch(`${API_BASE}/recipes/scrape`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Something went wrong.");
    }
    showMessage(`Saved "${data.title}" with ${data.ingredients.length} ingredients.`, "success");
    scrapeForm.reset();
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
  const ingredient_names = getIngredientNames();
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
        ingredient_names,
      }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Something went wrong.");
    }
    showMessage(`Saved "${data.title}" with ${data.ingredients.length} ingredients.`, "success");
    manualForm.reset();
    // Collapse ingredient rows back down to a single empty one.
    ingredientRows.innerHTML = "";
    ingredientRows.appendChild(makeIngredientRow());
  } catch (err) {
    showMessage(err.message, "error");
  } finally {
    submitBtn.disabled = false;
  }
});