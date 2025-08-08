// This is your test secret API key.
const stripe = Stripe(
  "pk_test_51RnfHKRZKvhbcGU6CgaLlT6dkRMiKGGmovIxHmhnlEEPSm0PhIq2OcefSdIaSFCa5GKW0AqSwunG1aUNuiejjAJ100J6AQBF0i"
);

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
  checkout.mount("#checkout");
}
