const providerFilters = document.querySelectorAll("[data-filter]");
const releaseCards = document.querySelectorAll(".release-card");
const selectButtons = document.querySelectorAll(".select-release");
const providerInput = document.getElementById("provider-input");
const releaseIdInput = document.getElementById("release-id-input");
const manualNameInput = document.getElementById("manual-name-input");
const manualUrlInput = document.getElementById("manual-url-input");
const selectedBanner = document.getElementById("selected-release-banner");

providerFilters.forEach((button) => {
  button.addEventListener("click", () => {
    const filter = button.dataset.filter;
    providerFilters.forEach((item) => item.classList.remove("is-active"));
    button.classList.add("is-active");
    releaseCards.forEach((card) => {
      const shouldShow = filter === "all" || card.dataset.provider === filter;
      card.hidden = !shouldShow;
    });
  });
});

selectButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const { provider, releaseId, releaseName, productUrl } = button.dataset;
    if (!provider || !releaseId || !releaseName || !productUrl) {
      return;
    }
    providerInput.value = provider;
    releaseIdInput.value = releaseId;
    manualNameInput.value = releaseName;
    manualUrlInput.value = productUrl;
    selectedBanner.textContent = `Selected ${releaseName} from ${provider}. The purchase form is now pre-filled.`;
    selectedBanner.classList.add("selected");
  });
});
