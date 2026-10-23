const grid = document.getElementById("grid");
const hint = document.getElementById("filters-hint");

function inr(n) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n);
}

function card(item) {
  const el = document.createElement("article");
  el.className = "card";
  const attrs = item.attributes || {};
  el.innerHTML = `
    <img src="${item.image_url}" alt="${item.title}" />
    <h3>${item.title}</h3>
    <p class="meta">${item.sku} · ${attrs.metal || ""} ${attrs.purity || ""} · stock ${item.stock_qty}</p>
    <p class="price">${inr(item.price_inr)}</p>
  `;
  return el;
}

async function loadCatalog() {
  const res = await fetch("/catalog?limit=24");
  const data = await res.json();
  grid.replaceChildren(...data.items.map(card));
}

document.getElementById("search-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  if (!fd.get("image") || !fd.get("image").size) fd.delete("image");
  const res = await fetch("/search", { method: "POST", body: fd });
  const data = await res.json();
  const f = data.filters || {};
  const used = Object.entries(f)
    .filter(([, v]) => v)
    .map(([k, v]) => `${k}=${v}`)
    .join(" · ");
  hint.textContent = used ? `Filters: ${used}` : "No structured filters parsed — ranking by text/visual only.";
  grid.replaceChildren(...(data.results || []).map(card));
});

document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById("shop").classList.toggle("hidden", btn.dataset.view !== "shop");
    document.getElementById("ops").classList.toggle("hidden", btn.dataset.view !== "ops");
  });
});

document.getElementById("quote-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const body = {
    weight_grams: Number(fd.get("weight_grams")),
    metal: fd.get("metal"),
    purity: fd.get("purity"),
    making_charge_pct: Number(fd.get("making_charge_pct")),
  };
  const res = await fetch("/quote", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  document.getElementById("quote-out").textContent = JSON.stringify(await res.json(), null, 2);
});

async function loadOps() {
  const [health, dups, gaps, metrics] = await Promise.all([
    fetch("/health").then((r) => r.json()),
    fetch("/inventory/duplicates").then((r) => r.json()),
    fetch("/inventory/gaps").then((r) => r.json()),
    fetch("/metrics").then((r) => r.json()),
  ]);
  document.getElementById("rate").textContent = `24K · ₹${health.gold_rate_24k_inr}/g · ${health.skus} SKUs`;
  document.getElementById("dups").innerHTML = (dups.items || [])
    .slice(0, 8)
    .map(
      (p) =>
        `<div class="row">${p.left.sku} ↔ ${p.right.sku}<br/><span class="muted">${p.left.title} · sim ${p.similarity}</span></div>`
    )
    .join("");
  document.getElementById("gaps").innerHTML = (gaps.items || [])
    .slice(0, 10)
    .map((g) => `<div class="row">${g.sku}: ${(g.gaps || []).join(", ")}</div>`)
    .join("");
  if (metrics.eval_report) {
    document.getElementById("metrics").textContent = JSON.stringify(metrics.eval_report, null, 2);
  }
}

loadCatalog().catch(console.error);
loadOps().catch(console.error);
