# Sales Management API

Sales transaction logging with automatic stock deduction.

---

## Overview

The Sales Management API provides endpoints for recording sales transactions and retrieving sales history. When sales are logged, stock levels are automatically reduced for both menu items and addons.

---

## Base URL

- Local: `http://localhost:5000/api/sales`
- Production: `https://your-domain.com/api/sales`

---

## Authentication

All endpoints require JWT authentication via the `Authorization` header:

```http
Authorization: Bearer <your_jwt_token>
```

Obtain a token via the `/api/users/login` endpoint.

---

## Endpoints

### `POST /api/sales`

Log a new sale and automatically deduct stock.

**Authentication:** Required

**Request Body:**
```json
{
  "menuItemId": "6984c05bb162ac961c44eafb",
  "addonIds": ["6984c05bb162ac961c44eb01", "6984c05bb162ac961c44eb02"],
  "quantity": 2,
  "pricePerUnit": 12.99,
  "discount": 1.50
}
```

**Required Fields:**
- `menuItemId` *(string)*: MongoDB ObjectId of the menu item sold
- `pricePerUnit` *(number)*: Price per unit (before discount)

**Optional Fields:**
- `addonIds` *(array[string], default: [])*: Array of addon ObjectIds
- `quantity` *(integer, default: 1)*: Number of items sold
- `discount` *(number, default: 0)*: Discount amount applied

**Response (201 Created):**
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "user": "507f191e810c19729de860ea",
  "menuItem": "6984c05bb162ac961c44eafb",
  "addons": [
    "6984c05bb162ac961c44eb01",
    "6984c05bb162ac961c44eb02"
  ],
  "quantity": 2,
  "pricePerUnit": 12.99,
  "discount": 1.50,
  "createdAt": "2024-01-15T14:30:00.000Z"
}
```

**Automatic Stock Deduction:**

When a sale is created, the following happens automatically:

1. **Menu Item Stock Deduction:**
   - Finds stock entry with `itemType: "MenuItem"`
   - Reduces `quantity` by sale quantity
   - Logs success or warning to console

2. **Addon Stock Deduction:**
   - For each addon in `addonIds`
   - Finds stock entry with `itemType: "Addon"`
   - Reduces `quantity` by sale quantity
   - Logs success or warning to console

**Console Output Example:**
```
✅ Deducted 2 from MenuItem 6984c05bb162ac961c44eafb. New quantity: 48
✅ Deducted 2 from Addon 6984c05bb162ac961c44eb01. New quantity: 198
✅ Deducted 2 from Addon 6984c05bb162ac961c44eb02. New quantity: 145
```

**If Stock Entry Not Found:**
```
⚠️  No stock entry found for MenuItem 6984c05bb162ac961c44eafb
⚠️  No stock entry found for Addon 6984c05bb162ac961c44eb01
```

**Important Notes:**
- Stock deduction happens **silently** - sale is created even if stock not found
- Stock can go negative if insufficient inventory
- No validation against current stock levels
- Consider adding stock availability checks before sale creation

**Error Response (400 Bad Request):**
```json
{
  "message": "Please include menu item and price per unit"
}
```

---

### `GET /api/sales`

Retrieve all sales for the authenticated user.

**Authentication:** Required

**Response (200 OK):**
```json
[
  {
    "_id": "507f1f77bcf86cd799439011",
    "user": "507f191e810c19729de860ea",
    "menuItem": {
      "_id": "6984c05bb162ac961c44eafb",
      "title": "Classic Burger",
      "price": 12.99,
      "category": "mains",
      "image": "burger.jpg"
    },
    "addons": [
      {
        "_id": "6984c05bb162ac961c44eb01",
        "name": "Extra Cheese",
        "price": 1.50
      },
      {
        "_id": "6984c05bb162ac961c44eb02",
        "name": "Bacon",
        "price": 2.00
      }
    ],
    "quantity": 2,
    "pricePerUnit": 12.99,
    "discount": 1.50,
    "createdAt": "2024-01-15T14:30:00.000Z"
  },
  {
    "_id": "507f1f77bcf86cd799439012",
    "user": "507f191e810c19729de860ea",
    "menuItem": {
      "_id": "6984c05bb162ac961c44eafc",
      "title": "Caesar Salad",
      "price": 9.99,
      "category": "salads"
    },
    "addons": [],
    "quantity": 1,
    "pricePerUnit": 9.99,
    "discount": 0,
    "createdAt": "2024-01-15T14:25:00.000Z"
  }
]
```

**Response Features:**
- Sorted by creation date (newest first)
- `menuItem` is populated with full details
- `addons` array is populated with addon details
- Empty array `[]` if no sales recorded

---

### `GET /api/sales/:id`

Retrieve a specific sale by ID.

**Authentication:** Required

**URL Parameters:**
- `id` *(string)*: Sale MongoDB ObjectId

**Response (200 OK):**
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "user": "507f191e810c19729de860ea",
  "menuItem": {
    "_id": "6984c05bb162ac961c44eafb",
    "title": "Classic Burger",
    "price": 12.99,
    "category": "mains"
  },
  "addons": [
    {
      "_id": "6984c05bb162ac961c44eb01",
      "name": "Extra Cheese",
      "price": 1.50
    }
  ],
  "quantity": 2,
  "pricePerUnit": 12.99,
  "discount": 1.50,
  "createdAt": "2024-01-15T14:30:00.000Z"
}
```

**Error Response (404 Not Found):**
```json
{
  "message": "Sale not found"
}
```

**Error Response (401 Unauthorized):**
```json
{
  "message": "User not authorized"
}
```

---

## Sale Calculation Examples

### Example 1: Simple Sale (No Addons, No Discount)
```json
{
  "menuItemId": "6984c05bb162ac961c44eafb",
  "quantity": 1,
  "pricePerUnit": 12.99,
  "discount": 0
}
```
**Total:** $12.99

---

### Example 2: Sale with Addons
```json
{
  "menuItemId": "6984c05bb162ac961c44eafb",
  "addonIds": ["addon1", "addon2"],
  "quantity": 1,
  "pricePerUnit": 12.99,
  "discount": 0
}
```
**Calculation:**
- Base: $12.99
- Addon 1: $1.50
- Addon 2: $2.00
- **Total:** $16.49

**Note:** Addon prices are stored in the addon documents, not in the sale record.

---

### Example 3: Multiple Quantity with Discount
```json
{
  "menuItemId": "6984c05bb162ac961c44eafb",
  "quantity": 3,
  "pricePerUnit": 12.99,
  "discount": 5.00
}
```
**Calculation:**
- Subtotal: 3 × $12.99 = $38.97
- Discount: -$5.00
- **Total:** $33.97

---

## Stock Deduction Behavior

### Scenario 1: Sufficient Stock
```javascript
// Before sale
MenuItem Stock: 50
Addon Stock: 200

// Sale created (quantity: 2)
POST /api/sales
{
  "menuItemId": "item123",
  "addonIds": ["addon456"],
  "quantity": 2,
  "pricePerUnit": 10.00
}

// After sale
MenuItem Stock: 48  // 50 - 2
Addon Stock: 198    // 200 - 2
```

---

### Scenario 2: Insufficient Stock (Goes Negative)
```javascript
// Before sale
MenuItem Stock: 1

// Sale created (quantity: 3)
POST /api/sales
{
  "menuItemId": "item123",
  "quantity": 3,
  "pricePerUnit": 10.00
}

// After sale
MenuItem Stock: -2  // 1 - 3 (NEGATIVE!)
```

**Warning:** The API allows negative stock. Consider implementing stock validation.

---

### Scenario 3: Stock Entry Doesn't Exist
```javascript
// No stock entry for MenuItem "item123"

// Sale created
POST /api/sales
{
  "menuItemId": "item123",
  "quantity": 2,
  "pricePerUnit": 10.00
}

// Result:
// - Sale is created successfully
// - Console warning: "No stock entry found"
// - No stock deduction occurs
```

---

## Error Responses

### 400 Bad Request
Missing required fields:
```json
{
  "message": "Please include menu item and price per unit"
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
Sale not found:
```json
{
  "message": "Sale not found"
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

// Create sale
async function createSale(saleData) {
  const res = await client.post('/sales', saleData);
  return res.data;
}

// Get all sales
async function getSales() {
  const res = await client.get('/sales');
  return res.data;
}

// Get sale by ID
async function getSaleById(id) {
  const res = await client.get(`/sales/${id}`);
  return res.data;
}

// Example usage
(async () => {
  try {
    // Login
    await login('user@example.com', 'password123');
    console.log('✅ Logged in\n');

    // Create a simple sale
    const sale1 = await createSale({
      menuItemId: '6984c05bb162ac961c44eafb',
      quantity: 2,
      pricePerUnit: 12.99,
      discount: 1.00
    });
    console.log('✅ Sale created:', sale1._id);

    // Create sale with addons
    const sale2 = await createSale({
      menuItemId: '6984c05bb162ac961c44eafc',
      addonIds: [
        '6984c05bb162ac961c44eb01',
        '6984c05bb162ac961c44eb02'
      ],
      quantity: 1,
      pricePerUnit: 9.99,
      discount: 0
    });
    console.log('✅ Sale with addons created:', sale2._id);

    // Get all sales
    const allSales = await getSales();
    console.log(`\n📊 Total sales recorded: ${allSales.length}`);

    // Display recent sales
    console.log('\n📋 RECENT SALES:');
    allSales.slice(0, 5).forEach((sale, i) => {
      const total = (sale.pricePerUnit * sale.quantity) - sale.discount;
      console.log(`  ${i + 1}. ${sale.menuItem.title} (×${sale.quantity})`);
      console.log(`     Price: $${sale.pricePerUnit} | Discount: $${sale.discount}`);
      console.log(`     Total: $${total.toFixed(2)}`);
      console.log(`     Addons: ${sale.addons.length}`);
      console.log(`     Date: ${new Date(sale.createdAt).toLocaleString()}\n`);
    });

    // Get specific sale
    if (allSales.length > 0) {
      const specific = await getSaleById(allSales[0]._id);
      console.log('🔍 Sale Details:');
      console.log(JSON.stringify(specific, null, 2));
    }

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
node salesClient.js
```

**Expected Output:**
```
✅ Logged in

✅ Sale created: 507f1f77bcf86cd799439011
✅ Sale with addons created: 507f1f77bcf86cd799439012

📊 Total sales recorded: 47

📋 RECENT SALES:
  1. Classic Burger (×2)
     Price: $12.99 | Discount: $1.00
     Total: $24.98
     Addons: 0
     Date: 1/15/2024, 2:30:00 PM

  2. Caesar Salad (×1)
     Price: $9.99 | Discount: $0.00
     Total: $9.99
     Addons: 2
     Date: 1/15/2024, 2:25:00 PM

  ...
```

---

## Database Schema

```javascript
const saleSchema = new Schema({
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
    index: true
  },
  menuItem: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'MenuItem',
    required: true,
    index: true
  },
  addons: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Addon'
  }],
  quantity: {
    type: Number,
    required: true,
    min: 1,
    default: 1
  },
  pricePerUnit: {
    type: Number,
    required: true,
    min: 0
  },
  discount: {
    type: Number,
    min: 0,
    default: 0
  }
}, {
  timestamps: true
});

// Indexes for efficient queries
saleSchema.index({ user: 1, createdAt: -1 });
saleSchema.index({ menuItem: 1, createdAt: -1 });
```

---

## Sales Analytics Queries

### Total Revenue
```javascript
const totalRevenue = await Sale.aggregate([
  { $match: { user: userId } },
  {
    $group: {
      _id: null,
      total: {
        $sum: {
          $subtract: [
            { $multiply: ['$pricePerUnit', '$quantity'] },
            '$discount'
          ]
        }
      }
    }
  }
]);
```

### Daily Sales Count
```javascript
const dailySales = await Sale.aggregate([
  { $match: { user: userId } },
  {
    $group: {
      _id: { $dateToString: { format: '%Y-%m-%d', date: '$createdAt' } },
      count: { $sum: '$quantity' },
      revenue: {
        $sum: {
          $subtract: [
            { $multiply: ['$pricePerUnit', '$quantity'] },
            '$discount'
          ]
        }
      }
    }
  },
  { $sort: { _id: -1 } }
]);
```

### Top Selling Items
```javascript
const topItems = await Sale.aggregate([
  { $match: { user: userId } },
  {
    $group: {
      _id: '$menuItem',
      totalSold: { $sum: '$quantity' },
      revenue: {
        $sum: {
          $subtract: [
            { $multiply: ['$pricePerUnit', '$quantity'] },
            '$discount'
          ]
        }
      }
    }
  },
  { $sort: { totalSold: -1 } },
  { $limit: 10 }
]);
```

---

## Integration with Stock System

### Stock Synchronization Script

Use this script to sync historical sales with stock:

```bash
node scripts/sync_sales_to_stock.js
```

**What it does:**
1. Processes all existing sales in chronological order
2. Calculates cumulative deductions per stock item
3. Applies all deductions in a single batch update
4. Provides detailed summary of changes

**Use Case:** 
- Migrating from manual stock tracking
- Fixing stock discrepancies
- Backfilling stock data after sales import

---

## Best Practices

### 1. Validate Stock Before Sale
```javascript
// Check stock availability
const stock = await Stock.findOne({
  user: userId,
  item: menuItemId,
  itemType: 'MenuItem'
});

if (!stock || stock.quantity < requestedQuantity) {
  throw new Error('Insufficient stock');
}

// Then create sale
await createSale({...});
```

### 2. Transaction-Safe Sales
```javascript
const session = await mongoose.startSession();
session.startTransaction();

try {
  // Create sale
  const sale = await Sale.create([saleData], { session });
  
  // Deduct stock
  await Stock.updateOne(
    { user, item: menuItemId },
    { $inc: { quantity: -quantity } },
    { session }
  );
  
  await session.commitTransaction();
} catch (error) {
  await session.abortTransaction();
  throw error;
} finally {
  session.endSession();
}
```

### 3. Add Stock Warnings
```javascript
// After stock deduction
if (menuItemStock && menuItemStock.quantity < 10) {
  console.warn(`⚠️  Low stock alert: ${menuItemId} has ${menuItemStock.quantity} left`);
}
```

---

## Installation & Setup

### Prerequisites
- Node.js 14.x+
- MongoDB 4.4+
- MenuItem, Addon, and Stock collections configured

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

- Sales cannot be updated or deleted (immutable by design)
- Stock deduction is automatic but not validated
- Negative stock is allowed - consider adding constraints
- Console logs show stock operations for debugging
- Addons are treated as separate stock items
- Each addon is deducted by the sale quantity (not per unit)

---

## License

MIT License
