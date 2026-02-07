# Discount Recommendation API Backend Integration Guide

This service exposes a small HTTP API that recommends an **item-level discount percent** based on:
- Current stock remaining (`amount_left`): This is the current stock in the inventory of the item
- Expected baseline demand in the remaining time window (`expected_demand_for_remaining`): This is the input from the demand prediction model
- Menu item (`item_id`)
- Aggressiveness knob: This is on a scale from 1 - 10
- window_hours: This is the number of hours you want the item to be sold by from the current time

---

## Base URL

- Local: `http://127.0.0.1:8000`

---

## Endpoints

### `GET /health`
Checks that the API is running **and** whether the model artifacts are loaded.

**Response**
- `200 OK` if the model is loaded
- `503 Service Unavailable` if the API is up but model artifacts are missing / failed to load

**Example**
```bash
curl http://127.0.0.1:8000/health
```

---

### `POST /discount`
Calls the trained model + decision logic to return a recommended discount.

**Content-Type:** `application/json`

#### Required JSON fields
- `amount_left` *(number)* — current stock remaining
- `expected_demand_for_remaining` *(number)* — expected demand in the remaining window at baseline
- `item_id` *(integer)* — item id

#### Optional JSON fields
- `num_items_targeted` *(integer, default: 1)*
- `now_ts_unix` *(integer, default: server time in seconds)*
- `window_end_ts_unix` *(integer)* — if provided, overrides `window_hours`
- `window_hours` *(number, default: 3.0)* — used if `window_end_ts_unix` not provided
- `pct_grid` *(array[number], default shown below)* — list of discount pcts (0..1)
- `baseline_pct` *(number, default: 0.0)*
- `place_id` *(integer)* — store / venue id
- `aggressiveness` *(number, default: 5.0)* — (0..10) tunes model-vs-rules weighting and coverage target
- `return_debug` *(boolean, default: false)* — include debug table for all pct candidates
- `debug_limit` *(integer, default: 200)* — max number of debug rows returned
- `reload` *(boolean, default: false)* — force reload artifacts from disk (admin/debug)

#### Example request (curl)
```bash
curl -X POST http://127.0.0.1:8000/discount \
  -H "Content-Type: application/json" \
  -d '{
    "amount_left": 20,
    "expected_demand_for_remaining": 18,
    "place_id": 59897,
    "item_id": 59932,
    "num_items_targeted": 1,
    "window_hours": 4.0,
    "pct_grid": [0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40],
    "baseline_pct": 0.0,
    "aggressiveness": 5.0,
    "return_debug": false
  }'
```

---

## Response format

### Success (HTTP 200)
```json
{
  "result": {
    "recommended_pct": 0.15,
    "status": "can_clear_inventory",
    "pred_units_per_hour": 3.2,
    "baseline_units_per_hour": 2.4,
    "multiplier_vs_baseline": 1.33,
    "adjusted_expected_for_remaining": 24.0,
    "amount_left": 20.0,
    "expected_demand_for_remaining": 18.0,
    "window_hours": 4.0,
    "coverage_factor": 0.98,
    "w_model": 0.74,
    "w_eq": 0.26,
    "place_id": 59897,
    "item_id": 59932,
    "campaign_segment": "item_discount",
    "num_items_targeted": 1,
    "aggressiveness": 5.0
  }
}
```

### Debug mode (`return_debug=true`)
When `return_debug=true`, you also get:
- `debug`: an array of per-grid candidate rows (up to `debug_limit`)

```json
{
  "result": { "...": "..." },
  "debug": [
    { "pct": 0.0, "pred_units_model": 1.2, "pred_units_eq": 2.5, "...": "..." },
    { "pct": 0.05, "pred_units_model": 1.3, "pred_units_eq": 2.7, "...": "..." }
  ]
}
```

---

## Status values

Typical values include:
- `can_clear_inventory` — at least one discount pct meets the coverage target
- `cannot_clear_*` — cannot meet target; fallback strategy chooses a best-effort pct

> Exact fallback status string depends on your decision policy.

---

## Error handling

### 400 Bad Request
Returned when required fields are missing or have invalid types.
```json
{ "error": "Missing required fields.", "missing": ["amount_left"] }
```

### 503 Service Unavailable
Returned when model artifacts are missing / not loaded.
```json
{
  "error": "Model artifacts not loaded.",
  "details": "Missing artifacts for prefix '...'",
  "hint": "Make sure <prefix>.txt and <prefix>.meta.json exist."
}
```

### 500 Internal Server Error
Returned when inference fails.
```json
{ "error": "Inference failed.", "details": "SomeError: ..." }
```

---

## Configuration

### Environment variables
- `DISCOUNT_ARTIFACT_PREFIX` *(string)*  
  **Path prefix (no extension)** for the artifacts:
  - `<prefix>.txt`
  - `<prefix>.meta.json`

- `PORT` *(int, default: 8000)*
- Run from the project root

### Example
```bash
export DISCOUNT_ARTIFACT_PREFIX="../models/artifacts/discount_lgbm"
export PORT=8000
python -m flask --app src.api.discount_prediction run --host 0.0.0.0 --port 8000
```

---

## Node.js (Axios) integration example

### Install
```bash
npm init -y
npm i axios
```

### Client (`discountClientAxios.js`)
```js
const axios = require("axios");

const BASE_URL = process.env.BASE_URL || "http://127.0.0.1:8000";

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 8000,
  headers: {
    "Content-Type": "application/json",
    "Accept": "application/json",
  },
});

async function health() {
  const res = await client.get("/health");
  return res.data;
}

async function recommendDiscount(payload) {
  const res = await client.post("/discount", payload);
  return res.data;
}

function printAxiosError(err) {
  if (err.response) {
    console.error(`HTTP ${err.response.status} ${err.response.statusText}`);
    console.error("Body:", JSON.stringify(err.response.data, null, 2));
    return;
  }
  if (err.request) {
    console.error("No response received (network/timeout?).");
    console.error(err.message);
    return;
  }
  console.error("Error:", err.message);
}

(async () => {
  try {
    const h = await health();
    console.log("Health:", h);
    if (!h.model_loaded) process.exit(1);

    const payload = {
      amount_left: 20,
      expected_demand_for_remaining: 18,
      place_id: 59897,
      item_id: 59932,
      window_hours: 4.0,
      pct_grid: [0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40],
      baseline_pct: 0.0,
      aggressiveness: 5.0,
      return_debug: false
    };

    const out = await recommendDiscount(payload);
    console.log(JSON.stringify(out, null, 2));

    console.log("recommended_pct:", out?.result?.recommended_pct);
    console.log("status:", out?.result?.status);
  } catch (err) {
    printAxiosError(err);
    process.exit(1);
  }
})();
```

Run:
```bash
node discountClientAxios.js
```

If API is remote:
```bash
BASE_URL="http://<host>:8000" node discountClientAxios.js
```

---

## Postman / OpenAPI

If you have:
- `openapi.json` → Postman can import it to generate requests
- Postman collection/environment JSON → run tests via Collection Runner

---

## Notes for production
- Load artifacts once at startup for low latency (already implemented).
- Use a process manager (e.g., gunicorn) for concurrency in production.
- Mount artifacts path in Docker/K8s and set `DISCOUNT_ARTIFACT_PREFIX` accordingly.
