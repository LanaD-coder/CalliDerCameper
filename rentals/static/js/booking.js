// booking.js

function toggleAdditionalDriverFields() {
  const yesRadio = document.getElementById("add_driver_yes");
  const noRadio = document.getElementById("add_driver_no");
  const additionalFields = document.getElementById("additional-driver-fields");

  if (yesRadio.checked) {
    additionalFields.style.display = "block";
  } else {
    additionalFields.style.display = "none";
    additionalFields
      .querySelectorAll("input")
      .forEach((input) => (input.value = ""));
  }
}

function calculateBaseRentalCost(datePrices) {
  console.log("Calculating base rental cost, datePrices:", datePrices);
  const startDateInput = document.getElementById("id_start_date");
  const endDateInput = document.getElementById("id_end_date");
  const baseCostEl = document.getElementById("base-rental-cost");

  const startDateStr = startDateInput.value;
  const endDateStr = endDateInput.value;

  if (!startDateStr || !endDateStr) {
    baseCostEl.textContent = "--";
    return 0;
  }

  const startDate = new Date(startDateStr);
  const endDate = new Date(endDateStr);

  if (endDate < startDate) {
    baseCostEl.textContent = "Invalid dates";
    return 0;
  }

  let totalCost = 0;
  for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
    const key = d.toISOString().split("T")[0];
    totalCost += datePrices[key] || 0;
  }

  baseCostEl.textContent = totalCost.toFixed(2);
  return totalCost;
}

function calculateSummary(base, additionalServicePrices) {
  const additionalServiceCheckboxes = document.querySelectorAll(
    'input[name="additional_services"]'
  );

  let servicesTotal = 0;

  additionalServiceCheckboxes.forEach((cb) => {
    if (cb.checked) {
      servicesTotal += additionalServicePrices[cb.value] || 0;
    }
  });

  const grandTotal = base + servicesTotal + 1000;

  document.getElementById("summary-base-price").textContent = base.toFixed(2);
  document.getElementById("summary-deposit-price").textContent = (1000).toFixed(
    2
  );
  document.getElementById("summary-services-price").textContent =
    servicesTotal.toFixed(2);
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

// Datepicker Functionality
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
    const data = await response.json();
    return data; // expect { available: true/false, errors: [...] }
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
    const startDateInput = document.getElementById("id_start_date");
    const endDateInput = document.getElementById("id_end_date");
    const startDate = startDateInput.value;
    const endDate = endDateInput.value;

    if (!startDate || !endDate) return;

    const availability = await checkAvailability(startDate, endDate);

    if (!availability.available) {
      showFormErrors(
        availability.errors || ["Selected dates are not available."]
      );
    } else {
      const errorBox = document.getElementById("form-errors");
      errorBox.style.display = "none";
      errorBox.innerHTML = "";
      let base = calculateBaseRentalCost(datePrices);
      calculateSummary(base, additionalServicePrices);
    }
  };
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

async function refreshDatepickers() {
  const bookedDates = await fetchBookedDates();

  // Destroy previous datepickers
  $("#id_start_date, #id_end_date").datepicker("destroy");

  // Initialize datepickers with disabled dates and bind changeDate event here
  $("#id_start_date, #id_end_date")
    .datepicker({
      format: "yyyy-mm-dd",
      datesDisabled: bookedDates,
      autoclose: true,
      todayHighlight: true,
    })
    .off("changeDate")
    .on("changeDate", onDatesChanged);
}

$(document).ready(function () {});

let stripe, elements, card;

function setupStripePayment() {
  stripe = Stripe(
    "pk_test_51RnfHKRZKvhbcGU6CgaLlT6dkRMiKGGmovIxHmhnlEEPSm0PhIq2OcefSdIaSFCa5GKW0AqSwunG1aUNuiejjAJ100J6AQBF0i"
  );
  elements = stripe.elements();
  card = elements.create("card");
  card.mount("#card-element");

  card.on("change", (event) => {
    const displayError = document.getElementById("card-errors");
    displayError.textContent = event.error ? event.error.message : "";
  });
}

function showFormErrors(errors) {
  const errorBox = document.getElementById("form-errors");
  errorBox.innerHTML = "";
  errorBox.style.display = "block";

  if (Array.isArray(errors)) {
    // Array of error strings, display each
    errors.forEach((err) => {
      const p = document.createElement("p");
      p.textContent = err;
      errorBox.appendChild(p);
    });
  } else if (typeof errors === "object" && errors !== null) {
    // Object: field name keys, array of error strings as values
    for (const [field, messages] of Object.entries(errors)) {
      // Convert snake_case field name to human readable label
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
    // Fallback for any other type
    const p = document.createElement("p");
    p.textContent =
      typeof errors === "string" ? errors : JSON.stringify(errors);
    errorBox.appendChild(p);
  }
}

export function initBookingForm({
  datePrices,
  additionalServicePrices,
  ajaxUrl,
}) {
  const startDateInput = document.getElementById("id_start_date");
  const endDateInput = document.getElementById("id_end_date");
  const additionalServiceCheckboxes = document.querySelectorAll(
    'input[name="additional_services"]'
  );
  const form = document.getElementById("booking-form");

  // Setup datepicker, fetch booked dates and bind events
  async function setupDatepickers() {
    const bookedDates = await fetchBookedDates();

    // Destroy previous datepickers (if any)
    $("#id_start_date, #id_end_date").datepicker("destroy");

    // Initialize datepickers with booked dates disabled
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

  setupDatepickers();

  // Toggle additional driver fields on page load and on radio change
  toggleAdditionalDriverFields();
  document
    .getElementById("add_driver_yes")
    .addEventListener("change", toggleAdditionalDriverFields);
  document
    .getElementById("add_driver_no")
    .addEventListener("change", toggleAdditionalDriverFields);

  additionalServiceCheckboxes.forEach((cb) => {
    cb.addEventListener("change", () => {
      const base =
        parseFloat(document.getElementById("base-rental-cost").textContent) ||
        0;
      calculateSummary(base, additionalServicePrices);
    });
  });

  // Initialize Stripe payment elements
  setupStripePayment();

  // Calculate and show initial costs
  const initialBase = calculateBaseRentalCost(datePrices);
  calculateSummary(initialBase, additionalServicePrices);

  // Form submission handler
  form.addEventListener("submit", function (e) {
    e.preventDefault();

    if (!document.getElementById("accept-datenschutz").checked) {
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

    console.log("Submitting booking data:", data);

    fetch(ajaxUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify(data),
    })
      .then((res) => {
        console.log("Fetch response status:", res.status);
        return res.json();
      })
      .then((data) => {
        console.log("Response JSON:", data);

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
