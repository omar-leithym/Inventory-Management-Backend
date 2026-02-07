# Stock Management API

Inventory tracking and AI-powered stock recommendation service.

---

## Overview

The Stock Management API provides endpoints for tracking inventory levels, managing stock entries, and generating intelligent stock replenishment recommendations based on AI demand predictions.

---

## Base URL

- Local: `http://localhost:5000/api/stock`
- Production: `https://your-domain.com/api/stock`

---

## Authentication

All endpoints require JWT authentication via the `Authorization` header:

```http
Authorization: Bearer <your_jwt_token>
```

Obtain a token via the `/api/users/login` endpoint.

---

## Endpoints

### `POST /api/stock`

Add new stock or update existing stock quantity for an item.

**Authentication:** Required

**Request Body:**
```json
{
  "itemId": "6984c05bb162ac961c44eafb",
  "itemType": "MenuItem",
  "quantity": 100
}
```

**Required Fields:**
- `itemId` *(string)*: MongoDB ObjectId of the item (MenuItem or Addon)
- `itemType` *(string)*: Must be either `"MenuItem"` or `"Addon"`
- `quantity` *(integer)*: Stock quantity to add (≥ 0)

**Response (201 Created)** - New stock entry:
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "user": "507f191e810c19729de860ea",
  "item": "6984c05bb162ac961c44eafb",
  "itemType": "MenuItem",
  "quantity": 100,
  "createdAt": "2024-01-15T10:30:00.000Z"
}
```

**Response (200 OK)** - Updated existing stock:
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "user": "507f191e810c19729de860ea",
  "item": "6984c05bb162ac961c44eafb",
  "itemType": "MenuItem",
  "quantity": 150,
  "createdAt": "2024-01-10T08:00:00.000Z",
  "updatedAt": "2024-01-15T10:30:00.000Z"
}
```

**Behavior:**
- If stock entry exists for the user/item/type: adds quantity to existing stock
- If no entry exists: creates new stock entry
- Quantity is cumulative when updating

**Error Response (400 Bad Request):**
```json
{
  "message": "Invalid item type. Must be MenuItem or Addon"
}
```

**Error Response (404 Not Found):**
```json
{
  "message": "MenuItem not found"
}
```

---

### `GET /api/stock`

Retrieve all stock entries for the authenticated user.

**Authentication:** Required

**Response (200 OK):**
```json
[
  {
    "_id": "507f1f77bcf86cd799439011",
    "user": "507f191e810c19729de860ea",
    "item": {
      "_id": "6984c05bb162ac961c44eafb",
      "title": "Classic Burger",
      "price": 12.99,
      "category": "mains"
    },
    "itemType": "MenuItem",
    "quantity": 50,
    "createdAt": "2024-01-15T10:30:00.000Z"
  },
  {
    "_id": "507f1f77bcf86cd799439012",
    "user": "507f191e810c19729de860ea",
    "item": {
      "_id": "6984c05bb162ac961c44eafc",
      "name": "Extra Cheese",
      "price": 1.50
    },
    "itemType": "Addon",
    "quantity": 200,
    "createdAt": "2024-01-15T11:00:00.000Z"
  }
]
```

**Response Features:**
- Sorted by creation date (newest first)
- Items are populated with full details
- Empty array `[]` if no stock entries

---

### `GET /api/stock/:id`

Retrieve a specific stock entry by ID.

**Authentication:** Required

**URL Parameters:**
- `id` *(string)*: Stock entry MongoDB ObjectId

**Response (200 OK):**
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "user": "507f191e810c19729de860ea",
  "item": {
    "_id": "6984c05bb162ac961c44eafb",
    "title": "Classic Burger",
    "price": 12.99
  },
  "itemType": "MenuItem",
  "quantity": 50,
  "createdAt": "2024-01-15T10:30:00.000Z"
}
```

**Error Response (404 Not Found):**
```json
{
  "message": "Stock item not found"
}
```

**Error Response (401 Unauthorized):**
```json
{
  "message": "User not authorized"
}
```

---

### `PUT /api/stock/:id`

Update stock quantity for a specific stock entry.

**Authentication:** Required

**URL Parameters:**
- `id` *(string)*: Stock entry MongoDB ObjectId

**Request Body:**
```json
{
  "quantity": 75
}
```

**Required Fields:**
- `quantity` *(integer)*: New stock quantity (≥ 0)

**Response (200 OK):**
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "user": "507f191e810c19729de860ea",
  "item": "6984c05bb162ac961c44eafb",
  "itemType": "MenuItem",
  "quantity": 75,
  "updatedAt": "2024-01-15T12:00:00.000Z"
}
```

**Behavior:**
- Sets absolute quantity (not cumulative)
- Use this to correct stock levels or reduce inventory

**Error Response (404 Not Found):**
```json
{
  "message": "Stock item not found"
}
```

**Error Response (401 Unauthorized):**
```json
{
  "message": "User not authorized"
}
```

---

### `DELETE /api/stock/:id`

Delete a stock entry.

**Authentication:** Required

**URL Parameters:**
- `id` *(string)*: Stock entry MongoDB ObjectId

**Response (200 OK):**
```json
{
  "id": "507f1f77bcf86cd799439011"
}
```

**Error Response (404 Not Found):**
```json
{
  "message": "Stock item not found"
}
```

**Error Response (401 Unauthorized):**
```json
{
  "message": "User not authorized"
}
```

---

### `GET /api/stock/recommendations`

Generate AI-powered stock recommendations for all catalog items.

**Authentication:** Required

**Response (200 OK):**
```json
{
  "recommendations": [
    {
      "menuItemId": "6984c05bb162ac961c44eafb",
      "inputDays": 7,
      "predictedDemand": 70,
      "dailyRate": 10,
      "aimStockLevel": 108,
      "currentStock": 50,
      "calculatedStock": 58,
      "details": {
        "leadTimeDemand": 20,
        "cycleDemand": 70,
        "baseDemand": 90,
        "bufferUsed": 1.2
      }
    },
    {
      "menuItemId": "6984c05bb162ac961c44eafc",
      "inputDays": 7,
      "predictedDemand": 140,
      "dailyRate": 20,
      "aimStockLevel": 216,
      "currentStock": 200,
      "calculatedStock": 16,
      "details": {
        "leadTimeDemand": 40,
        "cycleDemand": 140,
        "baseDemand": 180,
        "bufferUsed": 1.2
      }
    }
  ],
  "alerts": [
    {
      "menuItemId": "6984c05bb162ac961c44eafb",
      "severity": "WARNING",
      "title": "Replenishment Needed",
      "message": "Current stock (50) is below target (108).",
      "action": "Add 58 units to next order.",
      "itemType": "MenuItem"
    },
    {
      "menuItemId": "6984c05bb162ac961c44eafc",
      "severity": "INFO",
      "title": "Stock Adequate",
      "message": "Stock levels are near optimal.",
      "action": "Add 16 units to maintain buffer.",
      "itemType": "Addon"
    }
  ],
  "summary": {
    "totalAlerts": 15,
    "critical": 2,
    "warning": 8,
    "info": 5,
    "items": [...]
  },
  "appliedSettings": {
    "demandWindow": 7,
    "leadTime": 2,
    "safetyStockBuffer": 20,
    "lowStockThreshold": 20
  }
}
```

**Response Fields:**

**recommendations[]:**
- `menuItemId`: Item identifier
- `predictedDemand`: AI-predicted total demand for the period
- `dailyRate`: Average daily demand (predictedDemand / inputDays)
- `aimStockLevel`: Target stock level (the "aim number")
- `currentStock`: Current inventory quantity
- `calculatedStock`: Units to order/replenish
- `details`: Calculation breakdown

**alerts[]:**
- `severity`: `"CRITICAL"` | `"WARNING"` | `"INFO"`
- `title`: Alert headline
- `message`: Detailed description
- `action`: Recommended action

**Alert Severity Levels:**

| Severity | Condition | Example |
|----------|-----------|---------|
| CRITICAL | Stock ≤ 0 OR (stock/target) < lowStockThreshold% | Out of stock or critically low |
| WARNING | Stock < target AND above critical threshold | Replenishment needed |
| INFO | Stock > 2× target | Overstocked |

**Calculation Formula:**
```
Target Stock = (Lead Time Demand + Cycle Demand) × Buffer

Where:
- Lead Time Demand = Daily Rate × Lead Time Days
- Cycle Demand = Total Predicted Demand
- Buffer = 1 + (Safety Stock % / 100)
- Replenishment = max(0, Target - Current Stock)
```

**Settings Impact:**
All calculations use the authenticated user's settings:
- `demandWindow`: Prediction horizon (default: 7 days)
- `leadTime`: Supplier delivery days (default: 2)
- `safetyStockBuffer`: Safety percentage (default: 20%)
- `lowStockThreshold`: Critical alert threshold (default: 20%)

**Notes:**
- Processes all MenuItems and Addons in the catalog
- AI prediction currently uses placeholder (10 units/day)
- Replace `fetchAIPrediction()` in service with actual ML model
- Items with aim < 2 and stock > 0 are skipped (low priority)

---

## Error Responses

### 400 Bad Request
Invalid input:
```json
{
  "message": "Invalid item type. Must be MenuItem or Addon"
}
```

### 401 Unauthorized
Missing or invalid authentication:
```json
{
  "message": "User not authorized"
}
```

```json
{
  "message": "User not found"
}
```

### 404 Not Found
Resource not found:
```json
{
  "message": "Stock item not found"
}
```

```json
{
  "message": "MenuItem not found"
}
```

### 500 Internal Server Error
Server-side error:
```json
{
  "message": "Server error",
  "error": "Detailed error message"
}
```

---

## Node.js Client Example

### Installation
```bash
npm install axios
```

### Client Code
```javascript
const axios = require('axios');

const API_BASE = 'http://localhost:5000/api';
let authToken = null;

const client = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' }
});

// Add auth token
client.interceptors.request.use(config => {
  if (authToken) {
    config.headers.Authorization = `Bearer ${authToken}`;
  }
  return config;
});

// Login
async function login(email, password) {
  const res = await axios.post(`${API_BASE}/users/login`, {
    email,
    password
  });
  authToken = res.data.token;
  return res.data;
}

// Add stock
async function addStock(itemId, itemType, quantity) {
  const res = await client.post('/stock', {
    itemId,
    itemType,
    quantity
  });
  return res.data;
}

// Get all stock
async function getStock() {
  const res = await client.get('/stock');
  return res.data;
}

// Get stock by ID
async function getStockById(id) {
  const res = await client.get(`/stock/${id}`);
  return res.data;
}

// Update stock quantity
async function updateStock(id, quantity) {
  const res = await client.put(`/stock/${id}`, { quantity });
  return res.data;
}

// Delete stock
async function deleteStock(id) {
  const res = await client.delete(`/stock/${id}`);
  return res.data;
}

// Get recommendations
async function getRecommendations() {
  const res = await client.get('/stock/recommendations');
  return res.data;
}

// Example usage
(async () => {
  try {
    // Login
    await login('user@example.com', 'password123');
    console.log('✅ Logged in\n');

    // Add stock
    const newStock = await addStock(
      '6984c05bb162ac961c44eafb',
      'MenuItem',
      100
    );
    console.log('✅ Added stock:', newStock._id);

    // Get all stock
    const allStock = await getStock();
    console.log(`📦 Total stock entries: ${allStock.length}`);

    // Update stock
    if (allStock.length > 0) {
      const updated = await updateStock(allStock[0]._id, 75);
      console.log('✅ Updated stock to:', updated.quantity);
    }

    // Get recommendations
    const recs = await getRecommendations();
    console.log('\n📊 STOCK RECOMMENDATIONS');
    console.log('========================');
    console.log(`Total Alerts: ${recs.summary.totalAlerts}`);
    console.log(`  Critical: ${recs.summary.critical}`);
    console.log(`  Warnings: ${recs.summary.warning}`);
    console.log(`  Info: ${recs.summary.info}\n`);

    // Show critical alerts
    const critical = recs.alerts.filter(a => a.severity === 'CRITICAL');
    if (critical.length > 0) {
      console.log('🚨 CRITICAL ALERTS:');
      critical.forEach(alert => {
        console.log(`  ${alert.title}: ${alert.message}`);
        console.log(`  Action: ${alert.action}\n`);
      });
    }

    // Show top 3 recommendations
    console.log('📋 TOP RECOMMENDATIONS:');
    recs.recommendations.slice(0, 3).forEach((rec, i) => {
      console.log(`  ${i + 1}. Item ${rec.menuItemId}`);
      console.log(`     Current: ${rec.currentStock} | Target: ${rec.aimStockLevel}`);
      console.log(`     Order: ${rec.calculatedStock} units\n`);
    });

  } catch (error) {
    if (error.response) {
      console.error(`HTTP ${error.response.status}:`, error.response.data);
    } else {
      console.error('Error:', error.message);
    }
  }
})();
```

### Run
```bash
node stockClient.js
```

**Expected Output:**
```
✅ Logged in

✅ Added stock: 507f1f77bcf86cd799439011
📦 Total stock entries: 15
✅ Updated stock to: 75

📊 STOCK RECOMMENDATIONS
========================
Total Alerts: 15
  Critical: 2
  Warnings: 8
  Info: 5

🚨 CRITICAL ALERTS:
  Out of Stock: Item usage is halted. Immediate replenishment required.
  Action: Order 108 units immediately.

  Critically Low Stock: Stock at 15% of target. Risk of stockout.
  Action: Order 95 units ASAP.

📋 TOP RECOMMENDATIONS:
  1. Item 6984c05bb162ac961c44eafb
     Current: 50 | Target: 108
     Order: 58 units

  2. Item 6984c05bb162ac961c44eafc
     Current: 200 | Target: 216
     Order: 16 units

  3. Item 6984c05bb162ac961c44eafd
     Current: 0 | Target: 84
     Order: 84 units
```

---

## Database Schema

```javascript
const stockSchema = new Schema({
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
    index: true
  },
  item: {
    type: mongoose.Schema.Types.ObjectId,
    refPath: 'itemType',
    required: true,
    index: true
  },
  itemType: {
    type: String,
    required: true,
    enum: ['MenuItem', 'Addon']
  },
  quantity: {
    type: Number,
    required: true,
    min: 0,
    default: 0
  }
}, {
  timestamps: true
});

// Compound index for efficient lookups
stockSchema.index({ user: 1, item: 1, itemType: 1 }, { unique: true });
```

**refPath Feature:**
- `item` field references different collections based on `itemType`
- When `itemType = "MenuItem"`, references `MenuItem` collection
- When `itemType = "Addon"`, references `Addon` collection
- Enables polymorphic relationships with proper population

---

## Installation & Setup

### Prerequisites
- Node.js 14.x+
- MongoDB 4.4+
- MenuItem and Addon collections must exist

### Install Dependencies
```bash
npm install express express-async-handler mongoose
```

### Environment Variables
```env
MONGO_URI=mongodb://localhost:27017/freshflow
JWT_SECRET=your_secret_key_here
PORT=5000
```

### Start Server
```bash
npm start
```

---

## Notes

- Stock quantities are always absolute (not negative)
- Recommendations endpoint processes entire catalog (can be slow for large catalogs)
- AI prediction placeholder returns `10 * days` - replace with actual ML model
- Alerts are regenerated on each recommendations request (not persisted)
- Stock is automatically deducted when sales are recorded (see Sales API)

---

## License

MIT License
