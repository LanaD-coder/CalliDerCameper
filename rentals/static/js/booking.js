console.log("✅ booking.js loaded and running", window.location.href);

// booking.js
window.stripe = window.stripe || null;
window.elements = window.elements || null;
window.card = window.card || null;

console.log("✅ booking.js is loaded");

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

function parseDateYMD(str) {
  if (!str) return null;
  const parts = str.trim().split("-").map(Number);
  if (parts.length !== 3) return null;
  const [year, month, day] = parts;
  if (isNaN(year) || isNaN(month) || isNaN(day)) return null;
  return new Date(year, month - 1, day);
}

function formatDateYMD(date) {
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const dd = String(date.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
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

function calculateBaseRentalCost(datePrices, bookedDates = []) {
  const startInput = document.getElementById("id_start_date");
  const endInput = document.getElementById("id_end_date");
  const baseEl = document.getElementById("base-rental-cost");
  if (!startInput || !endInput || !baseEl) return 0;

  const startStr = startInput.value.trim();
  const endStr = endInput.value.trim();
  if (!startStr || !endStr) {
    baseEl.textContent = "--";
    return 0;
  }

  const startDate = parseDateYMD(startStr);
  const endDate = parseDateYMD(endStr);
  if (!startDate || !endDate || endDate < startDate) {
    baseEl.textContent = "Invalid dates";
    return 0;
  }

  let total = 0;
  let current = new Date(startDate);
  while (current <= endDate) {
    const key = formatDateYMD(current);

    // Only invalid if the date is booked
    if (bookedDates.includes(key)) {
      baseEl.textContent = "Invalid dates";
      return 0;
    }

    // If the date exists in datePrices, add it; otherwise 0
    total += datePrices[key] || 0;
    current.setDate(current.getDate() + 1);
  }

  baseEl.textContent = total.toFixed(2);
  return total;
}

function calculateSummary(base, additionalServicePrices) {
  console.log("calculateSummary called");
  console.log("Base:", base);
  console.log("Additional services:", additionalServicePrices);
  base = parseFloat(base) || 0;
  const additionalServiceCheckboxes = document.querySelectorAll(
    'input[name="additional_services"]'
  );

  let servicesTotal = 0;
  additionalServiceCheckboxes.forEach((cb) => {
    if (cb.checked) {
      servicesTotal += parseFloat(additionalServicePrices[cb.value]) || 0;
      console.log(
        `Service ${cb.value} checked, value:`,
        additionalServicePrices[cb.value]
      );
    }
  });

  const subtotal = base + servicesTotal;
  const vatAmount = Math.round(subtotal * 0.19 * 100) / 100 || 0;
  const deposit = 1000;
  const grandTotal = Math.round((subtotal + vatAmount + deposit) * 100) / 100;

  console.log("Subtotal:", subtotal);
  console.log("VAT amount:", vatAmount);
  console.log("Deposit:", deposit);
  console.log("Grand total:", grandTotal);

  const summaryElements = [
    "summary-base-price",
    "summary-services-price",
    "summary-vat",
    "summary-deposit-price",
    "summary-grand-total",
  ];

  if (!summaryElements.every((id) => document.getElementById(id))) return;

  document.getElementById("summary-base-price").textContent = base.toFixed(2);
  document.getElementById("summary-services-price").textContent =
    servicesTotal.toFixed(2);
  document.getElementById("summary-vat").textContent = vatAmount.toFixed(2);
  document.getElementById("summary-deposit-price").textContent =
    deposit.toFixed(2);
  document.getElementById("summary-grand-total").textContent =
    grandTotal.toFixed(2);
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

function onDatesChanged(datePrices, additionalServicePrices) {
  return async function () {
    const startInput = document.getElementById("id_start_date");
    const endInput = document.getElementById("id_end_date");
    if (!startInput || !endInput) return;

    const startStr = startInput.value.trim();
    const endStr = endInput.value.trim();

    if (!startStr || !endStr) {
      document.getElementById("base-rental-cost").textContent = "--";
      calculateSummary(0, additionalServicePrices);
      return;
    }

    // Check availability
    const availability = await checkAvailability(startStr, endStr);
    if (!availability.available) {
      showFormErrors(
        availability.errors || ["Selected dates are not available."]
      );
      document.getElementById("base-rental-cost").textContent = "Invalid dates";
      calculateSummary(0, additionalServicePrices);
      return;
    }

    const bookedDates = await fetchBookedDates();
    const base = calculateBaseRentalCost(datePrices, bookedDates);
    calculateSummary(base, additionalServicePrices);

    // Clear errors
    const errorBox = document.getElementById("form-errors");
    if (errorBox) {
      errorBox.style.display = "none";
      errorBox.innerHTML = "";
    }
  };
}

async function setupDatepickers(
  datePrices,
  additionalServicePrices,
  blockedDates = []
) {
  // Fetch booked dates from API
  const bookedDates = (await fetchBookedDates()) || [];
  console.log("Booked dates:", bookedDates);

  // Merge booked dates and blocked dates
  const allDisabledDates = [...bookedDates, ...blockedDates];

  // Keep only valid "yyyy-mm-dd" strings
  const allDisabledDatesFiltered = allDisabledDates.filter(
    (d) => typeof d === "string" && /^\d{4}-\d{2}-\d{2}$/.test(d)
  );

  // Destroy previous datepickers if any
  $("#id_start_date, #id_end_date").datepicker("destroy");

  // Initialize new datepickers with all disabled dates
  $("#id_start_date, #id_end_date")
    .datepicker({
      format: "yyyy-mm-dd",
      autoclose: true,
      todayHighlight: true,
      language: "de",
      datesDisabled: allDisabledDatesFiltered,
    })
    .on("changeDate", function () {
      onDatesChanged(datePrices, additionalServicePrices)();
    });
}

function setupStripePayment() {
  if (!document.getElementById("card-element")) return;

  window.stripe =
    window.stripe ||
    Stripe(
      "pk_test_51RnfHKRZKvhbcGU6CgaLlT6dkRMiKGGmovIxHmhnlEEPSm0PhIq2OcefSdIaSFCa5GKW0AqSwunG1aUNuiejjAJ100J6AQBF0i"
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

  // Ensure required fields exist
  data.start_date = data.start_date || "";
  data.end_date = data.end_date || "";

  return data;
}

// ----------------------
// Initialize Booking Form
// ----------------------
async function initBookingForm({
  datePrices,
  additionalServicePrices,
  blockedDates = [],
  ajaxUrl,
}) {
  window.blockedDates = blockedDates;

  try {
    console.log("Starting initBookingForm");

    const startDateInput = document.getElementById("id_start_date");
    const endDateInput = document.getElementById("id_end_date");
    const form = document.getElementById("booking-form");
    const additionalServiceCheckboxes = document.querySelectorAll(
      'input[name="additional_services"]'
    );

    if (!form || !startDateInput || !endDateInput) return;

    // Initialize datepickers
    await setupDatepickers(datePrices, additionalServicePrices, blockedDates);

    // Clear previous dates AFTER datepicker init
    startDateInput.value = "";
    endDateInput.value = "";
    calculateBaseRentalCost(datePrices);
    calculateSummary(0, additionalServicePrices);

    // Additional driver toggle
    toggleAdditionalDriverFields();
    document
      .getElementById("add_driver_yes")
      ?.addEventListener("change", toggleAdditionalDriverFields);
    document
      .getElementById("add_driver_no")
      ?.addEventListener("change", toggleAdditionalDriverFields);

    // Update summary when additional services change
    additionalServiceCheckboxes.forEach((cb) => {
      cb.addEventListener("change", () => {
        const base =
          parseFloat(
            document.getElementById("base-rental-cost")?.textContent
          ) || 0;
        calculateSummary(base, additionalServicePrices);
      });
    });

    // Initialize Stripe payment
    setupStripePayment();

    form.addEventListener("submit", function (e) {
      e.preventDefault();

      if (!document.getElementById("accept-datenschutz")?.checked) {
        showFormErrors(["Bitte bestätigen Sie die Datenschutzerklärung."]);
        return;
      }

      // Serialize form safely
      const data = serializeForm(this);
      console.log("📝 Serialized form data:", data);

      // Add safe numeric summary
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
      console.log("📦 JSON payload to send:", JSON.stringify(data));

      try {
        const jsonPayload = JSON.stringify(data);
        console.log("📦 JSON payload:", jsonPayload);

        fetch(ajaxUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          body: JSON.stringify(data),
        })
          .then(async (res) => {
            console.log("📤 Response status:", res.status);
            const json = await res.json().catch(() => null);
            console.log("📩 Response JSON:", json);
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
      } catch (err) {
        console.error("Error submitting form:", err);
        showFormErrors(["Beim Buchen ist ein Fehler aufgetreten."]);
      }
    }); // ✅ closes form.addEventListener
  } catch (err) {
    console.error("Error in initBookingForm:", err);
  }
} // ✅ closes initBookingForm

// Expose globally
window.initBookingForm = initBookingForm;
