const rangeEl = document.getElementById("calendar-range");
const gridEl = document.getElementById("calendar-grid");
const lengthButtons = document.querySelectorAll(".calendar-length-btn");
const plannedListEl = document.getElementById("recipe-list");
const availableListEl = document.getElementById("available-recipe-list");

const MEAL_SLOTS = ["breakfast", "lunch", "dinner"];
const SLOT_LABELS = { breakfast: "B", lunch: "L", dinner: "D" };

let allRecipes = [];

function formatDateHeading(dateStr) {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
}

// --- Calendar grid ---

function renderGrid(view) {
  rangeEl.textContent = `${formatDateHeading(view.start_date)} - ${formatDateHeading(view.end_date)} (${view.length_weeks} week${view.length_weeks > 1 ? "s" : ""})`;

  gridEl.innerHTML = "";
  for (let i = 0; i < view.days.length; i += 7) {
    const week = view.days.slice(i, i + 7);
    const weekRow = document.createElement("div");
    weekRow.className = "calendar-week-row";

    for (const day of week) {
      const dayCol = document.createElement("div");
      dayCol.className = "calendar-day-col";

      const heading = document.createElement("div");
      heading.className = "calendar-day-heading";
      heading.textContent = formatDateHeading(day.date);
      dayCol.appendChild(heading);

      for (const slot of MEAL_SLOTS) {
        const entry = day[slot];
        const slotRow = document.createElement("div");
        slotRow.className = "calendar-slot-row";

        const label = document.createElement("span");
        label.className = "calendar-slot-label";
        label.textContent = SLOT_LABELS[slot];
        slotRow.appendChild(label);

        const select = document.createElement("select");
        select.className = "calendar-slot-select";
        select.innerHTML =
          `<option value="">--</option>` +
          allRecipes.map((r) => `<option value="${r.id}">${r.title}</option>`).join("");
        select.value = entry ? String(entry.recipe_id) : "";
        select.addEventListener("change", () =>
          handleSlotChange(day.date, slot, select.value, entry ? entry.id : null)
        );
        slotRow.appendChild(select);

        dayCol.appendChild(slotRow);
      }

      weekRow.appendChild(dayCol);
    }
    gridEl.appendChild(weekRow);
  }
}

async function handleSlotChange(dateStr, slot, newRecipeId, existingEntryId) {
  if (newRecipeId) {
    const resp = await fetch("/calendar/entries", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ date: dateStr, meal_slot: slot, recipe_id: parseInt(newRecipeId, 10) }),
    });
    if (!resp.ok) {
      const data = await resp.json();
      window.alert(data.detail || "Couldn't schedule that recipe.");
      return;
    }
  } else if (existingEntryId) {
    await fetch(`/calendar/entries/${existingEntryId}`, { method: "DELETE" });
  }
  loadEverything();
}

lengthButtons.forEach((btn) => {
  btn.addEventListener("click", async () => {
    const weeks = parseInt(btn.dataset.weeks, 10);
    const hasSchedule = gridEl.querySelector(".calendar-slot-select")
      ? Array.from(gridEl.querySelectorAll(".calendar-slot-select")).some((s) => s.value)
      : false;
    if (hasSchedule) {
      const confirmed = window.confirm(
        "Starting a new calendar clears everything currently scheduled. Continue?"
      );
      if (!confirmed) return;
    }
    const resp = await fetch("/calendar/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ length_weeks: weeks }),
    });
    if (resp.ok) {
      loadEverything();
    } else {
      const data = await resp.json();
      window.alert(data.detail || "Couldn't start a new calendar.");
    }
  });
});

// --- Your Plan / Add from your recipes ---

function renderPlanned(recipes) {
  const planned = recipes.filter((r) => r.is_planned);
  if (planned.length === 0) {
    plannedListEl.innerHTML = `<p class="empty-state">Nothing planned yet -- add some below, or schedule one on the calendar above.</p>`;
    return;
  }

  plannedListEl.innerHTML = "";
  for (const recipe of planned) {
    const item = document.createElement("div");
    item.className = "recipe-item";
    const flag = recipe.is_staple || recipe.is_scheduled
      ? ""
      : `<span class="not-scheduled-badge" title="This is on your Plan but isn't scheduled on the calendar yet">Not on calendar</span>`;
    item.innerHTML = `
      <span class="recipe-name">${recipe.title} ${flag}</span>
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
  const available = recipes.filter((r) => !r.is_planned);
  if (available.length === 0) {
    availableListEl.innerHTML = `<p class="empty-state">Everything you've saved is already planned.</p>`;
    return;
  }

  availableListEl.innerHTML = "";
  for (const recipe of available) {
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

async function togglePlan(id) {
  await fetch(`/recipes/${id}/toggle-plan`, { method: "POST" });
  loadEverything();
}

// --- Load everything together, since scheduling can change is_planned ---

async function loadEverything() {
  try {
    const [calendarResponse, recipesResponse] = await Promise.all([
      fetch("/calendar"),
      fetch("/recipes"),
    ]);
    if (!calendarResponse.ok || !recipesResponse.ok) {
      throw new Error(
        `Planner request failed (${calendarResponse.status}/${recipesResponse.status})`
      );
    }
    const view = await calendarResponse.json();
    allRecipes = await recipesResponse.json();

    renderGrid(view);
    renderPlanned(allRecipes);
    renderAvailable(allRecipes);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    rangeEl.textContent = "Planner unavailable";
    gridEl.innerHTML = `<p class="empty-state">Couldn't load your plan (${message}).</p>`;
    plannedListEl.innerHTML = "";
    availableListEl.innerHTML = "";
  }
}

loadEverything();