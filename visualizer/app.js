const DATA_URL = "data/election_demographics_bundle.json";
const DHS_URL = "data/dhs_geospatial_clusters_public.csv";

let bundle = null;
let dhsClusters = [];
let showDhsClusters = false;
let dhsColorMode = "urban_rural";
let selectedStateKey = null;
let selectedMetric = "flip_rate";

const numberFormat = new Intl.NumberFormat("en-IN");
const percentFields = new Set([
  "flip_rate",
  "alliance_flip_rate",
  "close_seat_rate_5pct",
  "avg_top2_margin_pct",
  "urban_pct",
  "rural_pct",
  "sc_pct",
  "st_pct",
  "literacy_rate",
  "male_literacy",
  "female_literacy",
  "child_0_6_pct",
  "worker_pct",
  "main_worker_pct",
  "marginal_worker_pct",
  "hindu_pct",
  "muslim_pct",
  "christian_pct",
  "sikh_pct",
  "buddhist_pct",
  "jain_pct",
  "youth_pct",
  "working_age_pct",
  "elderly_pct",
]);

const metricCards = [
  ["seats", "Seats"],
  ["seat_flips", "Seat flips"],
  ["flip_rate", "Flip rate"],
  ["avg_volatility_score", "Volatility"],
  ["population_total", "Population"],
  ["urban_pct", "Urban"],
  ["sc_pct", "SC"],
  ["st_pct", "ST"],
  ["literacy_rate", "Literacy"],
];

function el(id) {
  return document.getElementById(id);
}

function fieldLabel(field) {
  const found = bundle.fields.find((f) => f.field === field);
  return found ? found.label : field.replaceAll("_", " ");
}

function formatValue(value, field) {
  if (value === null || value === undefined || Number.isNaN(value)) return "NA";
  if (percentFields.has(field)) return `${Number(value).toFixed(1)}%`;
  if (field.includes("swing") || field.includes("change")) return Number(value).toFixed(2);
  if (Math.abs(Number(value)) >= 1000) return numberFormat.format(Math.round(Number(value)));
  if (Number.isInteger(Number(value))) return numberFormat.format(Number(value));
  return Number(value).toFixed(2);
}

function numericValues(rows, field) {
  return rows
    .map((row) => row[field])
    .filter((value) => value !== null && value !== undefined && Number.isFinite(Number(value)))
    .map(Number);
}

function colorFor(value, min, max) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return "#eef2ef";
  if (max === min) return "#9fd1c4";
  const t = Math.max(0, Math.min(1, (Number(value) - min) / (max - min)));
  const low = [233, 239, 233];
  const mid = [159, 209, 196];
  const high = [23, 107, 104];
  const left = t < 0.5 ? low : mid;
  const right = t < 0.5 ? mid : high;
  const local = t < 0.5 ? t * 2 : (t - 0.5) * 2;
  const rgb = left.map((v, i) => Math.round(v + (right[i] - v) * local));
  return `rgb(${rgb.join(",")})`;
}

function stateAbbr(state) {
  const words = state.replaceAll("&", "and").split(/\s+/).filter(Boolean);
  if (words.length === 1) return words[0].slice(0, 3).toUpperCase();
  return words.map((w) => w[0]).join("").slice(0, 4).toUpperCase();
}

function selectedState() {
  return bundle.states.find((state) => state.state_key === selectedStateKey) || bundle.states[0];
}

function initControls() {
  const metricSelect = el("metricSelect");
  const grouped = {};
  bundle.fields
    .filter((f) => f.table === "states")
    .forEach((field) => {
      grouped[field.group] = grouped[field.group] || [];
      grouped[field.group].push(field);
    });

  Object.entries(grouped).forEach(([group, fields]) => {
    const optGroup = document.createElement("optgroup");
    optGroup.label = group;
    fields.forEach((field) => {
      const option = document.createElement("option");
      option.value = field.field;
      option.textContent = field.label;
      optGroup.appendChild(option);
    });
    metricSelect.appendChild(optGroup);
  });
  metricSelect.value = selectedMetric;
  metricSelect.addEventListener("change", () => {
    selectedMetric = metricSelect.value;
    render();
  });

  const stateSelect = el("stateSelect");
  bundle.states
    .slice()
    .sort((a, b) => a.state.localeCompare(b.state))
    .forEach((state) => {
      const option = document.createElement("option");
      option.value = state.state_key;
      option.textContent = state.state;
      stateSelect.appendChild(option);
    });
  stateSelect.addEventListener("change", () => {
    selectedStateKey = stateSelect.value;
    render();
  });

  const districtSort = el("districtSort");
  ["population_total", "urban_pct", "sc_pct", "st_pct", "literacy_rate", "worker_pct"].forEach((field) => {
    const option = document.createElement("option");
    option.value = field;
    option.textContent = fieldLabel(field);
    districtSort.appendChild(option);
  });
  districtSort.addEventListener("change", renderDistricts);

  el("minSeats").addEventListener("input", renderParties);
  el("constituencyFilter").addEventListener("change", renderConstituencies);

  el("gridMode").addEventListener("click", () => setMapMode("grid"));
  el("tableMode").addEventListener("click", () => setMapMode("table"));

  el("showDhsClusters").addEventListener("change", (event) => {
    showDhsClusters = event.target.checked;
    renderDhsMap();
  });
  el("dhsColorMode").addEventListener("change", (event) => {
    dhsColorMode = event.target.value;
    renderDhsMap();
  });
}

function setMapMode(mode) {
  el("gridMode").classList.toggle("active", mode === "grid");
  el("tableMode").classList.toggle("active", mode === "table");
  el("mapGrid").classList.toggle("hidden", mode !== "grid");
  el("stateTableWrap").classList.toggle("hidden", mode !== "table");
}

function renderLegend() {
  const values = numericValues(bundle.states, selectedMetric);
  const min = values.length ? Math.min(...values) : 0;
  const max = values.length ? Math.max(...values) : 0;
  el("legend").innerHTML = `
    <div>${fieldLabel(selectedMetric)}</div>
    <div class="legend-ramp"></div>
    <div>${formatValue(min, selectedMetric)} to ${formatValue(max, selectedMetric)}</div>
  `;
}

function renderMap() {
  const values = numericValues(bundle.states, selectedMetric);
  const min = values.length ? Math.min(...values) : 0;
  const max = values.length ? Math.max(...values) : 0;
  const grid = el("mapGrid");
  grid.innerHTML = "";

  bundle.states.forEach((state) => {
    const tile = document.createElement("button");
    tile.type = "button";
    tile.className = "state-tile";
    tile.style.background = colorFor(state[selectedMetric], min, max);
    if (state.grid_row && state.grid_col) {
      tile.style.gridRow = state.grid_row;
      tile.style.gridColumn = state.grid_col;
    }
    if (state.state_key === selectedStateKey) tile.classList.add("selected");
    tile.title = `${state.state}: ${formatValue(state[selectedMetric], selectedMetric)}`;
    tile.innerHTML = `
      <span class="state-code">${stateAbbr(state.state)}</span>
      <span class="state-value">${formatValue(state[selectedMetric], selectedMetric)}</span>
    `;
    tile.addEventListener("click", () => {
      selectedStateKey = state.state_key;
      render();
    });
    grid.appendChild(tile);
  });

  renderTable(
    el("stateTableWrap"),
    bundle.states.slice().sort((a, b) => Number(b[selectedMetric] || -Infinity) - Number(a[selectedMetric] || -Infinity)),
    ["state", selectedMetric, "seats", "seat_flips", "avg_volatility_score", "urban_pct", "sc_pct", "st_pct", "literacy_rate"],
    60,
  );
}

function renderStateSummary() {
  const state = selectedState();
  el("stateSelect").value = state.state_key;
  el("selectedStateName").textContent = state.state;
  el("stateSummary").innerHTML = metricCards
    .map(([field, label]) => `
      <div class="metric-card">
        <div class="metric-label">${label}</div>
        <div class="metric-value">${formatValue(state[field], field)}</div>
      </div>
    `)
    .join("");

  const signals = [
    ["Leading party 2019", state.leading_party_2019],
    ["Leading party 2024", state.leading_party_2024],
    ["Leading alliance 2019", state.leading_alliance_2019],
    ["Leading alliance 2024", state.leading_alliance_2024],
    ["BJP seats", `${state.bjp_seats_2019} to ${state.bjp_seats_2024}`],
    ["INC seats", `${state.inc_seats_2019} to ${state.inc_seats_2024}`],
    ["Demography match", state.demography_match_status],
  ];
  el("electionSignals").innerHTML = signals
    .map(([label, value]) => `<div class="signal-row"><span>${label}</span><strong>${value ?? "NA"}</strong></div>`)
    .join("");
}

function renderCoverage() {
  const fields = bundle.fields
    .filter((f) => f.table === "states")
    .sort((a, b) => a.group.localeCompare(b.group) || a.label.localeCompare(b.label));
  el("coverageList").innerHTML = fields
    .map((field) => {
      const pct = field.total_rows ? Math.round((field.available_rows / field.total_rows) * 100) : 0;
      return `
        <div class="coverage-item">
          <div class="coverage-label"><span>${field.label}</span><span>${field.available_rows}/${field.total_rows}</span></div>
          <div class="coverage-bar"><div class="coverage-fill" style="width:${pct}%"></div></div>
        </div>
      `;
    })
    .join("");
}

function renderTable(container, rows, columns, limit = 50) {
  const visibleRows = rows.slice(0, limit);
  if (!visibleRows.length) {
    container.innerHTML = "<div class=\"empty\">No rows.</div>";
    return;
  }
  const head = columns.map((col) => `<th>${fieldLabel(col)}</th>`).join("");
  const body = visibleRows
    .map((row) => `
      <tr>
        ${columns.map((col) => `<td>${formatValue(row[col], col)}</td>`).join("")}
      </tr>
    `)
    .join("");
  container.innerHTML = `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

function renderDistricts() {
  const sortField = el("districtSort").value || "population_total";
  const rows = bundle.districts
    .filter((district) => district.state_key === selectedStateKey)
    .sort((a, b) => Number(b[sortField] || -Infinity) - Number(a[sortField] || -Infinity));
  renderTable(
    el("districtTable"),
    rows,
    ["district", "population_total", "urban_pct", "sc_pct", "st_pct", "literacy_rate", "female_literacy", "worker_pct"],
    80,
  );
}

function renderParties() {
  const minSeats = Number(el("minSeats").value || 0);
  const rows = bundle.state_party_swings
    .filter((row) => row.state_key === selectedStateKey)
    .filter((row) => Math.max(Number(row.seats_2019 || 0), Number(row.seats_2024 || 0)) >= minSeats)
    .sort((a, b) => Number(b.seats_2024 || 0) - Number(a.seats_2024 || 0) || Math.abs(Number(b.avg_swing || 0)) - Math.abs(Number(a.avg_swing || 0)));
  renderTable(
    el("partyTable"),
    rows,
    ["party_id", "alliance_2024", "seats_2019", "seats_2024", "seat_change", "avg_vote_share_2019", "avg_vote_share_2024", "avg_swing"],
    80,
  );
}

function renderConstituencies() {
  const mode = el("constituencyFilter").value;
  let rows = bundle.constituencies.filter((row) => row.state_key === selectedStateKey);
  if (mode === "flipped") rows = rows.filter((row) => row.seat_flipped === true || row.seat_flipped === "True");
  if (mode === "close") rows = rows.filter((row) => Number(row.top2_margin_pct) <= 5);
  rows = rows.sort((a, b) => Number(b.volatility_score || 0) - Number(a.volatility_score || 0));
  renderTable(
    el("constituencyTable"),
    rows,
    ["constituency", "party_2019", "party_2024", "seat_flipped", "top2_margin_pct", "avg_abs_swing", "effective_num_parties", "volatility_score"],
    120,
  );
}

function dhsColor(cluster) {
  if (dhsColorMode === "survey") {
    return cluster.survey === "NFHS-5 (2019-21)" ? "#234d7d" : "#b84a39";
  }
  return cluster.urban_rural === "urban" ? "#176b68" : "#8a6d3b";
}

function renderDhsMap() {
  const mapEl = el("dhsMap");
  const legendEl = el("dhsLegend");
  if (!showDhsClusters || !dhsClusters.length) {
    mapEl.classList.add("hidden");
    legendEl.classList.add("hidden");
    mapEl.innerHTML = "";
    legendEl.innerHTML = "";
    return;
  }

  mapEl.classList.remove("hidden");
  legendEl.classList.remove("hidden");

  const state = selectedState();
  const stateName = state?.state || "";
  const points = dhsClusters.filter((row) => {
    if (!stateName) return true;
    return String(row.state_or_region || "").toLowerCase().includes(stateName.split(" ")[0].toLowerCase());
  });
  const visible = points.length ? points : dhsClusters;

  const lats = visible.map((p) => Number(p.latitude)).filter(Number.isFinite);
  const lons = visible.map((p) => Number(p.longitude)).filter(Number.isFinite);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const minLon = Math.min(...lons);
  const maxLon = Math.max(...lons);
  const pad = 0.05;

  const project = (lat, lon) => {
    const x = ((lon - minLon) / (maxLon - minLon + pad)) * 100;
    const y = (1 - (lat - minLat) / (maxLat - minLat + pad)) * 100;
    return { x, y };
  };

  const dots = visible
    .map((cluster) => {
      const { x, y } = project(Number(cluster.latitude), Number(cluster.longitude));
      return `<circle cx="${x}%" cy="${y}%" r="2.2" fill="${dhsColor(cluster)}" opacity="0.75" data-cluster="${cluster.cluster_id}"></circle>`;
    })
    .join("");

  mapEl.innerHTML = `
    <svg viewBox="0 0 100 100" preserveAspectRatio="none" role="img" aria-label="DHS cluster scatter map">
      ${dots}
    </svg>
    <div id="dhsTooltip" class="dhs-tooltip hidden"></div>
  `;

  const legendItems = dhsColorMode === "survey"
    ? [["NFHS-5", "#234d7d"], ["Other rounds", "#b84a39"]]
    : [["Urban", "#176b68"], ["Rural", "#8a6d3b"]];
  legendEl.innerHTML = legendItems
    .map(([label, color]) => `
      <span class="dhs-legend-item">
        <span class="dhs-legend-swatch" style="background:${color}"></span>
        ${label}
      </span>
    `)
    .join("");

  const tooltip = el("dhsTooltip");
  mapEl.querySelectorAll("circle").forEach((node, index) => {
    node.addEventListener("mouseenter", () => {
      const cluster = visible[index];
      tooltip.classList.remove("hidden");
      tooltip.innerHTML = `
        <strong>${cluster.state_or_region || "NA"}</strong><br>
        Survey: ${cluster.survey || "NA"}<br>
        Urban/rural: ${cluster.urban_rural || "NA"}<br>
        District: ${cluster.district_if_available || "NA"}<br>
        Lat/lon (rounded): ${cluster.latitude}, ${cluster.longitude}<br>
        <em>Displaced GPS — not exact locations.</em>
      `;
    });
    node.addEventListener("mousemove", (event) => {
      const rect = mapEl.getBoundingClientRect();
      tooltip.style.left = `${event.clientX - rect.left + 8}px`;
      tooltip.style.top = `${event.clientY - rect.top + 8}px`;
    });
    node.addEventListener("mouseleave", () => tooltip.classList.add("hidden"));
  });
}

function render() {
  renderLegend();
  renderMap();
  renderStateSummary();
  renderCoverage();
  renderDistricts();
  renderParties();
  renderConstituencies();
  renderDhsMap();
}

async function loadDhsClusters() {
  try {
    const response = await fetch(DHS_URL);
    if (!response.ok) return [];
    const text = await response.text();
    const lines = text.trim().split("\n");
    if (lines.length < 2) return [];
    const headers = lines[0].split(",");
    return lines.slice(1).map((line) => {
      const values = line.split(",");
      return Object.fromEntries(headers.map((header, i) => [header, values[i]]));
    });
  } catch {
    return [];
  }
}

async function main() {
  const response = await fetch(DATA_URL);
  bundle = await response.json();
  dhsClusters = await loadDhsClusters();
  selectedStateKey = bundle.states.find((s) => s.state === "Uttar Pradesh")?.state_key || bundle.states[0].state_key;
  initControls();
  render();
}

main().catch((error) => {
  document.body.innerHTML = `<pre>Could not load visualizer data.\n${error.stack || error}</pre>`;
});
