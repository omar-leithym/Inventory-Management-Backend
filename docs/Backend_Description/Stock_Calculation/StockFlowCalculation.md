\# Stock Flow Calculation API



AI-powered inventory management service that converts demand predictions into actionable stock requirements using configurable safety formulas.



---



\## Overview



The Stock Flow Calculation API analyzes predicted demand and current inventory levels to generate intelligent stock replenishment recommendations. It applies customizable lead time, safety buffer, and demand window parameters to calculate optimal stock targets.



\### Key Features



\- \*\*AI-Driven Predictions\*\*: Integrates with demand forecasting models for accurate future demand estimates

\- \*\*Configurable Safety Parameters\*\*: Customize lead time, safety stock buffer, and demand windows

\- \*\*Multi-Item Processing\*\*: Batch calculate stock needs for entire catalog (MenuItems + Addons)

\- \*\*Alert Generation\*\*: Automatic severity-based alerts (CRITICAL, WARNING, INFO)

\- \*\*Flexible Time Horizons\*\*: Support for daily, weekly, and custom prediction windows



---



\## Base URL



\- Local: `http://localhost:5000/api`

\- Production: `https://your-domain.com/api`



---



\## Core Calculation Formula



```

Target Stock = (Lead Time Demand + Cycle Demand) × Buffer Multiplier



Where:

\- Lead Time Demand = Daily Rate × Lead Time Days

\- Cycle Demand = Total Predicted Demand for Period

\- Buffer Multiplier = 1 + (Safety Stock % / 100)

\- Replenishment Needed = max(0, Target Stock - Current Stock)

```



\### Example Calculation



\*\*Inputs:\*\*

\- Predicted Demand (7 days): 70 units

\- Current Stock: 50 units

\- Lead Time: 2 days

\- Safety Buffer: 20%



\*\*Calculation:\*\*

```

Daily Rate = 70 / 7 = 10 units/day

Lead Time Demand = 10 × 2 = 20 units

Cycle Demand = 70 units

Base Demand = 20 + 70 = 90 units

Target Stock = 90 × 1.2 = 108 units

Replenishment = 108 - 50 = 58 units to order

```



---



\## Authentication



All endpoints require JWT authentication via the `Authorization` header:



```http

Authorization: Bearer <your\_jwt\_token>

```



Obtain a token via the `/api/users/login` endpoint.



---



\## Endpoints



\### `GET /api/stock/recommendations`



Generates stock recommendations for all catalog items based on AI predictions and current inventory.



\*\*Headers:\*\*

```http

Authorization: Bearer <token>

Content-Type: application/json

```



\*\*Query Parameters:\*\* None (uses authenticated user's settings)



\*\*Response (200 OK):\*\*

```json

{

&nbsp; "recommendations": \[

&nbsp;   {

&nbsp;     "menuItemId": "6984c05bb162ac961c44eafb",

&nbsp;     "inputDays": 7,

&nbsp;     "predictedDemand": 70,

&nbsp;     "dailyRate": 10,

&nbsp;     "aimStockLevel": 108,

&nbsp;     "currentStock": 50,

&nbsp;     "calculatedStock": 58,

&nbsp;     "details": {

&nbsp;       "leadTimeDemand": 20,

&nbsp;       "cycleDemand": 70,

&nbsp;       "baseDemand": 90,

&nbsp;       "bufferUsed": 1.2

&nbsp;     }

&nbsp;   }

&nbsp; ],

&nbsp; "alerts": \[

&nbsp;   {

&nbsp;     "menuItemId": "6984c05bb162ac961c44eafb",

&nbsp;     "severity": "WARNING",

&nbsp;     "title": "Replenishment Needed",

&nbsp;     "message": "Current stock (50) is below target (108).",

&nbsp;     "action": "Add 58 units to next order.",

&nbsp;     "itemType": "MenuItem"

&nbsp;   }

&nbsp; ],

&nbsp; "summary": {

&nbsp;   "totalAlerts": 15,

&nbsp;   "critical": 3,

&nbsp;   "warning": 8,

&nbsp;   "info": 4,

&nbsp;   "items": \[...]

&nbsp; },

&nbsp; "appliedSettings": {

&nbsp;   "demandWindow": 7,

&nbsp;   "leadTime": 2,

&nbsp;   "safetyStockBuffer": 20,

&nbsp;   "lowStockThreshold": 20

&nbsp; }

}

```



---



\### `GET /api/stock`



Retrieves current stock levels for the authenticated user.



\*\*Response (200 OK):\*\*

```json

\[

&nbsp; {

&nbsp;   "\_id": "507f1f77bcf86cd799439011",

&nbsp;   "user": "507f191e810c19729de860ea",

&nbsp;   "item": "6984c05bb162ac961c44eafb",

&nbsp;   "itemType": "MenuItem",

&nbsp;   "quantity": 50,

&nbsp;   "createdAt": "2024-01-15T10:30:00.000Z"

&nbsp; }

]

```



---



\### `POST /api/stock`



Adds or updates stock for an item.



\*\*Request Body:\*\*

```json

{

&nbsp; "itemId": "6984c05bb162ac961c44eafb",

&nbsp; "itemType": "MenuItem",

&nbsp; "quantity": 100

}

```



\*\*Validation:\*\*

\- `itemType`: Must be either `"MenuItem"` or `"Addon"`

\- `quantity`: Integer ≥ 0



\*\*Response (201 Created / 200 OK):\*\*

```json

{

&nbsp; "\_id": "507f1f77bcf86cd799439011",

&nbsp; "user": "507f191e810c19729de860ea",

&nbsp; "item": "6984c05bb162ac961c44eafb",

&nbsp; "itemType": "MenuItem",

&nbsp; "quantity": 100,

&nbsp; "createdAt": "2024-01-15T10:30:00.000Z"

}

```



---



\### `PUT /api/stock/:id`



Updates stock quantity for a specific stock entry.



\*\*Request Body:\*\*

```json

{

&nbsp; "quantity": 75

}

```



\*\*Response (200 OK):\*\*

```json

{

&nbsp; "\_id": "507f1f77bcf86cd799439011",

&nbsp; "quantity": 75

}

```



---



\### `DELETE /api/stock/:id`



Deletes a stock entry.



\*\*Response (200 OK):\*\*

```json

{

&nbsp; "id": "507f1f77bcf86cd799439011"

}

```



---



\### `GET /api/stock/:id`



Retrieves a specific stock entry by ID.



\*\*Response (200 OK):\*\*

```json

{

&nbsp; "\_id": "507f1f77bcf86cd799439011",

&nbsp; "user": "507f191e810c19729de860ea",

&nbsp; "item": {

&nbsp;   "\_id": "6984c05bb162ac961c44eafb",

&nbsp;   "title": "Classic Burger",

&nbsp;   "price": 12.99

&nbsp; },

&nbsp; "itemType": "MenuItem",

&nbsp; "quantity": 50

}

```



---



\## User Settings Configuration



\### `PUT /api/users/settings`



Configure calculation parameters that affect stock recommendations.



\*\*Request Body:\*\*

```json

{

&nbsp; "demandWindow": 7,

&nbsp; "leadTime": 2,

&nbsp; "safetyStockBuffer": 20,

&nbsp; "lowStockThreshold": 20,

&nbsp; "budgetLimit": 5000

}

```



\*\*Parameter Details:\*\*



| Parameter | Type | Default | Description |

|-----------|------|---------|-------------|

| `demandWindow` | Integer | 7 | Days to predict demand (1-30) |

| `leadTime` | Integer | 2 | Supplier delivery time in days (0-14) |

| `safetyStockBuffer` | Integer | 20 | Safety stock percentage (0-100) |

| `lowStockThreshold` | Integer | 20 | % threshold for CRITICAL alerts (0-50) |

| `budgetLimit` | Number | - | Optional monthly budget cap |



\*\*Response (200 OK):\*\*

```json

{

&nbsp; "demandWindow": 7,

&nbsp; "leadTime": 2,

&nbsp; "safetyStockBuffer": 20,

&nbsp; "lowStockThreshold": 20,

&nbsp; "budgetLimit": 5000

}

```



---



\### `GET /api/users/settings`



Retrieves current user settings.



\*\*Response (200 OK):\*\*

```json

{

&nbsp; "demandWindow": 7,

&nbsp; "leadTime": 2,

&nbsp; "safetyStockBuffer": 20,

&nbsp; "lowStockThreshold": 20

}

```



---



\## Alert Severity Levels



Alerts are categorized into three severity levels:



\### CRITICAL

\- \*\*Out of Stock\*\*: `currentStock <= 0`

\- \*\*Critically Low\*\*: `(currentStock / target) < lowStockThreshold%`



\*\*Example:\*\*

```json

{

&nbsp; "severity": "CRITICAL",

&nbsp; "title": "Out of Stock",

&nbsp; "message": "Item usage is halted. Immediate replenishment required.",

&nbsp; "action": "Order 108 units immediately."

}

```



\### WARNING

\- \*\*Replenishment Needed\*\*: `currentStock < aimStockLevel` but above critical threshold



\*\*Example:\*\*

```json

{

&nbsp; "severity": "WARNING",

&nbsp; "title": "Replenishment Needed",

&nbsp; "message": "Current stock (50) is below target (108).",

&nbsp; "action": "Add 58 units to next order."

}

```



\### INFO

\- \*\*Overstocked\*\*: `currentStock > aimStockLevel × 2`



\*\*Example:\*\*

```json

{

&nbsp; "severity": "INFO",

&nbsp; "title": "Overstocked",

&nbsp; "message": "Stock is double the requirement. Potential waste.",

&nbsp; "action": "Hold ordering. Excess: 100 units."

}

```



---



\## Error Responses



\### 400 Bad Request

```json

{

&nbsp; "message": "Invalid item type. Must be MenuItem or Addon"

}

```



\### 401 Unauthorized

```json

{

&nbsp; "message": "User not authorized"

}

```



\### 404 Not Found

```json

{

&nbsp; "message": "Stock item not found"

}

```



\### 500 Internal Server Error

```json

{

&nbsp; "message": "Server error",

&nbsp; "error": "Detailed error message"

}

```



---



\## Node.js Integration Example



\### Installation

```bash

npm install axios

```



\### Client Code (`stockClient.js`)

```javascript

const axios = require('axios');



const API\_BASE = 'http://localhost:5000/api';

let authToken = null;



// Create authenticated client

const client = axios.create({

&nbsp; baseURL: API\_BASE,

&nbsp; timeout: 10000,

&nbsp; headers: {

&nbsp;   'Content-Type': 'application/json'

&nbsp; }

});



// Add auth token to requests

client.interceptors.request.use(config => {

&nbsp; if (authToken) {

&nbsp;   config.headers.Authorization = `Bearer ${authToken}`;

&nbsp; }

&nbsp; return config;

});



// Login and get token

async function login(email, password) {

&nbsp; const res = await axios.post(`${API\_BASE}/users/login`, {

&nbsp;   email,

&nbsp;   password

&nbsp; });

&nbsp; authToken = res.data.token;

&nbsp; return res.data;

}



// Get stock recommendations

async function getRecommendations() {

&nbsp; const res = await client.get('/stock/recommendations');

&nbsp; return res.data;

}



// Update user settings

async function updateSettings(settings) {

&nbsp; const res = await client.put('/users/settings', settings);

&nbsp; return res.data;

}



// Add stock

async function addStock(itemId, itemType, quantity) {

&nbsp; const res = await client.post('/stock', {

&nbsp;   itemId,

&nbsp;   itemType,

&nbsp;   quantity

&nbsp; });

&nbsp; return res.data;

}



// Example usage

(async () => {

&nbsp; try {

&nbsp;   // Login

&nbsp;   await login('user@example.com', 'password123');

&nbsp;   console.log('✅ Logged in');



&nbsp;   // Configure settings

&nbsp;   await updateSettings({

&nbsp;     demandWindow: 7,

&nbsp;     leadTime: 3,

&nbsp;     safetyStockBuffer: 25,

&nbsp;     lowStockThreshold: 15

&nbsp;   });

&nbsp;   console.log('✅ Settings updated');



&nbsp;   // Get recommendations

&nbsp;   const data = await getRecommendations();

&nbsp;   

&nbsp;   console.log('\\n📊 STOCK RECOMMENDATIONS');

&nbsp;   console.log('========================');

&nbsp;   console.log(`Total Alerts: ${data.summary.totalAlerts}`);

&nbsp;   console.log(`Critical: ${data.summary.critical}`);

&nbsp;   console.log(`Warnings: ${data.summary.warning}`);

&nbsp;   

&nbsp;   // Show critical items

&nbsp;   const critical = data.alerts.filter(a => a.severity === 'CRITICAL');

&nbsp;   if (critical.length > 0) {

&nbsp;     console.log('\\n🚨 CRITICAL ITEMS:');

&nbsp;     critical.forEach(alert => {

&nbsp;       console.log(`  - ${alert.title}: ${alert.message}`);

&nbsp;       console.log(`    Action: ${alert.action}`);

&nbsp;     });

&nbsp;   }



&nbsp; } catch (error) {

&nbsp;   if (error.response) {

&nbsp;     console.error(`HTTP ${error.response.status}:`, error.response.data);

&nbsp;   } else {

&nbsp;     console.error('Error:', error.message);

&nbsp;   }

&nbsp; }

})();

```



\### Run

```bash

node stockClient.js

```



---



\## Testing



\### Unit Tests



Run calculation logic tests:

```bash

node tests/test\_calculation.js

```



\*\*Expected Output:\*\*

```

=== Testing Stock Calculation Logic ===



Test Case 1 (Stock 0):

Prediction: 70, Stock: 0

Expected Target: 108

Calculated Target (Aim): 108

Replenishment Needed: 108

PASS



Test Case 2 (Stock 50):

Expected Replenishment: 58

Calculated Replenishment: 58

PASS



Test Case 3 (High Stock):

Expected Replenishment: 0

Calculated Replenishment: 0

PASS

```



\### Integration Tests



Test with real database data:

```bash

node tests/test\_stock\_integration.js

```



\### Configuration Tests



Verify custom settings are applied:

```bash

node tests/test\_configurable\_settings.js

```



\### Demand Window Tests



Test different prediction horizons:

```bash

node tests/test\_demand\_window\_simple.js

```



---



\## Installation \& Setup



\### Prerequisites

\- Node.js 14.x or higher

\- MongoDB 4.4+

\- npm or yarn



\### Environment Variables



Create a `.env` file:

```env

MONGO\_URI=mongodb://localhost:27017/freshflow

JWT\_SECRET=your\_secret\_key\_here

PORT=5000

NODE\_ENV=development

```



\### Install Dependencies

```bash

npm install

```



\### Start Server

```bash

npm start

```



Server runs on `http://localhost:5000`



---



\## Production Deployment



\### Docker



```dockerfile

FROM node:14-alpine

WORKDIR /app

COPY package\*.json ./

RUN npm ci --only=production

COPY . .

EXPOSE 5000

CMD \["node", "server.js"]

```



\### Build and Run

```bash

docker build -t stock-flow-api .

docker run -p 5000:5000 --env-file .env stock-flow-api

```



\### Environment Best Practices

\- Use strong JWT secrets (32+ characters)

\- Enable rate limiting for production

\- Set `NODE\_ENV=production`

\- Use HTTPS in production

\- Implement request logging (Morgan, Winston)



---



\## API Limitations \& Notes



\- \*\*Rate Limiting\*\*: 100 requests/hour per user (configurable)

\- \*\*Demand Window Range\*\*: 1-30 days

\- \*\*Lead Time Range\*\*: 0-14 days

\- \*\*Safety Buffer Range\*\*: 0-100%

