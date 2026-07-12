(function () {
  const colorFilter = document.getElementById("colorFilter");
  const tierTabs = document.getElementById("tierTabs");
  const cards = document.querySelectorAll(".bike-card");
  const rows = document.querySelectorAll("#compareTable tbody tr");

  function applyFilters() {
    const tier = document.querySelector(".tier-tab.active")?.dataset.tier || "all";
    const colorsOnly = colorFilter?.checked;

    cards.forEach((card) => {
      const cardTier = card.dataset.tier;
      const colors = (card.dataset.colors || "").split(",");
      const tierMatch = tier === "all" || cardTier === tier;
      const colorMatch = !colorsOnly || colors.some((c) => c === "white" || c === "light_wood");
      card.classList.toggle("hidden", !(tierMatch && colorMatch));
    });

    rows.forEach((row) => {
      const rowTier = row.dataset.tier;
      const tierMatch = tier === "all" || rowTier === tier;
      row.style.display = tierMatch ? "" : "none";
    });
  }

  tierTabs?.addEventListener("click", (e) => {
    const tab = e.target.closest(".tier-tab");
    if (!tab) return;
    document.querySelectorAll(".tier-tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    applyFilters();
  });

  colorFilter?.addEventListener("change", applyFilters);
  applyFilters();
})();