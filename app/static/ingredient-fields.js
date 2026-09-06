// Common cooking units for the dropdown. "" means no unit (whole items,
// e.g. "2 eggs"). Anything not in this list falls back to a free-text
// field via the "Other" option, so nothing typed/scraped is ever lost.
const UNIT_OPTIONS = [
  { value: "", label: "(none)" },
  { value: "tsp", label: "tsp" },
  { value: "tbsp", label: "tbsp" },
  { value: "cup", label: "cup" },
  { value: "fl oz", label: "fl oz" },
  { value: "pint", label: "pint" },
  { value: "quart", label: "quart" },
  { value: "gallon", label: "gallon" },
  { value: "ml", label: "ml" },
  { value: "l", label: "l" },
  { value: "g", label: "g" },
  { value: "kg", label: "kg" },
  { value: "oz", label: "oz" },
  { value: "lb", label: "lb" },
  { value: "pinch", label: "pinch" },
  { value: "clove", label: "clove" },
  { value: "sprig", label: "sprig" },
  { value: "slice", label: "slice" },
  { value: "stalk", label: "stalk" },
  { value: "can", label: "can" },
];

const FRACTION_DENOMINATORS = [16, 8, 4, 3, 2];

function gcd(a, b) {
  return b === 0 ? a : gcd(b, a % b);
}

// Turns a decimal (0.5) into a standard cooking fraction string ("1/2").
// Only used for DISPLAY -- storage stays a plain float.
function formatAsFraction(value) {
  if (value === null || value === undefined) return "";
  const whole = Math.floor(value);
  const remainder = value - whole;

  if (remainder < 1 / 32) return String(whole);
  if (1 - remainder < 1 / 32) return String(whole + 1);

  let best = null;
  let bestError = Infinity;
  for (const den of FRACTION_DENOMINATORS) {
    const num = Math.round(remainder * den);
    if (num === 0 || num === den) continue;
    const error = Math.abs(num / den - remainder);
    if (error < bestError) {
      const divisor = gcd(num, den);
      bestError = error;
      best = { num: num / divisor, den: den / divisor };
    }
  }

  if (!best) return String(value);
  const fracStr = `${best.num}/${best.den}`;
  return whole ? `${whole} ${fracStr}` : fracStr;
}

// Parses user-typed quantity text -- accepts "1/2", "1 1/2", or plain
// decimals like "2" or "1.5". Returns null if it can't make sense of it.
function parseFractionInput(input) {
  if (input === null || input === undefined) return null;
  const str = String(input).trim();
  if (!str) return null;

  const mixed = str.match(/^(\d+)\s+(\d+)\/(\d+)$/);
  if (mixed) {
    const [, whole, num, den] = mixed.map(Number);
    return den ? whole + num / den : null;
  }

  const fraction = str.match(/^(\d+)\/(\d+)$/);
  if (fraction) {
    const [, num, den] = fraction.map(Number);
    return den ? num / den : null;
  }

  const decimal = parseFloat(str);
  return isNaN(decimal) ? null : decimal;
}

function formatIngredientAmount(ing) {
  const qty = ing.quantity != null ? formatAsFraction(ing.quantity) : "";
  const amount = [qty, ing.unit].filter(Boolean).join(" ");
  return amount ? `${amount} ${ing.name}` : ing.name;
}

// Builds one editable ingredient row: fraction-aware quantity text field,
// a unit dropdown, a name field, and a remove button. Always exactly 4
// fields -- if the given unit isn't one of our standard options (e.g. a
// vague scraped phrase like "good shakes"), we don't try to preserve it;
// we just drop the quantity/unit and keep the ingredient name, letting
// the user pick a real unit and type a quantity themselves if they want.
function makeIngredientEditRow(ing) {
  const row = document.createElement("div");
  row.className = "ingredient-edit-row";

  const knownValues = UNIT_OPTIONS.map((o) => o.value);
  const rawUnit = ing && ing.unit != null ? ing.unit : "";
  const isKnownUnit = knownValues.includes(rawUnit);

  const optionsHtml = UNIT_OPTIONS.map(
    (o) => `<option value="${o.value}">${o.label}</option>`
  ).join("");

  row.innerHTML = `
    <input type="text" class="ing-quantity" placeholder="1/2" />
    <select class="ing-unit-select">${optionsHtml}</select>
    <input type="text" class="ing-name" placeholder="Ingredient" autocapitalize="words" />
    <button type="button" class="remove-ingredient">&times;</button>
  `;

  if (isKnownUnit) {
    row.querySelector(".ing-quantity").value =
      ing && ing.quantity != null ? formatAsFraction(ing.quantity) : "";
    row.querySelector(".ing-unit-select").value = rawUnit;
  } else {
    row.querySelector(".ing-quantity").value = "";
    row.querySelector(".ing-unit-select").value = "";
  }
  row.querySelector(".ing-name").value = ing && ing.name != null ? ing.name : "";
  enableTitleCase(row.querySelector(".ing-name"));

  return row;
}

function titleCase(value) {
  return value.toLowerCase().replace(/(^|\s)(\S)/g, (match, space, letter) => space + letter.toUpperCase());
}

function enableTitleCase(input) {
  input.addEventListener("input", () => {
    const start = input.selectionStart;
    input.value = titleCase(input.value);
    input.setSelectionRange(start, start);
  });
}

// Reads one row back out as {name, quantity, unit}, or null if it's blank.
function readIngredientEditRow(row) {
  const name = row.querySelector(".ing-name").value.trim();
  if (!name) return null;

  const quantityRaw = row.querySelector(".ing-quantity").value;
  const quantity = parseFractionInput(quantityRaw);
  const unit = row.querySelector(".ing-unit-select").value || null;

  return { name, quantity, unit };
}