(function () {
  const STORAGE = {
    hidden: "ebike_hidden_v1",
    baseline: "ebike_baseline_v1",
    baselineHighlight: "ebike_baseline_highlight_v1",
    custom: "ebike_custom_v1",
  };

  const PAGE_TITLE = "E-Bike & Scooter Comparison · Surf City HB";

  const catalogBikes = JSON.parse(document.getElementById("all-bikes-data")?.textContent || "[]");
  const config = JSON.parse(document.getElementById("app-config")?.textContent || "{}");
  const tierLabels = JSON.parse(document.getElementById("tier-labels-data")?.textContent || "{}");
  const legalRules = JSON.parse(document.getElementById("legal-rules-data")?.textContent || "{}");
  const safetyData = JSON.parse(document.getElementById("safety-data")?.textContent || "{}");
  const faqData = JSON.parse(document.getElementById("faq-data")?.textContent || "{}");

  const PREFERRED_COLORS = new Set(["white", "light_wood", "sand"]);
  const BRAKE_DISPLAY = {
    hydraulic_disc: { icon: "", label: "Hydraulic Disc", css_class: "brake-hydraulic_disc", glyph: true },
    mechanical_disc: { icon: "", label: "Mechanical Disc", css_class: "brake-mechanical_disc", glyph: true },
    rim: { icon: "⭕", label: "Rim Brake", css_class: "brake-rim" },
    coaster: { icon: "↩️", label: "Coaster", css_class: "brake-coaster" },
    electronic_disc: { icon: "⚡", label: "Disc + regen", css_class: "brake-electronic_disc" },
  };
  const BRAKE_SCORES = { coaster: 5, rim: 8, mechanical_disc: 18, hydraulic_disc: 25, electronic_disc: 20 };
  const FEATURE_DEFS = {
    lock_builtin: ["Built-in lock", "security", 8],
    lock_cable: ["Cable / U-lock mount", "security", 3],
    alarm: ["Anti-theft alarm", "security", 6],
    immobilizer: ["Motor immobilizer", "security", 5],
    gps_tracking: ["GPS live tracking", "tracking", 12],
    find_my: ["Find My / location history", "tracking", 10],
    geofence: ["Geofence alerts", "tracking", 6],
    companion_app: ["Companion app", "app", 8],
    ride_history: ["Ride stats & history", "app", 4],
    firmware_ota: ["OTA firmware updates", "app", 5],
    remote_lock: ["Remote lock / unlock", "app", 6],
    bluetooth_speaker: ["Bluetooth speaker", "audio", 7],
    phone_mount: ["Phone mount included", "audio", 3],
    suspension: ["Suspension", "luxury", 8],
    regen_braking: ["Regen braking", "luxury", 5],
    cruise_control: ["Cruise control", "luxury", 4],
    turn_signals: ["Turn signals", "luxury", 6],
    keyless_start: ["Keyless / NFC start", "luxury", 4],
    fold_compact: ["Compact fold", "luxury", 3],
    ip_rating: ["Water resistance IPX5+", "luxury", 5],
  };
  const FEATURE_GROUPS = [
    ["security", "Security"],
    ["tracking", "Tracking"],
    ["app", "App"],
    ["audio", "Audio"],
    ["luxury", "Premium"],
  ];
  const CHARGE_LABELS = {
    onboard: "Onboard plug",
    removable: "Removable pack",
    removable_keyed: "Removable (keyed)",
    none: "N/A",
  };
  const EFFICIENCY_BANDS = [
    [9, "excellent"],
    [12, "good"],
    [16, "average"],
  ];
  const EFFICIENCY_HIGHLIGHT_MAX_WH_MI = 12;

  const colorFilter = document.getElementById("colorFilter");
  const efficiencyFilter = document.getElementById("efficiencyFilter");
  const vehicleFilter = document.getElementById("vehicleFilter");
  const smartFilter = document.getElementById("smartFilter");
  const speedFilter = document.getElementById("speedFilter");
  const legalFilter = document.getElementById("legalFilter");
  const priceFilter = document.getElementById("priceFilter");
  const tierTabs = document.getElementById("tierTabs");
  const cardGrid = document.getElementById("cardGrid");
  const cards = () => document.querySelectorAll(".bike-card");
  const rows = () => document.querySelectorAll("#compareTable tbody tr");

  const tableTierFilter = document.getElementById("tableTierFilter");
  const tableClassFilter = document.getElementById("tableClassFilter");
  const tableLegalFilter = document.getElementById("tableLegalFilter");
  const tableColorFilter = document.getElementById("tableColorFilter");

  let compareIds = [];
  let compareDrawerOpen = false;
  const MAX_COMPARE = 3;

  const compareDrawer = document.getElementById("compareDrawer");
  const compareFab = document.getElementById("btnCompareFab");
  const compareFabCount = document.getElementById("compareFabCount");
  const heroCompareLink = document.getElementById("heroCompareLink");

  let hiddenIds = JSON.parse(localStorage.getItem(STORAGE.hidden) || "[]");
  let customBikes = JSON.parse(localStorage.getItem(STORAGE.custom) || "[]");
  let baselineId = localStorage.getItem(STORAGE.baseline) || config.defaultBaselineId || "firmstrong-urban-lady";
  let baselineHighlightEnabled = localStorage.getItem(STORAGE.baselineHighlight) === "1";
  let currentDetailId = null;

  const browseView = document.getElementById("browseView");
  const detailView = document.getElementById("detailView");

  function saveHidden() {
    localStorage.setItem(STORAGE.hidden, JSON.stringify(hiddenIds));
  }
  function saveCustom() {
    localStorage.setItem(STORAGE.custom, JSON.stringify(customBikes));
  }
  function saveBaseline() {
    localStorage.setItem(STORAGE.baseline, baselineId);
  }
  function saveBaselineHighlight() {
    localStorage.setItem(STORAGE.baselineHighlight, baselineHighlightEnabled ? "1" : "0");
  }
  function enableBaselineHighlight() {
    baselineHighlightEnabled = true;
    saveBaselineHighlight();
  }

  function formatMoney(n) {
    const val = parseFloat(n);
    if (Number.isNaN(val)) return "—";
    if (val === Math.floor(val)) return `$${val.toLocaleString()}`;
    return `$${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }

  function whPerMile(wh, miles) {
    if (wh && miles && miles > 0) return Math.round((wh / miles) * 10) / 10;
    return null;
  }

  function milesPerKwh(wh, miles) {
    if (wh && miles && wh > 0) return Math.round((miles / wh) * 10000) / 10;
    return null;
  }

  function efficiencyRating(whPerMi) {
    if (whPerMi == null) return null;
    for (const [limit, label] of EFFICIENCY_BANDS) {
      if (whPerMi <= limit) return label;
    }
    return "poor";
  }

  function efficiencyLabel(whPerMiPas, whPerMiThr, mpkwhPas) {
    const parts = [];
    if (whPerMiPas != null) parts.push(`${whPerMiPas} Wh/mi PAS`);
    if (whPerMiThr != null) parts.push(`${whPerMiThr} Wh/mi throttle`);
    if (mpkwhPas != null) parts.push(`${mpkwhPas} mi/kWh`);
    return parts.length ? parts.join(" · ") : "—";
  }

  function formatBattery(bike) {
    const v = bike.battery_voltage_v;
    const ah = bike.battery_capacity_ah;
    const wh = bike.battery_wh || (v && ah ? Math.round(v * ah) : null);
    const pas = bike.battery_range_miles_pas;
    const thr = bike.battery_range_miles_throttle;
    const hrs = bike.battery_charge_hours;
    const method = bike.battery_charge_method || "";
    const notes = bike.battery_charge_notes || "";
    const ahAlt = bike.battery_capacity_ah_alt;
    const whPerMiPas = whPerMile(wh, pas);
    const whPerMiThr = whPerMile(wh, thr);
    const mpkwhPas = milesPerKwh(wh, pas);
    const effRating = efficiencyRating(whPerMiPas);

    if (method === "none" || (!v && !ah && !pas)) {
      return {
        has_battery: false,
        capacity_label: "—",
        range_label: "—",
        charge_label: "—",
        efficiency_label: "—",
        efficiency_rating: null,
        summary: "—",
        charge_notes: notes,
        wh_per_mile_pas: null,
        is_efficient: false,
      };
    }
    let capacity_label = "—";
    if (v && ah) {
      capacity_label = `${v}V · ${ah}Ah`;
      if (ahAlt) capacity_label += ` (or ${ahAlt}Ah)`;
      if (wh) capacity_label += ` · ${wh}Wh`;
    } else if (ah) capacity_label = `${ah}Ah`;

    const rangeParts = [];
    if (pas) rangeParts.push(`${pas} mi PAS`);
    if (thr) rangeParts.push(`${thr} mi throttle`);
    const range_label = rangeParts.length ? rangeParts.join(" · ") : "—";

    const chargeParts = [];
    if (hrs) chargeParts.push(`~${hrs} hr`);
    if (method && method !== "none") chargeParts.push(CHARGE_LABELS[method] || method);
    const charge_label = chargeParts.length ? chargeParts.join(" · ") : "—";

    const efficiency_label = efficiencyLabel(whPerMiPas, whPerMiThr, mpkwhPas);

    return {
      has_battery: true,
      capacity_label,
      range_label,
      charge_label,
      charge_notes: notes,
      efficiency_label,
      efficiency_rating: effRating,
      summary: range_label !== "—" ? range_label : capacity_label,
      range_miles: pas,
      capacity_ah: ah,
      battery_wh: wh,
      charge_method: method,
      wh_per_mile_pas: whPerMiPas,
      wh_per_mile_throttle: whPerMiThr,
      miles_per_kwh_pas: mpkwhPas,
      is_efficient: whPerMiPas != null && whPerMiPas <= EFFICIENCY_HIGHLIGHT_MAX_WH_MI,
    };
  }

  function batteryHtml(bike) {
    const b = formatBattery(bike);
    if (!b.has_battery) return `<span class="battery-inline">—</span>`;
    return `<span class="battery-inline" title="${b.charge_notes || ""}">${b.range_label} · ${b.capacity_label}</span>`;
  }

  function ipRatingOk(features) {
    const ip = (features?.ip_rating || "").toUpperCase();
    return ["IPX5", "IPX6", "IPX7", "IP54", "IP55", "IP65"].some((x) => ip.includes(x));
  }

  function buildFeatureChecklist(features) {
    const feats = features || {};
    return Object.entries(FEATURE_DEFS).map(([key, [label, group, _w]]) => {
      const ok = key === "ip_rating" ? ipRatingOk(feats) : !!feats[key];
      return { key, group, label, ok, value: key === "ip_rating" ? feats.ip_rating || "—" : ok };
    });
  }

  function computeLuxuryScore(features) {
    let score = 0;
    const feats = features || {};
    Object.entries(FEATURE_DEFS).forEach(([key, [, , weight]]) => {
      if (key === "ip_rating" ? ipRatingOk(feats) : feats[key]) score += weight;
    });
    return Math.min(score, 100);
  }

  function formatFeatureDisplay(features, checklist) {
    const list = checklist || buildFeatureChecklist(features);
    const byGroup = {};
    let total = 0;
    list.forEach((item) => {
      if (item.ok) {
        total += 1;
        byGroup[item.group] = (byGroup[item.group] || 0) + 1;
      }
    });
    const perks = list.filter((i) => i.ok).map((i) => i.label).slice(0, 4);
    const f = features || {};
    return {
      luxury_score: computeLuxuryScore(f),
      feature_count: total,
      by_group: byGroup,
      perks_label: perks.length ? perks.join(" · ") : "—",
      has_app: !!f.companion_app,
      has_tracking: !!(f.gps_tracking || f.find_my),
      has_security: !!(f.lock_builtin || f.alarm || f.immobilizer),
      has_audio: !!(f.bluetooth_speaker || f.phone_mount),
      is_smart: !!(f.companion_app && (f.gps_tracking || f.find_my || f.lock_builtin)),
    };
  }

  const FEATURE_COLLAPSE_ACTIVE = 4;
  const FEATURE_COLLAPSE_GROUPS = 2;

  function detailSpecBlock(title, bodyHtml, { className = "" } = {}) {
    const body = (bodyHtml || "").trim();
    if (!body) return "";
    const extra = className ? ` ${className}` : "";
    return `<section class="detail-spec-block${extra}"><h3>${title}</h3><div class="detail-spec-body">${body}</div></section>`;
  }

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function productLabel(bike) {
    return `${bike.brand} ${bike.model}`;
  }

  function buildProductFaq(bike) {
    const items = [];
    const isScooter = bike.vehicle_type === "scooter";
    const name = productLabel(bike);
    const bd = formatBattery(bike);
    const brake = formatBrake(bike.brake_type);
    const lights = bike.lights || {};

    if (bike.legal_for_age === false) {
      items.push({
        q: `Can a 12-year-old legally ride the ${name}?`,
        a: isScooter
          ? "This model is flagged as not appropriate for a 12-year-old under our Huntington Beach rules checklist. Review local scooter path limits and helmet requirements before riding."
          : bike.e_bike_class === 3
            ? "No — California prohibits riders under 16 from operating Class 3 e-bikes (28 mph assist). Pick a Class 1 or 2 model capped at 20 mph instead."
            : "Our checklist flags legal concerns for a 12-year-old on this model. Read the Legal notes above and verify current California and HB rules.",
      });
    } else {
      const classNote =
        !isScooter && bike.e_bike_class
          ? ` It is a Class ${bike.e_bike_class} e-bike (${legalRules.classes?.[bike.e_bike_class]?.description || "see California e-bike classes"}).`
          : "";
      items.push({
        q: `Can a 12-year-old ride the ${name}?`,
        a: `Generally yes, with rules: riders under 18 need a helmet, night riding requires lights, and HB beach/park paths are 10 mph max.${classNote}`,
      });
    }

    items.push({
      q: `How fast is the ${name}?`,
      a: `Top speed is ${bike.max_speed_mph || "—"} mph. On Huntington Beach paths you should ride at 10 mph (5 mph near pedestrians) even if the ${isScooter ? "scooter" : "bike"} can go faster.`,
    });

    if (bd.range_label && bd.range_label !== "—") {
      items.push({
        q: `What range can you expect on the ${name}?`,
        a: `Estimated range is ${bd.range_label} (${bd.capacity_label} pack). Real range varies with rider weight, hills, wind, and how much you use throttle vs pedal-assist.`,
      });
    }

    items.push({
      q: `How safe is the ${name} for a young rider?`,
      a: `Safety score: ${bike.safety_score ?? "—"}/100. Brakes: ${brake.label}. Front light: ${lights.front ? "yes" : "no"}. Rear light: ${lights.rear ? "yes" : "no"}. UL battery cert: ${bike.ul_certified ? "yes" : "no"}. Higher scores mean more safety equipment — not a guarantee against injury.`,
    });

    if (!isScooter && bike.e_bike_class) {
      const cls = legalRules.classes?.[String(bike.e_bike_class)];
      items.push({
        q: `What e-bike class is the ${name}?`,
        a: cls
          ? `Class ${bike.e_bike_class}: ${cls.description}. ${cls.legal_under_16 ? "Legal for under-16 riders in California." : "Not legal for riders under 16 in California."}`
          : `Listed as Class ${bike.e_bike_class}. Class 3 models are illegal for riders under 16 in California.`,
      });
    }

    const smart = bike.feature_display || formatFeatureDisplay(bike.features || {}, bike.feature_checklist || []);
    if (smart.is_smart || smart.luxury_score > 0) {
      items.push({
        q: `Does the ${name} have app or anti-theft features?`,
        a: smart.perks_label && smart.perks_label !== "—"
          ? `Yes — highlights include ${smart.perks_label}. Use the app for firmware updates and tracking, but still use a physical lock.`
          : "Some smart features are listed above. Check the Smart & connectivity section for GPS, app, and lock options.",
      });
    } else if (isScooter) {
      items.push({
        q: `Is the ${name} a "smart" scooter?`,
        a: "This model has few or no connected features in our database. Physical locks and parking in visible areas matter more than app features here.",
      });
    }

    const vs = bike.vs_baseline;
    const baseline = getBaseline();
    if (vs && bike.id !== baseline.id) {
      items.push({
        q: `How does the ${name} compare on price?`,
        a: `Versus ${baseline.brand} ${baseline.model} (${formatMoney(bikePrice(baseline))}), this ${isScooter ? "scooter" : "e-bike"} costs about ${vs.price_multiplier}× and is ${vs.speed_delta_mph >= 0 ? "+" : ""}${vs.speed_delta_mph} mph faster.`,
      });
    }

    const issues = bike.legal_issues || [];
    if (issues.length) {
      items.push({
        q: `Any local riding restrictions for the ${name}?`,
        a: issues.slice(0, 3).join(" "),
      });
    }

    const pool = [
      ...(faqData.shared || []),
      ...(isScooter ? faqData.scooter || [] : faqData.ebike || []),
    ];
    pool.slice(0, 2).forEach((entry) => {
      items.push({ q: entry.q, a: entry.a, general: true });
    });

    return items;
  }

  function faqAccordionHtml(items, { productId = "" } = {}) {
    if (!items.length) return "";
    const rows = items
      .map(
        (item) => `
      <details class="faq-item">
        <summary class="faq-question">${escapeHtml(item.q)}</summary>
        <div class="faq-answer"><p>${escapeHtml(item.a)}</p></div>
      </details>`
      )
      .join("");
    return `<div class="faq-accordion" data-product-id="${escapeHtml(productId)}">${rows}</div>`;
  }

  function faqSectionHtml(items, { productId = "" } = {}) {
    if (!items.length) return "";
    return `<details class="detail-faq-fold">
      <summary class="detail-faq-summary">Common questions about this ride</summary>
      <div class="detail-faq-inner">${faqAccordionHtml(items, { productId })}</div>
    </details>`;
  }

  let chatDrawerOpen = false;
  let chatHistory = [];
  const chatDrawer = document.getElementById("chatDrawer");
  const chatMessages = document.getElementById("chatMessages");
  const chatSuggestions = document.getElementById("chatSuggestions");

  function chatContextBike() {
    const id = currentDetailId;
    return id && bikeMap[id] ? bikeMap[id] : null;
  }

  function chatGreeting() {
    const bike = chatContextBike();
    if (bike) {
      return `Hi! I can answer questions about the ${productLabel(bike)}, compare it to other rides in our catalog, or explain HB safety rules. What would you like to know?`;
    }
    return "Hi! Ask me about e-bikes and scooters in this comparison — safety scores, California rules, battery range, or which models fit a 12-year-old in Huntington Beach.";
  }

  function appendChatMessage(role, text) {
    if (!chatMessages) return;
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble chat-bubble--${role}`;
    bubble.innerHTML = `<p>${escapeHtml(text).replace(/\n/g, "<br>")}</p>`;
    chatMessages.appendChild(bubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    chatHistory.push({ role, text });
  }

  function renderChatSuggestions() {
    if (!chatSuggestions) return;
    const bike = chatContextBike();
    const suggestions = bike
      ? [
          `Is the ${bike.brand} ${bike.model} safe for a 12-year-old?`,
          `What is the range on this ${bike.vehicle_type === "scooter" ? "scooter" : "bike"}?`,
          "What are HB path speed limits?",
          "Compare this to my baseline",
        ]
      : [
          "Best budget e-bike for a 12-year-old?",
          "Class 2 vs Class 3 — what's the difference?",
          "Do scooters need UL certification?",
          "Explain the safety score",
        ];
    chatSuggestions.innerHTML = suggestions
      .map((s) => `<button type="button" class="chat-chip" data-chat-suggest="${escapeHtml(s)}">${escapeHtml(s)}</button>`)
      .join("");
  }

  function visibleCatalog() {
    return Object.values(bikeMap).filter((b) => !b.is_baseline && !hiddenIds.includes(b.id));
  }

  function answerChatLocal(query) {
    const q = query.trim();
    const lower = q.toLowerCase();
    const bike = chatContextBike();
    const baseline = getBaseline();

    if (/^(hi|hello|hey|help)\b/.test(lower)) return chatGreeting();

    if (bike && /(this|current|it\b|the one)/.test(lower)) {
      const bd = formatBattery(bike);
      return `${productLabel(bike)}: ${formatMoney(bikePrice(bike))} landed, ${bike.max_speed_mph} mph, safety ${bike.safety_score}/100. Range ${bd.range_label}. ${bike.legal_for_age !== false ? "Passes our age-12 legal checklist." : "Fails our age-12 legal checklist — see PDP legal notes."}`;
    }

    if (bike && /range|battery|charge|mile|wh\b/.test(lower)) {
      const bd = formatBattery(bike);
      return `On the ${productLabel(bike)}: ${bd.range_label} estimated range, ${bd.capacity_label} battery, charges via ${bd.charge_label}. ${bd.charge_notes || ""}`.trim();
    }

    if (/(safety|brake|light|ul|cert)/.test(lower)) {
      if (bike) {
        const brake = formatBrake(bike.brake_type);
        const lights = bike.lights || {};
        return `${productLabel(bike)} safety score ${bike.safety_score}/100. Brakes: ${brake.label}. Lights F/R: ${lights.front ? "yes" : "no"}/${lights.rear ? "yes" : "no"}. UL cert: ${bike.ul_certified ? "yes" : "no"}.`;
      }
      return (safetyData.glossary && safetyData.glossary["Class 1"])
        ? `Safety scores sum brakes, lights, reflectors, UL cert, and speed limiter. ${faqData.shared?.find((f) => f.id === "safety-score")?.a || ""}`
        : "Safety scores weight equipment on each model — higher is better, but no score predicts crashes.";
    }

    if (/(legal|law|age|12|16|helmet|class\s*[123])/i.test(q)) {
      const parts = [];
      (legalRules.california || []).slice(0, 3).forEach((r) => parts.push(`${r.title}: ${r.summary}`));
      (legalRules.huntington_beach || []).slice(0, 2).forEach((r) => parts.push(`${r.title}: ${r.summary}`));
      if (bike?.e_bike_class === 3) parts.unshift("This PDP model is Class 3 — illegal for under-16 in CA.");
      if (bike?.vehicle_type === "scooter") {
        (legalRules.scooters || []).slice(0, 2).forEach((r) => parts.push(`${r.title}: ${r.summary}`));
      }
      return parts.join("\n\n");
    }

    if (/(hb|huntington|beach|path|10\s*mph|sidewalk)/i.test(q)) {
      const hb = (legalRules.huntington_beach || []).map((r) => `• ${r.title}: ${r.summary}`).join("\n");
      return hb || "Huntington Beach paths are generally 10 mph max (5 mph near pedestrians). Check HBPD alternative vehicle safety page for updates.";
    }

    if (bike && /compare|vs|baseline|difference/.test(lower)) {
      const vs = bike.vs_baseline;
      if (!vs) return `No baseline comparison saved for ${productLabel(bike)}.`;
      return `${productLabel(bike)} vs ${baseline.brand} ${baseline.model}: ${vs.price_multiplier}× price, ${vs.speed_delta_mph >= 0 ? "+" : ""}${vs.speed_delta_mph} mph, brake upgrade: ${vs.brake_upgrade || "—"}.`;
    }

    if (/(cheapest|budget|affordable|under \$)/i.test(q)) {
      const tier = /scooter/.test(lower) ? "scooter" : "budget";
      const pool = visibleCatalog().filter((b) => b.tier === tier);
      pool.sort((a, b) => bikePrice(a) - bikePrice(b));
      const top = pool.slice(0, 3);
      if (!top.length) return "No matching models in the current catalog.";
      return `Lowest landed ${tier === "scooter" ? "scooters" : "budget e-bikes"}:\n${top.map((b) => `• ${productLabel(b)} — ${formatMoney(bikePrice(b))} (safety ${b.safety_score})`).join("\n")}`;
    }

    if (/(best|recommend|pick|which)/i.test(q) && /(12|kid|child|teen)/i.test(q)) {
      const pool = visibleCatalog()
        .filter((b) => b.legal_for_age !== false && (b.safety_score || 0) >= 50)
        .sort((a, b) => (b.safety_score || 0) - (a.safety_score || 0) || bikePrice(a) - bikePrice(b));
      const top = pool.slice(0, 4);
      return top.length
        ? `Models that pass our age-12 checklist with solid safety scores:\n${top.map((b) => `• ${productLabel(b)} — safety ${b.safety_score}, ${formatMoney(bikePrice(b))}`).join("\n")}\nOpen any card for full specs.`
        : "No models match that filter right now — try widening your tier or vehicle filters.";
    }

    if (/scooter/.test(lower) && !bike) {
      const entry = (faqData.scooter || [])[0];
      return entry ? `${entry.q} ${entry.a}` : "E-scooters need helmets under 18, UL electrical certification is recommended, and HB path speed limits apply.";
    }

    if (/class\s*1|class\s*2|class\s*3/.test(lower)) {
      const g = safetyData.glossary || {};
      return ["Class 1", "Class 2", "Class 3"]
        .map((k) => (g[k] ? `${k}: ${g[k]}` : null))
        .filter(Boolean)
        .join("\n");
    }

    if (bike) {
      const faq = buildProductFaq(bike).find((item) => lower.includes(item.q.slice(0, 12).toLowerCase()));
      if (faq) return faq.a;
      return `I don't have a precise answer for that. On ${productLabel(bike)}: ${bike.max_speed_mph} mph, safety ${bike.safety_score}, ${bike.legal_for_age !== false ? "legal for age 12 per our checklist" : "not legal for age 12 per our checklist"}. Try asking about range, brakes, HB rules, or "compare to baseline".`;
    }

    const general = [...(faqData.shared || []), ...(faqData.ebike || [])].find((f) =>
      lower.split(/\s+/).some((w) => w.length > 4 && f.q.toLowerCase().includes(w))
    );
    if (general) return general.a;

    return "Try asking about safety scores, California helmet rules, Class 1/2/3, HB 10 mph paths, battery range, or open a product page and ask about that specific ride.";
  }

  async function answerChat(query) {
    const apiUrl = config.chatApiUrl;
    if (apiUrl) {
      try {
        const resp = await fetch(apiUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: query,
            productId: currentDetailId,
            history: chatHistory.slice(-6),
          }),
        });
        if (resp.ok) {
          const data = await resp.json();
          if (data.reply) return data.reply;
        }
      } catch (_err) {
        /* fall through to local */
      }
    }
    return answerChatLocal(query);
  }

  function openChatDrawer(prefill) {
    if (!chatDrawer) return;
    chatDrawerOpen = true;
    chatDrawer.hidden = false;
    chatDrawer.setAttribute("aria-hidden", "false");
    document.body.classList.add("chat-drawer-open");
    const sub = document.getElementById("chatDrawerSub");
    const bike = chatContextBike();
    if (sub) {
      sub.textContent = bike
        ? `Answering about ${productLabel(bike)} — plus catalog & HB rules`
        : "Ask about bikes, scooters, safety, and local rules";
    }
    renderChatSuggestions();
    if (!chatMessages?.childElementCount) {
      appendChatMessage("assistant", chatGreeting());
    }
    if (prefill) {
      document.getElementById("chatInput").value = prefill;
      submitChat(prefill);
    } else {
      document.getElementById("chatInput")?.focus();
    }
  }

  function closeChatDrawer() {
    if (!chatDrawer) return;
    chatDrawerOpen = false;
    chatDrawer.hidden = true;
    chatDrawer.setAttribute("aria-hidden", "true");
    document.body.classList.remove("chat-drawer-open");
  }

  async function submitChat(text) {
    const input = document.getElementById("chatInput");
    const q = (text || input?.value || "").trim();
    if (!q) return;
    if (input) input.value = "";
    appendChatMessage("user", q);
    const sendBtn = document.getElementById("btnChatSend");
    if (sendBtn) sendBtn.disabled = true;
    appendChatMessage("assistant", "…");
    const pending = chatMessages?.lastElementChild;
    const reply = await answerChat(q);
    if (pending) pending.remove();
    appendChatMessage("assistant", reply);
    if (sendBtn) sendBtn.disabled = false;
    input?.focus();
  }

  function featureBlockHtml(bike, { detail = false } = {}) {
    const feats = bike.features || {};
    const checklist = bike.feature_checklist?.length ? bike.feature_checklist : buildFeatureChecklist(feats);
    const hasFeatures = checklist.some((i) => i.ok);
    if (!detail && !hasFeatures) return "";
    const display = bike.feature_display || formatFeatureDisplay(feats, checklist);
    const activeItems = checklist.filter((i) => i.ok);
    const groupRows = FEATURE_GROUPS.map(([gid, glabel]) => {
      const items = checklist.filter((i) => i.group === gid);
      if (!items.length) return "";
      const active = items.filter((i) => i.ok);
      if (!detail && !active.length) return "";
      const tags = (detail ? items : active)
        .map((i) => `<span class="feature-tag${i.ok ? " ok" : " miss"}" title="${i.label}">${i.label}</span>`)
        .join("");
      return `<li class="feature-group-row"><span class="${detail ? "spec-label" : "bf-label"}">${glabel}</span><span class="feature-tags">${tags}</span></li>`;
    })
      .filter(Boolean)
      .join("");
    const groupCount = groupRows ? groupRows.split("feature-group-row").length - 1 : 0;
    const scoreBadge =
      display.luxury_score > 0
        ? `<span class="luxury-score-badge">★ ${display.luxury_score}</span>`
        : "";
    if (detail && groupRows) {
      const shouldCollapse =
        activeItems.length > FEATURE_COLLAPSE_ACTIVE || groupCount > FEATURE_COLLAPSE_GROUPS;
      if (shouldCollapse) {
        const previewTags = activeItems
          .slice(0, FEATURE_COLLAPSE_ACTIVE)
          .map((i) => `<span class="feature-tag ok" title="${i.label}">${i.label}</span>`)
          .join("");
        const moreCount = Math.max(0, activeItems.length - FEATURE_COLLAPSE_ACTIVE);
        const ellipsis = moreCount > 0 ? `<span class="feature-more-ellipsis">… +${moreCount} more</span>` : "";
        const toggleLabel = `Show all features (${activeItems.length})`;
        return `${scoreBadge}
          <div class="feature-detail-collapsible is-collapsed" data-feature-count="${activeItems.length}">
            <div class="feature-detail-preview">
              <div class="feature-tags feature-tags--preview">${previewTags}${ellipsis}</div>
            </div>
            <div class="feature-detail-full" hidden>
              <ul class="feature-facts feature-facts--detail">${groupRows}</ul>
            </div>
            <button type="button" class="btn-spec-toggle" aria-expanded="false">${toggleLabel}</button>
          </div>`;
      }
    }
    const inner = groupRows
      ? `<ul class="feature-facts feature-facts${detail ? "--detail" : ""}">${groupRows}</ul>`
      : `<p class="detail-spec-empty">No app or smart features listed for this model.</p>`;
    if (detail) return `${scoreBadge}${inner}`;
    return `<div class="feature-equip">
      <span class="feature-equip-title">Smart &amp; luxury ${scoreBadge}</span>
      ${inner}
    </div>`;
  }

  function factRow(label, valueHtml, { detail = false } = {}) {
    const labelClass = detail ? "spec-label" : "bf-label";
    const valueClass = detail ? "spec-value" : "fact-value";
    return `<li><span class="${labelClass}">${label}</span><span class="${valueClass}">${valueHtml}</span></li>`;
  }

  function batteryBlockHtml(bike, { detail = false } = {}) {
    const b = formatBattery(bike);
    const note = b.charge_notes ? `<span class="bf-note" title="${b.charge_notes}">ⓘ</span>` : "";
    const effValue =
      b.efficiency_label && b.efficiency_label !== "—"
        ? `<span class="efficiency-tag efficiency-readout efficiency-${b.efficiency_rating || "unknown"}">${b.efficiency_label}</span>`
        : "";
    const rows = `<ul class="battery-facts${detail ? " battery-facts--detail" : ""}">
        ${factRow("Range", b.range_label, { detail })}
        ${factRow("Capacity", b.capacity_label, { detail })}
        ${factRow("Charging", `${b.charge_label}${note}`, { detail })}
        ${effValue ? factRow("Efficiency", effValue, { detail }) : ""}
      </ul>`;
    if (detail) return rows;
    return `<div class="battery-equip">
      <span class="battery-equip-title">Battery &amp; range</span>
      ${rows}
    </div>`;
  }

  function formatBrake(brakeType) {
    const key = (brakeType || "rim").toLowerCase();
    const info = BRAKE_DISPLAY[key] || { icon: "❓", label: key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()) };
    return { icon: info.icon || "", label: info.label, key, css_class: info.css_class || "", glyph: !!info.glyph };
  }

  function bikePrice(bike) {
    return bike.price ?? bike.landed_price_usd ?? bike.price_usd ?? 0;
  }

  function computeSafetyScore(bike) {
    if (bike.vehicle_type === "scooter") {
      let score = 15;
      if (bike.brake_type === "electronic_disc") score += 20;
      else if (["mechanical_disc", "hydraulic_disc"].includes(bike.brake_type)) score += 18;
      const lights = bike.lights || {};
      if (lights.front) score += 12;
      if (lights.rear) score += 12;
      if (bike.ul_certified) score += 15;
      const maxSpd = bike.max_speed_mph || 20;
      if (maxSpd <= 20) score += 12;
      else if (maxSpd <= 25) score += 6;
      if (ipRatingOk(bike.features)) score += 8;
      if (bike.features?.alarm || bike.features?.lock_builtin) score += 5;
      return Math.min(score, 100);
    }
    let score = BRAKE_SCORES[bike.brake_type] || 5;
    const lights = bike.lights || {};
    if (lights.front) score += 10;
    if (lights.rear) score += 10;
    if (bike.reflectors) score += 5;
    if ((bike.tire_width_in || 0) >= 2.4) score += 5;
    const maxSpd = bike.max_speed_mph || 20;
    if (maxSpd < 20) score += 12;
    else if (maxSpd <= 20) score += 10;
    else if (maxSpd <= 28) score += 5;
    if (bike.ul_certified) score += 5;
    if (bike.brakes_front) score += 5;
    return Math.min(score, 100);
  }

  function buildChecklist(bike) {
    const lights = bike.lights || {};
    const brake = formatBrake(bike.brake_type);
    const tireW = bike.tire_width_in;
    return [
      { key: "brake_type", row_label: "Brakes", label: brake.label, ok: ["mechanical_disc", "hydraulic_disc"].includes(bike.brake_type) },
      { key: "front_light", row_label: "Front light", label: "Front light", ok: !!lights.front },
      { key: "rear_light", row_label: "Rear light", label: "Rear light", ok: !!lights.rear },
      { key: "ul_cert", row_label: "UL battery cert", label: "UL battery cert", ok: !!bike.ul_certified },
    ];
  }

  function compareToBaseline(bike, baseline) {
    const bPrice = bikePrice(baseline) || 289;
    const ePrice = bikePrice(bike);
    const ratio = bPrice ? Math.round((ePrice / bPrice) * 10) / 10 : null;
    const bSpeed = baseline.max_speed_mph || 15;
    const eSpeed = bike.max_speed_mph || 20;
    return {
      price_multiplier: ratio,
      speed_delta_mph: Math.round((eSpeed - bSpeed) * 10) / 10,
      baseline_model: baseline.model,
      baseline_price: bPrice,
    };
  }

  function enrichBike(raw) {
    const bike = { ...raw };
    bike.price = bikePrice(bike);
    bike.brake_display = bike.brake_display || formatBrake(bike.brake_type);
    if (!bike.safety_score) bike.safety_score = computeSafetyScore(bike);
    if (!bike.safety_checklist?.length) bike.safety_checklist = buildChecklist(bike);
    bike.tier_label = bike.tier_label || tierLabels[bike.tier] || bike.tier;
    bike.battery_display = formatBattery(bike);
    if (bike.features && Object.keys(bike.features).length) {
      bike.feature_checklist = bike.feature_checklist?.length ? bike.feature_checklist : buildFeatureChecklist(bike.features);
      bike.feature_display = bike.feature_display || formatFeatureDisplay(bike.features, bike.feature_checklist);
      bike.luxury_score = bike.feature_display.luxury_score;
    }
    return bike;
  }

  function getCatalogMap() {
    const map = {};
    catalogBikes.forEach((b) => {
      map[b.id] = enrichBike(b);
    });
    customBikes.forEach((b) => {
      map[b.id] = enrichBike({ ...b, custom: true });
    });
    return map;
  }

  let bikeMap = getCatalogMap();

  function getBaseline() {
    return bikeMap[baselineId] || bikeMap[config.defaultBaselineId] || catalogBikes[0];
  }

  function applyBaselineToAll() {
    const baseline = getBaseline();
    Object.values(bikeMap).forEach((bike) => {
      if (bike.id !== baseline.id) {
        bike.vs_baseline = compareToBaseline(bike, baseline);
      }
    });
  }

  function hasPreferredColor(colorsStr) {
    return (colorsStr || "").split(",").some((c) => PREFERRED_COLORS.has(c.trim()));
  }

  function brakeHtml(bike) {
    const b = bike.brake_display || {};
    const label = b.label || bike.brake_type || "—";
    const cls = b.css_class ? ` ${b.css_class}` : "";
    const icon = b.glyph ? "" : `${b.icon || "❓"} `;
    return `<span class="brake-label${cls}" title="${label}">${icon}${label}</span>`;
  }

  function yesNo(ok) {
    return ok ? '<span class="cell-yes">✓ Yes</span>' : '<span class="cell-no">✗ No</span>';
  }

  function speedMatches(speed, filter) {
    const s = parseFloat(speed) || 0;
    if (filter === "under20") return s > 0 && s < 20;
    if (filter === "20") return s === 20;
    if (filter === "28") return s >= 28;
    return true;
  }

  function isEfficientBike(bike) {
    const b = bike.battery_display || formatBattery(bike);
    return !!b.is_efficient;
  }

  function isSmartRide(bike) {
    return !!(bike.feature_display?.is_smart || formatFeatureDisplay(bike.features).is_smart);
  }

  function getCardFilters() {
    return {
      tier: document.querySelector(".tier-tab.active")?.dataset.tier || "all",
      vehicle: vehicleFilter?.value || "all",
      highlightColors: colorFilter?.checked,
      highlightEfficient: efficiencyFilter?.checked,
      highlightSmart: smartFilter?.checked,
      legal: legalFilter?.value || "all",
      maxPrice: priceFilter?.value || "all",
      speed: speedFilter?.value || "all",
    };
  }

  function getTableFilters() {
    return {
      tier: tableTierFilter?.value || "all",
      cls: tableClassFilter?.value || "all",
      legal: tableLegalFilter?.value || "all",
      highlightColors: tableColorFilter?.checked,
    };
  }

  function isCardVisible(card, f) {
    if (hiddenIds.includes(card.dataset.id)) return false;
    const tierOk = f.tier === "all" || card.dataset.tier === f.tier;
    const legalOk = f.legal === "all" || card.dataset.legal === f.legal;
    const price = parseFloat(card.dataset.price) || 0;
    const priceOk = f.maxPrice === "all" || price <= parseFloat(f.maxPrice);
    const speedOk = speedMatches(card.dataset.speed, f.speed);
    const vehicleOk = f.vehicle === "all" || card.dataset.vehicle === f.vehicle;
    return tierOk && legalOk && priceOk && speedOk && vehicleOk;
  }

  function getVisibleBikesForCharts() {
    const f = getCardFilters();
    return [...cards()]
      .filter((card) => isCardVisible(card, f))
      .map((card) => bikeMap[card.dataset.id])
      .filter(Boolean);
  }

  function applyCardFilters() {
    const f = getCardFilters();
    cards().forEach((card) => {
      const visible = isCardVisible(card, f);
      card.classList.toggle("hidden", !visible);
      card.classList.toggle("user-hidden", hiddenIds.includes(card.dataset.id));
      card.classList.toggle("color-preferred", f.highlightColors && hasPreferredColor(card.dataset.colors));
      const bike = bikeMap[card.dataset.id];
      card.classList.toggle("efficiency-preferred", f.highlightEfficient && bike && isEfficientBike(bike));
      card.classList.toggle("smart-preferred", f.highlightSmart && bike && isSmartRide(bike));
      card.classList.toggle("is-baseline", baselineHighlightEnabled && card.dataset.id === baselineId);
    });
    updateHiddenUi();
    renderCharts();
  }

  function applyTableFilters() {
    const f = getTableFilters();
    rows().forEach((row) => {
      if (hiddenIds.includes(row.dataset.id)) {
        row.classList.add("hidden");
        return;
      }
      const tierOk = f.tier === "all" || row.dataset.tier === f.tier;
      const classOk = f.cls === "all" || row.dataset.class === f.cls;
      const legalOk = f.legal === "all" || row.dataset.legal === f.legal;
      row.classList.toggle("hidden", !(tierOk && classOk && legalOk));
      row.classList.toggle("color-preferred", f.highlightColors && hasPreferredColor(row.dataset.colors));
    });
  }

  function renderBaselinePanel() {
    const baseline = getBaseline();
    const media = document.getElementById("baselineMedia");
    const details = document.getElementById("baselineDetails");
    const select = document.getElementById("baselineSelect");
    if (!media || !details || !select) return;

    const gallery = baseline.image_gallery?.length ? baseline.image_gallery : baseline.image_src ? [baseline.image_src] : [];
    const main = gallery[0];
    const thumbs =
      gallery.length > 1
        ? `<div class="gallery-thumbs">${gallery
            .map(
              (src, i) =>
                `<button type="button" class="gallery-thumb${i === 0 ? " active" : ""}" data-src="${src}" aria-label="Photo ${i + 1}"><img src="${src}" alt=""></button>`
            )
            .join("")}</div>`
        : "";
    media.innerHTML = `<div class="bike-thumb">${
      main
        ? `<img class="bike-main-img" src="${main}" alt="${baseline.brand} ${baseline.model}">`
        : `<span class="placeholder-icon">🚲</span>`
    }</div>${thumbs}`;

    const kind = baseline.is_baseline || baseline.motor_w === 0 ? "Pedal" : `Class ${baseline.e_bike_class || "?"}`;
    const link = baseline.url || baseline.best_buy_url;
    const bat = formatBattery(baseline);
    const batLine = bat.has_battery ? ` · ${bat.range_label}` : "";
    const effLine = bat.efficiency_label && bat.efficiency_label !== "—" ? ` · ${bat.efficiency_label}` : "";
    details.innerHTML = `
      <p><strong>${baseline.brand} ${baseline.model}</strong> · ${formatMoney(bikePrice(baseline))} · ${kind} · ${baseline.max_speed_mph || "?"} mph max · ${brakeHtml(baseline)}${batLine}${effLine}</p>
      <p>All “vs baseline” multipliers compare to this bike.${link ? ` <a href="${link}" target="_blank" rel="noopener">Product page →</a>` : ""}</p>
    `;

    const options = Object.values(bikeMap)
      .sort((a, b) => `${a.brand} ${a.model}`.localeCompare(`${b.brand} ${b.model}`))
      .map((b) => `<option value="${b.id}"${b.id === baselineId ? " selected" : ""}>${b.brand} ${b.model}</option>`)
      .join("");
    select.innerHTML = options;
  }

  function updateHiddenUi() {
    const count = hiddenIds.length;
    const btn = document.getElementById("btnRestoreHidden");
    const span = document.getElementById("hiddenCount");
    if (span) span.textContent = String(count);
    if (btn) btn.hidden = count === 0;
  }

  function hideBike(id) {
    if (!hiddenIds.includes(id)) hiddenIds.push(id);
    compareIds = compareIds.filter((x) => x !== id);
    saveHidden();
    if (currentDetailId === id) closeDetail();
    applyCardFilters();
    applyTableFilters();
    updateComparePanel();
  }

  function restoreBike(id) {
    hiddenIds = hiddenIds.filter((x) => x !== id);
    saveHidden();
    applyCardFilters();
    applyTableFilters();
  }

  function setBaseline(id, fromUser = true) {
    if (!bikeMap[id]) return;
    baselineId = id;
    saveBaseline();
    if (fromUser) enableBaselineHighlight();
    applyBaselineToAll();
    renderBaselinePanel();
    applyCardFilters();
    updateComparePanel();
    if (currentDetailId === id) renderDetailPage(id);
    else if (currentDetailId) renderDetailPage(currentDetailId);
  }

  function productGallery(bike) {
    return bike.image_gallery?.length ? bike.image_gallery : bike.image_src ? [bike.image_src] : [];
  }

  function galleryHtml(gallery, alt, mainClass = "bike-main-img") {
    const main = gallery[0];
    const thumbs =
      gallery.length > 1
        ? `<div class="gallery-thumbs" role="group" aria-label="${alt} photos">${gallery
            .map(
              (src, i) =>
                `<button type="button" class="gallery-thumb${i === 0 ? " active" : ""}" data-src="${src}" aria-label="Photo ${i + 1}"><img src="${src}" alt=""></button>`
            )
            .join("")}</div>`
        : "";
    return `<div class="bike-thumb detail-hero-thumb">${
      main ? `<img class="${mainClass}" src="${main}" alt="${alt}">` : `<span class="placeholder-icon">🚲</span>`
    }</div>${thumbs}`;
  }

  function buyLinksHtml(bike) {
    const best = bike.best_buy_url
      ? `<a class="buy-best" href="${bike.best_buy_url}" target="_blank" rel="noopener" title="${bike.best_buy_delivery || ""}">
          ★ ${bike.best_buy_platform || "Buy"} ${formatMoney(bike.landed_price_usd || bike.price)}
        </a>`
      : "";
    const alts = (bike.price_sources || [])
      .filter((src) => src.url && src.url !== bike.best_buy_url)
      .map(
        (src) =>
          `<a class="buy-alt" href="${src.url}" target="_blank" rel="noopener" title="${src.delivery_note || ""}">
            ${src.platform_label} $${src.landed_usd != null ? Math.round(src.landed_usd) : "—"}${src.is_search_url ? " ↗" : ""}
          </a>`
      )
      .join("");
    return best || alts ? `<div class="buy-links">${best}${alts}</div>` : "";
  }

  function vehicleMarkHtml(bike) {
    const isScooter = bike.vehicle_type === "scooter";
    return `<span class="vehicle-mark ${isScooter ? "vehicle-mark--scooter" : "vehicle-mark--bike"}" title="${isScooter ? "E-scooter" : "E-bike"}" aria-hidden="true">${isScooter ? "🛴" : "🚲"}</span>`;
  }

  function compactCardInner(bike) {
    const gallery = productGallery(bike);
    const isScooter = bike.vehicle_type === "scooter";
    const placeholder = isScooter ? "🛴" : "🚲";
    const img = gallery[0]
      ? `<img class="bike-main-img" src="${gallery[0]}" alt="${bike.brand} ${bike.model}" loading="lazy">`
      : `<span class="placeholder-icon">${placeholder}</span>`;
    const customBadge = bike.id?.startsWith("custom-") ? ` <span class="badge info">Custom</span>` : "";
    const legalBadge = bike.legal_for_age !== false
      ? `<span class="badge ok">${bike.vehicle_type === "scooter" ? "OK" : "Legal"}</span>`
      : `<span class="badge danger">✗</span>`;
    const smartBadge =
      bike.feature_display?.is_smart || (bike.features && formatFeatureDisplay(bike.features).is_smart)
        ? `<span class="badge luxury">Smart</span>`
        : "";
    return `
      <button type="button" class="card-open" data-id="${bike.id}" aria-label="View ${bike.brand} ${bike.model} details">
        <div class="bike-media"><div class="bike-thumb bike-thumb-compact">${vehicleMarkHtml(bike)}${img}</div></div>
        <h3>${bike.brand} ${bike.model}${customBadge}</h3>
        <div class="price-big">${formatMoney(bikePrice(bike))}</div>
        <div class="badges badges-compact">
          <span class="badge ok">Safety ${bike.safety_score}</span>
          ${legalBadge}
          ${smartBadge}
        </div>
      </button>
      <div class="card-actions card-actions-compact">
        <button type="button" class="btn-compare" data-id="${bike.id}">+ Compare</button>
        <button type="button" class="btn-hide" data-id="${bike.id}">Hide</button>
      </div>`;
  }

  function renderDetailPage(id) {
    const bike = bikeMap[id];
    if (!bike) return;
    const baseline = getBaseline();
    const vs = bike.vs_baseline;
    const gallery = productGallery(bike);
    const kind =
      bike.is_baseline || bike.motor_w === 0
        ? "Pedal"
        : bike.vehicle_type === "scooter"
          ? "E-scooter"
          : `Class ${bike.e_bike_class || "?"}`;

    document.getElementById("detailGallery").innerHTML = galleryHtml(
      gallery,
      `${bike.brand} ${bike.model}`,
      "bike-main-img detail-hero-img"
    );
    document.getElementById("detailBreadcrumb").textContent = `${bike.brand} ${bike.model}`;

    const recBadge = bike.friend_recommended ? `<span class="badge info">Recommended</span>` : "";
    const smartScore = bike.feature_display?.luxury_score || bike.luxury_score;
    const smartBadge = smartScore ? `<span class="badge luxury">Smart ${smartScore}</span>` : "";
    const legalBadge =
      bike.legal_for_age !== false
        ? `<span class="badge ok">${bike.vehicle_type === "scooter" ? "OK w/ rules" : "Legal"}</span>`
        : `<span class="badge danger">Not legal age 12</span>`;

    const vsBlock =
      vs && bike.id !== baseline.id
        ? `<div class="detail-vs-baseline">
            <span class="detail-vs-label">vs ${baseline.brand} ${baseline.model}</span>
            <strong>${vs.price_multiplier}×</strong> price ·
            <strong>${vs.speed_delta_mph >= 0 ? "+" : ""}${vs.speed_delta_mph} mph</strong>
          </div>`
        : "";

    const compareOn = compareIds.includes(id);
    document.getElementById("detailBuyBox").innerHTML = `
      <h1 class="detail-title">${bike.brand} ${bike.model}</h1>
      <div class="detail-price">${formatMoney(bikePrice(bike))} <span class="price-note">landed</span></div>
      ${buyLinksHtml(bike)}
      <div class="badges detail-badges">
        <span class="badge ok">Safety ${bike.safety_score}</span>
        ${smartBadge}
        ${legalBadge}
        ${recBadge}
      </div>
      <p class="detail-meta">${bike.tier_label || tierLabels[bike.tier] || bike.tier} · ${kind} · ${bike.max_speed_mph || "?"} mph · ${brakeHtml(bike)}</p>
      ${vsBlock}
      <div class="detail-actions">
        <button type="button" class="btn-compare detail-action-btn${compareOn ? " active" : ""}" data-id="${bike.id}">${compareOn ? "✓ Comparing" : "+ Compare"}</button>
        <button type="button" class="btn-baseline detail-action-btn" data-id="${bike.id}">Set baseline</button>
        <button type="button" class="btn-hide detail-action-btn" data-id="${bike.id}">Hide</button>
      </div>`;

    const checklist = (bike.safety_checklist || buildChecklist(bike))
      .map((i) => `<li class="${i.ok ? "ok" : "miss"}">${i.label}</li>`)
      .join("");
    const colors = (bike.colors || [])
      .map((c) => `<span class="color-chip"><span class="dot ${c.family}"></span>${c.name}</span>`)
      .join("");
    const legalIssues = (bike.legal_issues || [])
      .map((issue) => `<li>${issue}</li>`)
      .join("");

    document.getElementById("detailSpecs").innerHTML = [
      detailSpecBlock("Safety equipment", `<ul class="checklist checklist-compact">${checklist}</ul>`),
      detailSpecBlock("Battery & range", batteryBlockHtml(bike, { detail: true })),
      detailSpecBlock("Smart & connectivity", featureBlockHtml(bike, { detail: true }), {
        className: "detail-spec-block--smart",
      }),
      colors ? detailSpecBlock("Available colors", `<div class="color-chips color-chips--detail">${colors}</div>`) : "",
      legalIssues ? detailSpecBlock("Legal notes", `<ul class="detail-legal-list">${legalIssues}</ul>`) : "",
    ]
      .filter(Boolean)
      .join("");

    const faqEl = document.getElementById("detailFaq");
    const faqItems = buildProductFaq(bike);
    if (faqEl) {
      const html = faqSectionHtml(faqItems, { productId: bike.id });
      faqEl.innerHTML = html;
      faqEl.hidden = !html;
    }

    const similar = Object.values(bikeMap)
      .filter((b) => b.id !== id && b.tier === bike.tier && !hiddenIds.includes(b.id))
      .slice(0, 4);
    const similarEl = document.getElementById("detailSimilar");
    if (similar.length) {
      similarEl.innerHTML = `
        <h3 class="detail-similar-title">More in ${bike.tier_label || tierLabels[bike.tier] || bike.tier}</h3>
        <div class="detail-similar-grid">${similar
          .map(
            (b) => `
          <button type="button" class="detail-similar-card" data-id="${b.id}">
            ${productGallery(b)[0] ? `<img src="${productGallery(b)[0]}" alt="">` : `<span class="placeholder-icon">${b.vehicle_type === "scooter" ? "🛴" : "🚲"}</span>`}
            <span>${b.brand} ${b.model}</span>
            <span class="detail-similar-price">${formatMoney(bikePrice(b))}</span>
          </button>`
          )
          .join("")}</div>`;
      similarEl.hidden = false;
    } else {
      similarEl.innerHTML = "";
      similarEl.hidden = true;
    }

    document.title = `${bike.brand} ${bike.model} · Surf City HB`;
  }

  function parseRoute() {
    const hash = location.hash.replace(/^#/, "");
    const m = hash.match(/^\/?ride\/([^/?#]+)/);
    return m ? decodeURIComponent(m[1]) : null;
  }

  function showDetailView(id) {
    currentDetailId = id;
    browseView.hidden = true;
    detailView.hidden = false;
    renderDetailPage(id);
    if (chatDrawerOpen) renderChatSuggestions();
    window.scrollTo(0, 0);
  }

  function openDetail(id) {
    if (!bikeMap[id]) {
      closeDetail();
      return;
    }
    const target = `#/ride/${encodeURIComponent(id)}`;
    if (location.hash !== target) location.hash = target;
    else showDetailView(id);
  }

  function closeDetail(skipHash) {
    currentDetailId = null;
    if (!skipHash && location.hash.match(/#\/ride\//)) {
      history.replaceState(null, "", location.pathname + location.search);
    }
    browseView.hidden = false;
    detailView.hidden = true;
    document.title = PAGE_TITLE;
    window.scrollTo(0, 0);
  }

  function handleRoute() {
    const id = parseRoute();
    if (id && bikeMap[id]) showDetailView(id);
    else if (id) closeDetail(true);
    else if (currentDetailId) closeDetail(true);
  }

  function renderCharts() {
    const bikes = getVisibleBikesForCharts();
    renderScatterChart("chartSafetyPrice", bikes, (b) => bikePrice(b), (b) => b.safety_score, "Price", "Safety");
    renderTierChart("chartSafetyTier", bikes);
    renderChecklistChart("chartChecklist", bikes);
    renderScatterChart("chartSpeedSafety", bikes, (b) => b.max_speed_mph, (b) => b.safety_score, "Max mph", "Safety");
    const rangeEl = document.getElementById("chartRangePrice");
    if (rangeEl) {
      const withRange = bikes.filter((b) => b.battery_display?.range_miles || b.battery_range_miles_pas);
      renderScatterChart(
        "chartRangePrice",
        withRange,
        (b) => bikePrice(b),
        (b) => b.battery_display?.range_miles || b.battery_range_miles_pas,
        "Price",
        "PAS range (mi)"
      );
    }
    const effEl = document.getElementById("chartEfficiencyPrice");
    if (effEl) {
      const withEff = bikes.filter((b) => b.battery_display?.wh_per_mile_pas != null);
      renderScatterChart(
        "chartEfficiencyPrice",
        withEff,
        (b) => bikePrice(b),
        (b) => b.battery_display.wh_per_mile_pas,
        "Price",
        "Wh/mi PAS"
      );
    }
    renderEfficiencyTierChart("chartEfficiencyTier", bikes);
    const luxEl = document.getElementById("chartLuxuryPrice");
    if (luxEl) {
      const withLux = bikes.filter((b) => (b.feature_display?.luxury_score || b.luxury_score || 0) > 0);
      renderScatterChart(
        "chartLuxuryPrice",
        withLux,
        (b) => bikePrice(b),
        (b) => b.feature_display?.luxury_score || b.luxury_score || 0,
        "Price",
        "Smart score"
      );
    }
  }

  function renderEfficiencyTierChart(elId, bikes) {
    const el = document.getElementById(elId);
    if (!el) return;
    const tiers = ["budget", "value", "mid", "premium"];
    const data = tiers
      .map((t) => {
        const group = bikes.filter((b) => b.tier === t && b.battery_display?.wh_per_mile_pas != null);
        const avg = group.length
          ? group.reduce((s, b) => s + b.battery_display.wh_per_mile_pas, 0) / group.length
          : 0;
        return { tier: t, label: tierLabels[t] || t, avg, n: group.length };
      })
      .filter((d) => d.n > 0);
    if (!data.length) {
      el.innerHTML = "<p class='chart-empty'>No bikes match filters.</p>";
      return;
    }
    const max = Math.max(...data.map((d) => d.avg), 1);
    el.innerHTML = data
      .map(
        (d) => `
      <div class="bar-row">
        <span class="bar-label">${d.label}</span>
        <div class="bar-track"><div class="bar-fill bar-fill--eff" style="width:${(d.avg / max) * 100}%"></div></div>
        <span class="bar-val">${d.avg.toFixed(1)}</span>
      </div>`
      )
      .join("");
  }

  function renderScatterChart(elId, bikes, xFn, yFn, xLabel, yLabel) {
    const el = document.getElementById(elId);
    if (!el) return;
    if (!bikes.length) {
      el.innerHTML = "<p class='chart-empty'>No bikes match filters.</p>";
      return;
    }
    const W = 280;
    const H = 160;
    const pad = { t: 12, r: 12, b: 28, l: 36 };
    const xs = bikes.map(xFn);
    const ys = bikes.map(yFn);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    const scaleX = (v) => pad.l + ((v - minX) / (maxX - minX || 1)) * (W - pad.l - pad.r);
    const scaleY = (v) => H - pad.b - ((v - minY) / (maxY - minY || 1)) * (H - pad.t - pad.b);
    const dots = bikes
      .map((b) => {
        const cx = scaleX(xFn(b));
        const cy = scaleY(yFn(b));
        const title = `${b.brand} ${b.model}`;
        return `<circle cx="${cx}" cy="${cy}" r="5" class="chart-dot"><title>${title}</title></circle>`;
      })
      .join("");
    el.innerHTML = `
      <svg viewBox="0 0 ${W} ${H}" class="chart-svg" role="img" aria-label="${yLabel} vs ${xLabel}">
        <line x1="${pad.l}" y1="${H - pad.b}" x2="${W - pad.r}" y2="${H - pad.b}" class="chart-axis"/>
        <line x1="${pad.l}" y1="${pad.t}" x2="${pad.l}" y2="${H - pad.b}" class="chart-axis"/>
        <text x="${W / 2}" y="${H - 4}" class="chart-label" text-anchor="middle">${xLabel}</text>
        <text x="10" y="${H / 2}" class="chart-label" transform="rotate(-90 10 ${H / 2})">${yLabel}</text>
        ${dots}
      </svg>`;
  }

  function renderTierChart(elId, bikes) {
    const el = document.getElementById(elId);
    if (!el) return;
    const tiers = ["budget", "value", "mid", "premium"];
    const data = tiers.map((t) => {
      const group = bikes.filter((b) => b.tier === t);
      const avg = group.length ? group.reduce((s, b) => s + b.safety_score, 0) / group.length : 0;
      return { tier: t, label: tierLabels[t] || t, avg, n: group.length };
    }).filter((d) => d.n > 0);
    if (!data.length) {
      el.innerHTML = "<p class='chart-empty'>No bikes match filters.</p>";
      return;
    }
    const max = Math.max(...data.map((d) => d.avg), 1);
    el.innerHTML = data
      .map(
        (d) => `
      <div class="bar-row">
        <span class="bar-label">${d.label}</span>
        <div class="bar-track"><div class="bar-fill" style="width:${(d.avg / max) * 100}%"></div></div>
        <span class="bar-val">${Math.round(d.avg)}</span>
      </div>`
      )
      .join("");
  }

  function renderChecklistChart(elId, bikes) {
    const el = document.getElementById(elId);
    if (!el) return;
    if (!bikes.length) {
      el.innerHTML = "<p class='chart-empty'>No bikes match filters.</p>";
      return;
    }
    const keys = [
      { key: "brake_type", label: "Disc brakes" },
      { key: "front_light", label: "Front light" },
      { key: "rear_light", label: "Rear light" },
      { key: "ul_cert", label: "UL cert" },
    ];
    el.innerHTML = keys
      .map((k) => {
        const pass = bikes.filter((b) => (b.safety_checklist || []).find((i) => i.key === k.key)?.ok).length;
        const pct = Math.round((pass / bikes.length) * 100);
        return `
        <div class="bar-row">
          <span class="bar-label">${k.label}</span>
          <div class="bar-track"><div class="bar-fill bar-fill--ok" style="width:${pct}%"></div></div>
          <span class="bar-val">${pct}%</span>
        </div>`;
      })
      .join("");
  }

  function checklistKeys(bike) {
    return (bike.safety_checklist || []).map((i) => i.key);
  }

  function checklistCellText(item) {
    if (!item) return "—";
    if (item.key === "brake_type") return item.label;
    return yesNo(item.ok);
  }

  function renderCompareSlot(slotEl, bike) {
    if (!slotEl || !bike) return false;
    slotEl.className = "compare-slot";
    slotEl.dataset.id = bike.id;
    const gallery = bike.image_gallery?.length ? bike.image_gallery : bike.image_src ? [bike.image_src] : [];
    const mainImg = gallery[0];
    const img = mainImg
      ? `<img class="bike-main-img" src="${mainImg}" alt="">`
      : `<span style="font-size:2rem;display:block;text-align:center;padding:20px;">🚲</span>`;
    const buyLink = bike.best_buy_url
      ? `<a class="buy-best" href="${bike.best_buy_url}" target="_blank" rel="noopener">★ ${bike.best_buy_platform || "Buy"} ${formatMoney(bike.price)}</a>`
      : "";
    const legalBadge = bike.legal_for_age !== false
      ? '<span class="badge ok">Legal age 12</span>'
      : '<span class="badge danger">Illegal age 12</span>';
    const vs = bike.vs_baseline;
    slotEl.innerHTML = `
      <button type="button" class="compare-slot-remove" data-id="${bike.id}" aria-label="Remove ${bike.brand} ${bike.model} from compare">✕</button>
      <div class="thumb-wrap">${img}</div>
      <strong>${bike.brand} ${bike.model}</strong>
      <div>${formatMoney(bike.price)} · Safety <strong>${bike.safety_score}</strong>/100</div>
      <div>${bike.vehicle_type === "scooter" ? "Scooter" : `Class ${bike.e_bike_class || "?"}`} · ${bike.max_speed_mph} mph max</div>
      <div>${legalBadge} · ${brakeHtml(bike)}${bike.luxury_score ? ` · Smart <strong>${bike.luxury_score}</strong>` : ""}</div>
      <div class="compare-battery">${batteryHtml(bike)}</div>
      ${vs ? `<div>vs baseline: <strong>${vs.price_multiplier}×</strong> · ${vs.speed_delta_mph >= 0 ? "+" : ""}${vs.speed_delta_mph} mph</div>` : ""}
      <div class="buy-links">${buyLink}</div>
    `;
    return true;
  }

  function openCompareDrawer() {
    if (!compareDrawer || compareIds.length === 0) return;
    compareDrawerOpen = true;
    compareDrawer.hidden = false;
    compareDrawer.setAttribute("aria-hidden", "false");
    document.body.classList.add("compare-drawer-open");
  }

  function closeCompareDrawer() {
    if (!compareDrawer) return;
    compareDrawerOpen = false;
    compareDrawer.hidden = true;
    compareDrawer.setAttribute("aria-hidden", "true");
    document.body.classList.remove("compare-drawer-open");
  }

  function toggleCompare(id) {
    const wasIncluded = compareIds.includes(id);
    if (wasIncluded) {
      compareIds = compareIds.filter((x) => x !== id);
      if (compareIds.length === 0) closeCompareDrawer();
    } else if (compareIds.length < MAX_COMPARE) {
      compareIds.push(id);
      openCompareDrawer();
    } else {
      compareIds.shift();
      compareIds.push(id);
      openCompareDrawer();
    }
    updateComparePanel();
    if (currentDetailId === id) renderDetailPage(id);
  }

  function renderSafetyMatrix(selected) {
    const matrixEl = document.getElementById("compareMatrix");
    const wrapEl = document.getElementById("compareMatrixWrap");
    if (!matrixEl || !wrapEl || selected.length < 2) {
      if (wrapEl) wrapEl.hidden = true;
      return;
    }
    wrapEl.hidden = false;
    const baseline = getBaseline();
    const allKeys = [...new Set(selected.flatMap(checklistKeys))];
    const headers = selected.map((b) => `<th>${b.brand} ${b.model}</th>`).join("");
    const checklistRows = allKeys.map((key) => {
      const rowLabel = (selected[0].safety_checklist || []).find((i) => i.key === key)?.row_label || key;
      const cells = selected.map((b) => {
        const item = (b.safety_checklist || []).find((i) => i.key === key);
        const cls = item?.ok ? "cell-best" : "cell-worst";
        return `<td class="${cls}">${checklistCellText(item)}</td>`;
      });
      return `<tr><th class="row-label">${rowLabel}</th>${cells.join("")}</tr>`;
    });

    const metricRows = [
      { label: "Safety score", values: selected.map((b) => b.safety_score), higherBetter: true, fmt: (v) => `<strong>${v}</strong>/100` },
      { label: "Landed price", values: selected.map((b) => b.price), higherBetter: false, fmt: (v) => formatMoney(v) },
      { label: `vs ${baseline.brand} ${baseline.model}`, values: selected.map((b) => b.vs_baseline?.price_multiplier), higherBetter: false, fmt: (v) => (v ? `${v}×` : "—") },
      { label: "Speed delta vs baseline", values: selected.map((b) => b.vs_baseline?.speed_delta_mph), higherBetter: null, fmt: (v) => (v != null ? `${v >= 0 ? "+" : ""}${v} mph` : "—") },
      { label: "Max speed", values: selected.map((b) => b.max_speed_mph), higherBetter: null, fmt: (v) => `${v} mph` },
      {
        label: "PAS range",
        values: selected.map((b) => b.battery_display?.range_miles ?? b.battery_range_miles_pas),
        higherBetter: true,
        fmt: (v, b) => formatBattery(b).range_label,
        bikes: selected,
      },
      {
        label: "Battery",
        values: selected.map((b) => b.battery_display?.battery_wh ?? b.battery_wh),
        higherBetter: true,
        fmt: (v, b) => formatBattery(b).capacity_label,
        bikes: selected,
      },
      {
        label: "Charging",
        values: selected.map((b) => 0),
        higherBetter: null,
        fmt: (v, b) => formatBattery(b).charge_label,
        bikes: selected,
      },
      {
        label: "Energy efficiency (PAS)",
        values: selected.map((b) => b.battery_display?.wh_per_mile_pas),
        higherBetter: false,
        fmt: (v, b) => {
          const bat = formatBattery(b);
          if (v == null) return "—";
          return `<span class="efficiency-tag efficiency-${bat.efficiency_rating || "unknown"}">${bat.efficiency_label}</span>`;
        },
        bikes: selected,
      },
      {
        label: "Smart / luxury score",
        values: selected.map((b) => b.feature_display?.luxury_score || b.luxury_score || 0),
        higherBetter: true,
        fmt: (v) => (v ? `<strong>${v}</strong>/100` : "—"),
      },
      { label: "Brakes", values: selected.map((b) => b.brake_type), higherBetter: null, fmt: (_, b) => brakeHtml(b), bikes: selected },
    ];

    const featureKeys = [...new Set(selected.flatMap((b) => (b.feature_checklist || []).map((i) => i.key)))];
    const featureRows = featureKeys.map((key) => {
      const rowLabel = (selected.find((b) => (b.feature_checklist || []).find((i) => i.key === key))?.feature_checklist || []).find((i) => i.key === key)?.label || key;
      const cells = selected.map((b) => {
        const item = (b.feature_checklist || []).find((i) => i.key === key);
        if (!item) return "<td>—</td>";
        const cls = item.ok ? "cell-best" : "cell-worst";
        return `<td class="${cls}">${item.ok ? "✓" : "✗"}</td>`;
      });
      return `<tr><th class="row-label">${rowLabel}</th>${cells.join("")}</tr>`;
    });

    const metricHtml = metricRows.map((row) => {
      const nums = row.values.filter((v) => typeof v === "number" && !Number.isNaN(v));
      let best = null;
      let worst = null;
      if (row.higherBetter === true && nums.length) {
        best = Math.max(...nums);
        worst = Math.min(...nums);
      } else if (row.higherBetter === false && nums.length) {
        best = Math.min(...nums);
        worst = Math.max(...nums);
      }
      const cells = row.values.map((v, i) => {
        let cls = "";
        if (row.higherBetter !== null && typeof v === "number" && !Number.isNaN(v)) {
          if (v === best && best !== worst) cls = "cell-best";
          else if (v === worst && best !== worst) cls = "cell-worst";
        }
        const content = row.bikes ? row.fmt(v, row.bikes[i]) : row.fmt(v);
        return `<td class="${cls}">${content}</td>`;
      });
      return `<tr><th class="row-label">${row.label}</th>${cells.join("")}</tr>`;
    });

    matrixEl.innerHTML = `
      <table class="compare-matrix">
        <thead><tr><th>Safety factor</th>${headers}</tr></thead>
        <tbody>${metricHtml.join("")}${featureRows.join("")}${checklistRows.join("")}</tbody>
      </table>`;
  }

  function updateComparePanel() {
    const slotsContainer = document.getElementById("compareSlots");
    const hint = document.getElementById("compareDrawerHint");
    const selected = compareIds.map((id) => bikeMap[id]).filter(Boolean);

    if (slotsContainer) {
      slotsContainer.innerHTML = "";
      if (selected.length === 0) {
        slotsContainer.innerHTML = `<p class="compare-empty-msg">No rides selected yet.</p>`;
      } else {
        selected.forEach((bike) => {
          const slot = document.createElement("div");
          if (!renderCompareSlot(slot, bike)) return;
          slotsContainer.appendChild(slot);
        });
      }
    }

    if (hint) {
      hint.hidden = selected.length >= MAX_COMPARE;
      hint.textContent =
        selected.length === 0
          ? "Add rides with + Compare on any card or detail page (up to 3)."
          : selected.length < MAX_COMPARE
            ? `${selected.length} of ${MAX_COMPARE} — add another from browse, or open the safety matrix with 2+.`
            : "";
    }

    const hasCompare = compareIds.length > 0;
    if (compareFab) compareFab.hidden = !hasCompare;
    if (compareFabCount) compareFabCount.textContent = String(compareIds.length);
    if (heroCompareLink) {
      heroCompareLink.hidden = !hasCompare;
      heroCompareLink.textContent = `Compare (${compareIds.length})`;
    }

    cards().forEach((card) => {
      const btn = card.querySelector(".btn-compare");
      const id = card.dataset.id;
      const on = compareIds.includes(id);
      card.classList.toggle("selected", on);
      if (btn) {
        btn.classList.toggle("active", on);
        btn.textContent = on ? "✓ Comparing" : "+ Compare";
      }
    });

    const diffEl = document.getElementById("compareDiff");
    const matrixWrap = document.getElementById("compareMatrixWrap");
    const baseline = getBaseline();
    if (selected.length >= 2 && diffEl) {
      diffEl.hidden = false;
      const prices = selected.map((b) => b.price);
      const safest = selected.reduce((a, b) => (a.safety_score > b.safety_score ? a : b));
      const cheapest = selected.reduce((a, b) => (a.price < b.price ? a : b));
      diffEl.innerHTML = `
        <strong>Safety-first read:</strong>
        Highest safety: <em>${safest.brand} ${safest.model}</em> (${safest.safety_score}/100).
        Cheapest: <em>${cheapest.brand} ${cheapest.model}</em> (${formatMoney(cheapest.price)}).
        Baseline: <em>${baseline.brand} ${baseline.model}</em> (${formatMoney(bikePrice(baseline))}).
      `;
      renderSafetyMatrix(selected);
    } else {
      if (diffEl) diffEl.hidden = true;
      if (matrixWrap) matrixWrap.hidden = true;
    }
  }

  function appendCustomBikeCard(bike) {
    if (!cardGrid) return;
    const article = document.createElement("article");
    article.className = "bike-card bike-card-compact custom-bike";
    article.dataset.id = bike.id;
    article.dataset.tier = bike.tier || "other";
    article.dataset.price = bike.price;
    article.dataset.legal = bike.legal_for_age !== false ? "yes" : "no";
    article.dataset.colors = (bike.colors || []).map((c) => c.family).join(",");
    article.dataset.class = bike.vehicle_type === "scooter" ? "scooter" : bike.e_bike_class || "";
    article.dataset.vehicle = bike.vehicle_type || "ebike";
    article.dataset.speed = bike.max_speed_mph;
    article.dataset.efficiency = bike.battery_display?.wh_per_mile_pas ?? "";
    article.dataset.luxury = bike.luxury_score ?? "";
    article.dataset.smart = bike.feature_display?.is_smart ? "yes" : "no";
    article.innerHTML = compactCardInner(bike);
    cardGrid.appendChild(article);
  }

  async function fetchProductHints(url) {
    const status = document.getElementById("addBikeStatus");
    status.textContent = "Fetching…";
    try {
      const proxy = `https://api.allorigins.win/raw?url=${encodeURIComponent(url)}`;
      const resp = await fetch(proxy);
      if (!resp.ok) throw new Error("Fetch failed");
      const html = await resp.text();
      const title = html.match(/<meta[^>]+property=["']og:title["'][^>]+content=["']([^"']+)/i)?.[1]
        || html.match(/<title>([^<]+)/i)?.[1]?.trim();
      const image = html.match(/<meta[^>]+property=["']og:image["'][^>]+content=["']([^"']+)/i)?.[1];
      let price = null;
      const ld = html.match(/<script[^>]+type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/i);
      if (ld) {
        try {
          const data = JSON.parse(ld[1]);
          const items = Array.isArray(data) ? data : [data];
          for (const item of items) {
            if (item["@type"] === "Product") {
              const offers = item.offers;
              const offer = Array.isArray(offers) ? offers[0] : offers;
              price = parseFloat(offer?.price || offer?.lowPrice);
              break;
            }
          }
        } catch (_) {}
      }
      if (title) {
        const parts = title.split(/[-–|]/).map((s) => s.trim());
        document.getElementById("addBikeBrand").value = parts[0] || "";
        document.getElementById("addBikeModel").value = parts.slice(1).join(" ") || parts[0] || "";
      }
      if (price) document.getElementById("addBikePrice").value = Math.round(price);
      status.textContent = title ? `Found: ${title}` : "Could not parse title — fill in manually.";
      return { title, image, price };
    } catch (e) {
      status.textContent = "Fetch blocked — enter details manually.";
      return {};
    }
  }

  function openRestoreModal() {
    const list = document.getElementById("hiddenBikeList");
    const modal = document.getElementById("restoreModal");
    list.innerHTML = hiddenIds
      .map((id) => {
        const b = bikeMap[id];
        const label = b ? `${b.brand} ${b.model}` : id;
        return `<li><span>${label}</span> <button type="button" class="btn-ghost btn-restore-one" data-id="${id}">Restore</button></li>`;
      })
      .join("");
    modal.showModal();
  }

  function resetPreferences() {
    if (!confirm("Reset hidden bikes, custom bikes, and baseline choice?")) return;
    hiddenIds = [];
    customBikes = [];
    baselineId = config.defaultBaselineId;
    baselineHighlightEnabled = false;
    localStorage.removeItem(STORAGE.hidden);
    localStorage.removeItem(STORAGE.custom);
    localStorage.removeItem(STORAGE.baseline);
    localStorage.removeItem(STORAGE.baselineHighlight);
    document.querySelectorAll(".custom-bike").forEach((el) => el.remove());
    bikeMap = getCatalogMap();
    applyBaselineToAll();
    renderBaselinePanel();
    applyCardFilters();
    applyTableFilters();
    updateComparePanel();
    if (currentDetailId) renderDetailPage(currentDetailId);
  }

  // Event wiring
  tierTabs?.addEventListener("click", (e) => {
    const tab = e.target.closest(".tier-tab");
    if (!tab) return;
    document.querySelectorAll(".tier-tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    applyCardFilters();
  });

  [colorFilter, legalFilter, priceFilter, speedFilter, efficiencyFilter, vehicleFilter, smartFilter].forEach((el) =>
    el?.addEventListener("change", applyCardFilters)
  );
  [tableTierFilter, tableClassFilter, tableLegalFilter, tableColorFilter].forEach((el) =>
    el?.addEventListener("change", applyTableFilters)
  );

  document.getElementById("baselineSelect")?.addEventListener("change", (e) => setBaseline(e.target.value, true));

  document.getElementById("btnBaselineExpand")?.addEventListener("click", () => {
    const panel = document.getElementById("baselineExpanded");
    const btn = document.getElementById("btnBaselineExpand");
    if (!panel || !btn) return;
    const open = panel.hidden;
    panel.hidden = !open;
    btn.setAttribute("aria-expanded", open ? "true" : "false");
    btn.textContent = open ? "Hide details" : "Show details";
  });

  document.getElementById("btnDetailBack")?.addEventListener("click", () => closeDetail());
  window.addEventListener("hashchange", handleRoute);

  document.getElementById("btnCompareFab")?.addEventListener("click", openCompareDrawer);
  document.getElementById("btnCompareClose")?.addEventListener("click", closeCompareDrawer);
  document.getElementById("compareDrawerBackdrop")?.addEventListener("click", closeCompareDrawer);
  document.getElementById("btnChatFab")?.addEventListener("click", () => openChatDrawer());
  document.getElementById("btnChatClose")?.addEventListener("click", closeChatDrawer);
  document.getElementById("chatDrawerBackdrop")?.addEventListener("click", closeChatDrawer);
  document.getElementById("chatForm")?.addEventListener("submit", (e) => {
    e.preventDefault();
    submitChat();
  });
  heroCompareLink?.addEventListener("click", (e) => {
    e.preventDefault();
    openCompareDrawer();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    if (chatDrawerOpen) closeChatDrawer();
    else if (compareDrawerOpen) closeCompareDrawer();
  });

  document.addEventListener("click", (e) => {
    const cardOpen = e.target.closest(".card-open");
    if (cardOpen?.dataset.id) {
      openDetail(cardOpen.dataset.id);
      return;
    }
    const similarCard = e.target.closest(".detail-similar-card");
    if (similarCard?.dataset.id) {
      openDetail(similarCard.dataset.id);
      return;
    }
    const tableRow = e.target.closest("#compareTable tbody tr[data-id]");
    if (tableRow?.dataset.id && !e.target.closest("a")) {
      openDetail(tableRow.dataset.id);
      return;
    }
    const thumb = e.target.closest(".gallery-thumb");
    if (thumb) {
      e.preventDefault();
      const media = thumb.closest(".bike-media, .detail-gallery");
      const main = media?.querySelector(".bike-main-img, .detail-hero-img");
      if (main && thumb.dataset.src) {
        main.src = thumb.dataset.src;
        media.querySelectorAll(".gallery-thumb").forEach((t) => t.classList.toggle("active", t === thumb));
      }
      return;
    }
    const hideBtn = e.target.closest(".btn-hide");
    if (hideBtn) {
      hideBike(hideBtn.dataset.id);
      return;
    }
    const baseBtn = e.target.closest(".btn-baseline");
    if (baseBtn) {
      setBaseline(baseBtn.dataset.id);
      return;
    }
    const removeCompare = e.target.closest(".compare-slot-remove");
    if (removeCompare?.dataset.id) {
      toggleCompare(removeCompare.dataset.id);
      return;
    }
    const compareBtn = e.target.closest(".btn-compare");
    if (compareBtn?.dataset.id) {
      toggleCompare(compareBtn.dataset.id);
      return;
    }
    const chatChip = e.target.closest(".chat-chip");
    if (chatChip?.dataset.chatSuggest) {
      submitChat(chatChip.dataset.chatSuggest);
      return;
    }
    const specToggle = e.target.closest(".btn-spec-toggle");
    if (specToggle) {
      const wrap = specToggle.closest(".feature-detail-collapsible");
      if (!wrap) return;
      const expanding = wrap.classList.contains("is-collapsed");
      wrap.classList.toggle("is-collapsed", !expanding);
      wrap.classList.toggle("is-expanded", expanding);
      const full = wrap.querySelector(".feature-detail-full");
      if (full) full.hidden = !expanding;
      const count = wrap.dataset.featureCount || "";
      specToggle.setAttribute("aria-expanded", expanding ? "true" : "false");
      specToggle.textContent = expanding
        ? "Show less"
        : `Show all features (${count})`;
      return;
    }
    const restoreOne = e.target.closest(".btn-restore-one");
    if (restoreOne) {
      restoreBike(restoreOne.dataset.id);
      openRestoreModal();
    }
  });

  document.getElementById("btnAddBike")?.addEventListener("click", () => {
    document.getElementById("addBikeStatus").textContent = "";
    document.getElementById("addBikeModal").showModal();
  });
  document.getElementById("btnCancelAdd")?.addEventListener("click", () => document.getElementById("addBikeModal").close());
  document.getElementById("btnFetchUrl")?.addEventListener("click", () => {
    const url = document.getElementById("addBikeUrl").value.trim();
    if (url) fetchProductHints(url);
  });
  document.getElementById("btnRestoreHidden")?.addEventListener("click", openRestoreModal);
  document.getElementById("btnRestoreAll")?.addEventListener("click", () => {
    hiddenIds = [];
    saveHidden();
    applyCardFilters();
    applyTableFilters();
    document.getElementById("restoreModal").close();
  });
  document.getElementById("btnResetPrefs")?.addEventListener("click", resetPreferences);

  document.getElementById("addBikeForm")?.addEventListener("submit", (e) => {
    e.preventDefault();
    const url = document.getElementById("addBikeUrl").value.trim();
    const id = `custom-${Date.now()}`;
    const rangePas = parseFloat(document.getElementById("addBikeRange").value);
    const ah = parseFloat(document.getElementById("addBikeAh").value);
    const voltage = parseFloat(document.getElementById("addBikeVoltage").value);
    const chargeHrs = parseFloat(document.getElementById("addBikeChargeHrs").value);
    const bike = enrichBike({
      id,
      brand: document.getElementById("addBikeBrand").value.trim(),
      model: document.getElementById("addBikeModel").value.trim(),
      price_usd: parseFloat(document.getElementById("addBikePrice").value),
      landed_price_usd: parseFloat(document.getElementById("addBikePrice").value),
      max_speed_mph: parseFloat(document.getElementById("addBikeSpeed").value),
      e_bike_class: parseInt(document.getElementById("addBikeClass").value, 10),
      brake_type: document.getElementById("addBikeBrake").value,
      battery_range_miles_pas: Number.isNaN(rangePas) ? null : rangePas,
      battery_capacity_ah: Number.isNaN(ah) ? null : ah,
      battery_voltage_v: Number.isNaN(voltage) ? null : voltage,
      battery_wh: !Number.isNaN(voltage) && !Number.isNaN(ah) ? Math.round(voltage * ah) : null,
      battery_charge_hours: Number.isNaN(chargeHrs) ? null : chargeHrs,
      battery_charge_method: document.getElementById("addBikeChargeMethod").value,
      lights: {
        front: document.getElementById("addBikeLightFront").checked,
        rear: document.getElementById("addBikeLightRear").checked,
      },
      ul_certified: document.getElementById("addBikeUl").checked,
      tier: "other",
      tier_label: "Custom",
      best_buy_url: url,
      legal_for_age: parseInt(document.getElementById("addBikeClass").value, 10) <= 2,
      colors: [],
    });
    bike.vs_baseline = compareToBaseline(bike, getBaseline());
    customBikes.push(bike);
    bikeMap[id] = bike;
    saveCustom();
    appendCustomBikeCard(bike);
    document.getElementById("addBikeModal").close();
    applyCardFilters();
    renderBaselinePanel();
  });

  const table = document.getElementById("compareTable");
  let sortCol = null;
  let sortDir = 1;
  table?.querySelectorAll("th[data-sort]").forEach((th) => {
    th.addEventListener("click", () => {
      const col = th.dataset.sort;
      const type = th.dataset.type;
      if (sortCol === col) sortDir *= -1;
      else {
        sortCol = col;
        sortDir = 1;
      }
      table.querySelectorAll("th").forEach((h) => h.classList.remove("sorted-asc", "sorted-desc"));
      th.classList.add(sortDir === 1 ? "sorted-asc" : "sorted-desc");
      const tbody = table.querySelector("tbody");
      const sorted = [...rows()].sort((a, b) => {
        let va = a.dataset[col] ?? a.querySelector(`td:nth-child(${th.cellIndex + 1})`)?.textContent;
        let vb = b.dataset[col] ?? b.querySelector(`td:nth-child(${th.cellIndex + 1})`)?.textContent;
        if (type === "number") {
          va = parseFloat(va) || 0;
          vb = parseFloat(vb) || 0;
          return (va - vb) * sortDir;
        }
        return String(va).localeCompare(String(vb)) * sortDir;
      });
      sorted.forEach((r) => tbody.appendChild(r));
    });
  });

  // Init
  customBikes.forEach((b) => {
    const enriched = enrichBike(b);
    bikeMap[b.id] = enriched;
    appendCustomBikeCard(enriched);
  });
  try {
    applyBaselineToAll();
    renderBaselinePanel();
    applyCardFilters();
    applyTableFilters();
    updateComparePanel();
    renderCharts();
    handleRoute();
  } catch (err) {
    console.error("E-bike comparison init failed:", err);
  }
})();