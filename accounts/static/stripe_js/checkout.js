// This is your test secret API key.
const stripe = Stripe(
  "pk_live_51RnfHCDAhijUh3p6J8a3IyFFXCA1kKyTmDbiTyRHcQFyjyacaV7hSr4Pc3OTCVMQ16JyEAI0Es2YywsVj4MNxNDk00XvIfYEBh"
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
