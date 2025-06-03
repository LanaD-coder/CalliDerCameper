// This is your test secret API key.
const stripe = Stripe("pk_test_51RR5xNRuPRcbt1gx7WkgF3wbjT12gH7SELnXNXExbQnEyLrvoh8EIcXupxqPtDxoA1JEVv1QPU8njnADydc5SKrW000eLZzJwS");

initialize();

// Create a Checkout Session
async function initialize() {
  const fetchClientSecret = async () => {
    const response = await fetch("/create-checkout-session", {
      method: "POST",
    });
    const { clientSecret } = await response.json();
    return clientSecret;
  };

  const checkout = await stripe.initEmbeddedCheckout({
    fetchClientSecret,
  });

  // Mount Checkout
  checkout.mount('#checkout');
}