// booking.js
window.stripe = window.stripe || null;
window.elements = window.elements || null;
window.card = window.card || null;

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
    return (data.booked_dates || []).map((d) => d.date);
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
  base = parseFloat(base) || 0;
  const additionalServiceCheckboxes = document.querySelectorAll(
    'input[name="additional_services"]'
  );

  let servicesTotal = 0;
  additionalServiceCheckboxes.forEach((cb) => {
    if (cb.checked) {
      servicesTotal += parseFloat(additionalServicePrices[cb.value]) || 0;
    }
  });

  const subtotal = base + servicesTotal;
  const vatAmount = Math.round(subtotal * 0.19 * 100) / 100 || 0;
  const deposit = 1000;
  const grandTotal = Math.round((subtotal + vatAmount + deposit) * 100) / 100;

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

async function refreshDatepickers(datePrices, additionalServicePrices) {
  const bookedDates = await fetchBookedDates();

  $("#id_start_date, #id_end_date").datepicker("destroy");

  $("#id_start_date, #id_end_date")
    .datepicker({
      format: "yyyy-mm-dd",
      datesDisabled: bookedDates,
      autoclose: true,
      todayHighlight: true,
    })
    .off("changeDate")
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

// ----------------------
// Initialize Booking Form
// ----------------------
async function initBookingForm({
  datePrices,
  additionalServicePrices,
  ajaxUrl,
}) {
  const startDateInput = document.getElementById("id_start_date");
  const endDateInput = document.getElementById("id_end_date");
  const form = document.getElementById("booking-form");
  const additionalServiceCheckboxes = document.querySelectorAll(
    'input[name="additional_services"]'
  );

  if (!form || !startDateInput || !endDateInput) return;

  async function setupDatepickers() {
    const bookedDates = await fetchBookedDates();
    $("#id_start_date, #id_end_date").datepicker("destroy");
    $("#id_start_date, #id_end_date")
      .datepicker({
        format: "yyyy-mm-dd",
        datesDisabled: bookedDates,
        autoclose: true,
        todayHighlight: true,
      })
      .off("changeDate")
      .on("changeDate", onDatesChanged(datePrices, additionalServicePrices));
  }

  await setupDatepickers();

  // Clear previous dates AFTER datepicker init
  startDateInput.value = "";
  endDateInput.value = "";
  calculateBaseRentalCost({}); // shows "--"
  calculateSummary(0, additionalServicePrices);

  toggleAdditionalDriverFields();
  document
    .getElementById("add_driver_yes")
    ?.addEventListener("change", toggleAdditionalDriverFields);
  document
    .getElementById("add_driver_no")
    ?.addEventListener("change", toggleAdditionalDriverFields);

  additionalServiceCheckboxes.forEach((cb) => {
    cb.addEventListener("change", () => {
      const base =
        parseFloat(document.getElementById("base-rental-cost").textContent) ||
        0;
      calculateSummary(base, additionalServicePrices);
    });
  });

  setupStripePayment();

  // Form submission
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!document.getElementById("accept-datenschutz")?.checked) {
      showFormErrors(["Bitte bestätigen Sie die Datenschutzerklärung."]);
      return;
    }

    const formData = new FormData(this);
    const data = {};
    formData.forEach((value, key) => {
      if (key === "additional_services") {
        if (!data[key]) data[key] = [];
        data[key].push(value);
      } else {
        data[key] = value;
      }
    });

    fetch(ajaxUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify(data),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.session_id) {
          stripe.redirectToCheckout({ sessionId: data.session_id });
        } else if (data.errors) {
          showFormErrors(data.errors);
        } else {
          showFormErrors(["Ein unbekannter Fehler ist aufgetreten."]);
        }
      })
      .catch((err) => {
        console.error("Submit error:", err);
        showFormErrors(["Beim Buchen ist ein Fehler aufgetreten."]);
      });
  });
}

window.initBookingForm = initBookingForm;
