(function () {
  "use strict";

  const CONFIG_URL = "data/commerce.json";
  let config = null;

  const $ = selector => document.querySelector(selector);
  const status = () => $("#commerceStatus");
  const emailInput = () => $("#commerceEmail");
  const selectRoot = () => $("#pkgSelect");
  const hiddenInput = () => selectRoot()?.querySelector('input[name="package"]');
  const trigger = () => selectRoot()?.querySelector(".pkg-select-trigger");
  const checkoutButton = () => $("#commerceCheckoutButton");

  function setStatus(message, isError = false) {
    const node = status();
    if (!node) return;
    node.textContent = message;
    node.dataset.state = isError ? "error" : "ready";
  }

  function productFor(key) {
    return config?.products?.[key] || null;
  }

  function chooseProduct(key) {
    const product = productFor(key);
    if (!product) return;
    if (hiddenInput()) hiddenInput().value = key;
    if (trigger()) trigger().childNodes[0].textContent = product.name + " ";
    selectRoot()?.classList.remove("open");
    trigger()?.setAttribute("aria-expanded", "false");
    setStatus(product.billing === "one_time"
      ? `${product.name} · €${product.price_eur} · one-time${product.term_months ? ` · ${product.term_months} months` : ""}`
      : product.name);
  }

  async function loadConfig() {
    const response = await fetch(CONFIG_URL, { cache: "no-store" });
    if (!response.ok) throw new Error("Commerce configuration is unavailable.");
    config = await response.json();
    document.querySelectorAll("[data-commerce-select]").forEach(card => {
      card.addEventListener("click", () => {
        chooseProduct(card.dataset.commerceSelect);
        $("#contact")?.scrollIntoView({ behavior: "smooth", block: "center" });
      });
      card.addEventListener("keydown", event => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          card.click();
        }
      });
    });
    document.querySelectorAll("[data-product-key]").forEach(option => {
      option.addEventListener("click", () => chooseProduct(option.dataset.productKey));
    });
  }

  async function beginCheckout() {
    const key = hiddenInput()?.value || "";
    const product = productFor(key);
    const email = (emailInput()?.value || "").trim();

    if (!product) {
      setStatus("Choose Doberman Intelligence Record or Kennel Promotion Service first.", true);
      trigger()?.focus();
      return;
    }
    if (!email || !emailInput()?.checkValidity()) {
      setStatus("Enter a valid email address for the order and receipt.", true);
      emailInput()?.focus();
      return;
    }
    if (!config?.api_base) {
      setStatus("Secure checkout is being activated. Please try again shortly.", true);
      return;
    }

    const button = checkoutButton();
    if (button) {
      button.disabled = true;
      button.textContent = "Opening secure checkout…";
    }
    setStatus("Creating a single-use Dodo Payments checkout session…");

    try {
      const response = await fetch(`${config.api_base}/v1/commerce/checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          service_key: key,
          customer_email: email,
          source: "doberman-index.com"
        })
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok || !body.checkout_url) {
        throw new Error(body.error || "Checkout could not be created.");
      }
      window.location.assign(body.checkout_url);
    } catch (error) {
      setStatus(error.message || "Checkout could not be created. Please try again.", true);
      if (button) {
        button.disabled = false;
        button.textContent = "Continue to secure checkout";
      }
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    loadConfig().catch(error => setStatus(error.message, true));
    checkoutButton()?.addEventListener("click", beginCheckout);
  });
})();
