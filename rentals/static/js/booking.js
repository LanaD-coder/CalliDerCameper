console.log("✅ booking.js loaded and running", window.location.href);

// booking.js global objects
window.stripe = window.stripe || null;
window.elements = window.elements || null;
window.card = window.card || null;
window.dailyRates = window.dailyRates || {};
window.additionalServicePrices = window.additionalServicePrices || {};

// ----------------------
// Seasonal Rates
// ----------------------
const seasonalRates = [
  { start: "2025-04-01", end: "2025-05-31", price: 95 },
  { start: "2025-06-01", end: "2025-08-31", price: 110 },
  { start: "2025-09-01", end: "2025-09-30", price: 95 },
  { start: "2025-10-01", end: "2026-03-31", price: 75 },
];

window.additionalServicePrices = {
  1: 59, // Endreinigung
};
console.log("AdditionalServicePrices:", window.additionalServicePrices);
// ----------------------
// Helpers
// ----------------------
function parseDateYMD(str) {
  if (!str) return null;
  const [year, month, day] = str.split("-").map(Number);
  return new Date(year, month - 1, day);
}

function formatDateYMD(date) {
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const dd = String(date.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

function getPriceForDate(dateStr) {
  return window.dailyRates[dateStr] || 0;
}

function safeParseNumber(value) {
  const num = parseFloat(value);
  return isNaN(num) ? 0 : num;
}

// ----------------------
// Function Definitions
// ----------------------
function toggleAdditionalDriverFields() {
  const container = document.getElementById("additional-driver-fields");
  const yes = document.getElementById("add_driver_yes")?.checked;
  if (container) container.style.display = yes ? "block" : "none";
}
window.toggleAdditionalDriverFields = toggleAdditionalDriverFields;

console.log("Daily rates loaded:", window.dailyRates);

function calculateBaseRentalCost() {
  const startInput = document.getElementById("id_start_date");
  const endInput = document.getElementById("id_end_date");
  const baseEl = document.getElementById("base-rental-cost");
  if (!startInput || !endInput || !baseEl) return null;

  const startStr = startInput.value.trim();
  const endStr = endInput.value.trim();
  if (!startStr || !endStr) {
    baseEl.textContent = "--";
    return null;
  }

  const startDate = parseDateYMD(startStr);
  const endDate = parseDateYMD(endStr);
  console.log("Start:", startStr, "End:", endStr);
  console.log("Parsed Start:", startDate, "Parsed End:", endDate);
  if (!startDate || !endDate || endDate < startDate) {
    baseEl.textContent = "Invalid dates";
    return null;
  }

  let total = 0;
  const oneDay = 24 * 60 * 60 * 1000;
  for (let t = startDate.getTime(); t <= endDate.getTime(); t += oneDay) {
    const d = new Date(t);
    const dateKey = formatDateYMD(d);
    const price = getPriceForDate(dateKey);
    console.log("Date:", dateKey, "Price:", price);
    total += price;
  }

  baseEl.textContent = total.toFixed(2);
  return total;
}

async function fetchBookedDates() {
  try {
    const response = await fetch("/rentals/api/booked-dates/", {
      method: "GET",
      headers: { "X-CSRFToken": getCookie("csrftoken") },
    });
    const data = await response.json();
    return data.booked_dates || [];
  } catch (error) {
    console.error("Error fetching booked dates:", error);
    return [];
  }
}

function calculateSummary(base, additionalServicePrices) {
  console.log("Base:", base);
  base = parseFloat(base) || 0;

  const additionalServiceCheckboxes = document.querySelectorAll(
    'input[name="additional_services"]:checked'
  );
  let servicesTotal = 0;

  additionalServiceCheckboxes.forEach((cb) => {
    const key = cb.value.toString().trim(); // ensures string + removes whitespace
    const price = parseFloat(window.additionalServicePrices[key]) || 0;
    servicesTotal += price;
    console.log(`Service ${key} checked, value:`, price);
  });

  const subtotal = base + servicesTotal;
  const vatAmount = Math.round(subtotal * 0.19 * 100) / 100 || 0; // 19% VAT
  const deposit = 1000; // fixed deposit
  const grandTotal = Math.round((subtotal + vatAmount + deposit) * 100) / 100;

  console.log("Subtotal:", subtotal);
  console.log("VAT amount:", vatAmount);
  console.log("Deposit:", deposit);
  console.log("Grand total:", grandTotal);

  const domMap = {
    "summary-base-price": base,
    "summary-services-price": servicesTotal,
    "summary-vat": vatAmount,
    "summary-deposit-price": deposit,
    "summary-grand-total": grandTotal,
  };

  Object.entries(domMap).forEach(([id, value]) => {
    const el = document.getElementById(id);
    if (el) el.textContent = value.toFixed(2);
  });
}

function getCookie(name) {
  const cookie = document.cookie
    .split(";")
    .map((c) => c.trim())
    .find((c) => c.startsWith(name + "="));
  return cookie ? decodeURIComponent(cookie.split("=")[1]) : null;
}

async function checkAvailability(startDate, endDate) {
  try {
    const response = await fetch("/rentals/api/check-availability/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify({ start_date: startDate, end_date: endDate }),
    });
    return await response.json();
  } catch (err) {
    console.error("Error checking availability:", err);
    return {
      available: false,
      errors: ["Server error while checking availability"],
    };
  }
}

function onDatesChanged(additionalServicePrices, bookedDates) {
  return function () {
    console.log("✅ Dates changed listener fired");
    const startInput = document.getElementById("id_start_date");
    const endInput = document.getElementById("id_end_date");
    if (!startInput || !endInput) return;

    const startStr = startInput.value.trim();
    const endStr = endInput.value.trim();
    console.log("Dates changed:", startStr, endStr);

    if (!startStr || !endStr) {
      document.getElementById("base-rental-cost").textContent = "--";
      const summaryFields = [
        "summary-base-price",
        "summary-services-price",
        "summary-vat",
        "summary-deposit-price",
        "summary-grand-total",
      ];
      summaryFields.forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.textContent = "--";
      });
      return;
    }

    const startDate = parseDateYMD(startStr);
    const endDate = parseDateYMD(endStr);
    if (!startDate || !endDate || endDate < startDate) {
      console.log("Invalid dates, skipping calculation");
      return;
    }

    const base = calculateBaseRentalCost();
    calculateSummary(base, additionalServicePrices);

    const errorBox = document.getElementById("form-errors");
    if (errorBox) {
      errorBox.style.display = "none";
      errorBox.innerHTML = "";
    }
  };
}

async function setupDatepickers(
  blockedDates = [],
  bookedDates = [],
  handleDatesChange
) {
  console.log("Booked Dates:", bookedDates);

  // Destroy previous datepickers
  $("#id_start_date, #id_end_date").datepicker("destroy");

  // Merge and normalize blocked dates
  window.allDisabledDates = [...blockedDates, ...bookedDates]
    .map((d) => {
      if (typeof d !== "string") return null;
      const parts = d.split("-");
      if (parts.length !== 3) return null;
      const y = parts[0].padStart(4, "0");
      const m = parts[1].padStart(2, "0");
      const day = parts[2].padStart(2, "0");
      return `${y}-${m}-${day}`;
    })
    .filter(Boolean);

  // Setup datepickers
  ["#id_start_date", "#id_end_date"].forEach((selector) => {
    $(selector)
      .datepicker({
        format: "yyyy-mm-dd",
        startDate: new Date(),
        autoclose: true,
        todayHighlight: true,
        language: "de",
        beforeShowDay: function (date) {
          const formatted = formatDateYMD(date);
          if (window.allDisabledDates.includes(formatted)) {
            return {
              enabled: false,
              classes: "disabled-date",
              tooltip: "Dieser Tag ist nicht verfügbar",
            };
          }
          return true;
        },
        forceParse: false,
      })
      .on("changeDate", function (e) {
        const formatted = e.format("yyyy-mm-dd");
        $(this).val(formatted);
        handleDatesChange(); // ✅ calculation happens here
      });
  });

  // Prevent typing blocked dates
  $("#id_start_date, #id_end_date").on("change", function () {
    const val = $(this).val();
    if (window.allDisabledDates.includes(val)) {
      alert("Dieser Tag ist nicht verfügbar!");
      $(this).val("");
    }
  });
}

function setupStripePayment() {
  if (!document.getElementById("card-element")) return;

  window.stripe =
    window.stripe ||
    Stripe(
      "pk_live_51RnfHCDAhijUh3p6J8a3IyFFXCA1kKyTmDbiTyRHcQFyjyacaV7hSr4Pc3OTCVMQ16JyEAI0Es2YywsVj4MNxNDk00XvIfYEBh"
    );
  window.elements = window.elements || window.stripe.elements();
  window.card = window.card || window.elements.create("card");
  window.card.mount("#card-element");

  window.card.on("change", (event) => {
    const displayError = document.getElementById("card-errors");
    if (displayError)
      displayError.textContent = event.error ? event.error.message : "";
  });
}

function showFormErrors(errors) {
  const errorBox = document.getElementById("form-errors");
  if (!errorBox) return;

  errorBox.innerHTML = "";
  errorBox.style.display = "block";

  if (Array.isArray(errors)) {
    errors.forEach((err) => {
      const p = document.createElement("p");
      p.textContent = err;
      errorBox.appendChild(p);
    });
  } else if (typeof errors === "object" && errors !== null) {
    for (const [field, messages] of Object.entries(errors)) {
      const label = field
        .replace(/_/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase());
      messages.forEach((msg) => {
        const p = document.createElement("p");
        p.textContent = `${label}: ${msg}`;
        errorBox.appendChild(p);
      });
    }
  } else {
    const p = document.createElement("p");
    p.textContent =
      typeof errors === "string" ? errors : JSON.stringify(errors);
    errorBox.appendChild(p);
  }
}

function serializeForm(form) {
  const formData = new FormData(form);
  const data = {};

  for (let [key, value] of formData.entries()) {
    if (value === undefined || value === null || value === "") continue;

    if (key === "additional_services") {
      if (!data[key]) data[key] = [];
      data[key].push(value);
    } else {
      data[key] = value;
    }
  }

  data.start_date = data.start_date || "";
  data.end_date = data.end_date || "";

  return data;
}

async function initBookingForm({
  additionalServicePrices = {},
  blockedDates = [],
  ajaxUrl,
}) {
  window.blockedDates = blockedDates;

  try {
    console.log("Starting initBookingForm");

    const startDateInput = document.getElementById("id_start_date");
    const endDateInput = document.getElementById("id_end_date");
    const form = document.getElementById("booking-form");

    const bookedDates = await fetchBookedDates();

    // Define the handler BEFORE passing it
    const handleDatesChange = onDatesChanged(
      additionalServicePrices,
      bookedDates
    );

    // Pass the handler into setupDatepickers
    await setupDatepickers(blockedDates, bookedDates, handleDatesChange);

    if (!form || !startDateInput || !endDateInput) return;

    console.log("Triggering initial calculation");
    handleDatesChange(); // optional initial calculation

    toggleAdditionalDriverFields();
    document
      .getElementById("add_driver_yes")
      ?.addEventListener("change", toggleAdditionalDriverFields);
    document
      .getElementById("add_driver_no")
      ?.addEventListener("change", toggleAdditionalDriverFields);

    document
      .querySelectorAll('input[name="additional_services"]')
      .forEach((cb) => {
        cb.addEventListener("change", () => {
          handleDatesChange();
        });
      });

    setupStripePayment();

    form.addEventListener("submit", function (e) {
      e.preventDefault();

      if (!document.getElementById("accept-datenschutz")?.checked) {
        showFormErrors(["Bitte bestätigen Sie die Datenschutzerklärung."]);
        return;
      }

      const data = serializeForm(this);
      data.summary = {
        base: safeParseNumber(
          document.getElementById("summary-base-price")?.textContent
        ),
        servicesTotal: safeParseNumber(
          document.getElementById("summary-services-price")?.textContent
        ),
        vatAmount: safeParseNumber(
          document.getElementById("summary-vat")?.textContent
        ),
        deposit: safeParseNumber(
          document.getElementById("summary-deposit-price")?.textContent
        ),
        grandTotal: safeParseNumber(
          document.getElementById("summary-grand-total")?.textContent
        ),
      };

      fetch(ajaxUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        credentials: "include",
        body: JSON.stringify(data),
      })
        .then(async (res) => {
          const json = await res.json().catch(() => null);
          return json;
        })
        .then((resp) => {
          if (!resp) return showFormErrors(["Server returned invalid JSON"]);
          if (resp.session_id)
            stripe.redirectToCheckout({ sessionId: resp.session_id });
          else if (resp.errors) showFormErrors(resp.errors);
          else showFormErrors(["Ein unbekannter Fehler ist aufgetreten."]);
        })
        .catch((err) => {
          console.error("Submit error:", err);
          showFormErrors(["Beim Buchen ist ein Fehler aufgetreten."]);
        });
    });
  } catch (err) {
    console.error("Error in initBookingForm:", err);
  }
}

window.initBookingForm = initBookingForm;
