// booking.js

function toggleAdditionalDriverFields() {
  const yesRadio = document.getElementById('add_driver_yes');
  const noRadio = document.getElementById('add_driver_no');
  const additionalFields = document.getElementById('additional-driver-fields');

  if (yesRadio.checked) {
    additionalFields.style.display = 'block';
  } else {
    additionalFields.style.display = 'none';
    additionalFields.querySelectorAll('input').forEach(input => input.value = '');
  }
}

function calculateBaseRentalCost(datePrices) {
  const startDateInput = document.getElementById("id_start_date");
  const endDateInput = document.getElementById("id_end_date");
  const baseCostEl = document.getElementById('base-rental-cost');

  const startDateStr = startDateInput.value;
  const endDateStr = endDateInput.value;

  if (!startDateStr || !endDateStr) {
    baseCostEl.textContent = '--';
    return 0;
  }

  const startDate = new Date(startDateStr);
  const endDate = new Date(endDateStr);

  if (endDate < startDate) {
    baseCostEl.textContent = 'Invalid dates';
    return 0;
  }

  let totalCost = 0;
  for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
    const key = d.toISOString().split('T')[0];
    totalCost += datePrices[key] || 0;
  }

  baseCostEl.textContent = totalCost.toFixed(2);
  return totalCost;
}

function calculateSummary(base, insuranceCost, additionalServicePrices) {
  const insuranceCheckbox = document.getElementById("id_additional_insurance");
  const additionalServiceCheckboxes = document.querySelectorAll('input[name="additional_services"]');

  let insurance = insuranceCheckbox.checked ? insuranceCost : 0;
  let servicesTotal = 0;

  additionalServiceCheckboxes.forEach(cb => {
    if (cb.checked) {
      servicesTotal += additionalServicePrices[cb.value] || 0;
    }
  });

  const grandTotal = base + servicesTotal + insurance;

  document.getElementById('summary-base-price').textContent = base.toFixed(2);
  document.getElementById('summary-insurance-price').textContent = insurance.toFixed(2);
  document.getElementById('summary-services-price').textContent = servicesTotal.toFixed(2);
  document.getElementById('summary-grand-total').textContent = grandTotal.toFixed(2);
}

function getCookie(name) {
  const cookie = document.cookie
    .split(';')
    .map(c => c.trim())
    .find(c => c.startsWith(name + '='));
  return cookie ? decodeURIComponent(cookie.split('=')[1]) : null;
}

function showFormErrors(errors) {
  const errorBox = document.getElementById('form-errors');
  errorBox.innerHTML = '';
  if (Array.isArray(errors)) {
    errors.forEach(err => {
      const p = document.createElement('p');
      p.textContent = err;
      errorBox.appendChild(p);
    });
  } else {
    const p = document.createElement('p');
    p.textContent = typeof errors === 'string' ? errors : JSON.stringify(errors);
    errorBox.appendChild(p);
  }
  errorBox.style.display = 'block';
}

export function initBookingForm({ datePrices, additionalServicePrices, insuranceCost = 20, ajaxUrl }) {
  const startDateInput = document.getElementById("id_start_date");
  const endDateInput = document.getElementById("id_end_date");
  const insuranceCheckbox = document.getElementById("id_additional_insurance");
  const additionalServiceCheckboxes = document.querySelectorAll('input[name="additional_services"]');

  document.addEventListener('DOMContentLoaded', () => {
    toggleAdditionalDriverFields();
    let base = calculateBaseRentalCost(datePrices);
    calculateSummary(base, insuranceCost, additionalServicePrices);
  });

  document.getElementById('add_driver_yes').addEventListener('change', toggleAdditionalDriverFields);
  document.getElementById('add_driver_no').addEventListener('change', toggleAdditionalDriverFields);

  startDateInput.addEventListener('change', () => {
    let base = calculateBaseRentalCost(datePrices);
    calculateSummary(base, insuranceCost, additionalServicePrices);
  });
  endDateInput.addEventListener('change', () => {
    let base = calculateBaseRentalCost(datePrices);
    calculateSummary(base, insuranceCost, additionalServicePrices);
  });

  insuranceCheckbox.addEventListener('change', () => {
    let base = parseFloat(document.getElementById('base-rental-cost').textContent) || 0;
    calculateSummary(base, insuranceCost, additionalServicePrices);
  });

  additionalServiceCheckboxes.forEach(cb => {
    cb.addEventListener('change', () => {
      let base = parseFloat(document.getElementById('base-rental-cost').textContent) || 0;
      calculateSummary(base, insuranceCost, additionalServicePrices);
    });
  });

  document.getElementById('booking-form').addEventListener('submit', function (e) {
    e.preventDefault();

    if (!document.getElementById('accept-datenschutz').checked) {
      showFormErrors(["Bitte bestätigen Sie die Datenschutzerklärung."]);
      return;
    }

    const formData = new FormData(this);
    const data = {};
    formData.forEach((value, key) => { data[key] = value; });

    console.log("Fetching URL:", ajaxUrl);
    fetch(ajaxUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify(data),
    })
    .then(res => res.json())
    .then(data => {
      if (data.session_id) {
        const stripe = Stripe("pk_test_51RR5xNRuPRcbt1gx7WkgF3wbjT12gH7SELnXNXExbQnEyLrvoh8EIcXupxqPtDxoA1JEVv1QPU8njnADydc5SKrW000eLZzJwS");
        stripe.redirectToCheckout({ sessionId: data.session_id });
      } else if (data.errors) {
        showFormErrors(data.errors);
      } else {
        showFormErrors(["Ein unbekannter Fehler ist aufgetreten."]);
      }
    })
    .catch(err => {
      console.error("Submit error:", err);
      showFormErrors(["Beim Buchen ist ein Fehler aufgetreten."]);
    });
  });
}