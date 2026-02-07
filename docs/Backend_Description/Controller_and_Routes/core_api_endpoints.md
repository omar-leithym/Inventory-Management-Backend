# Core API Documentation

This document outlines the API endpoints for Addons, Menu Items, Recommendations, and Analytics.

## Base URL
All endpoints are prefixed with `/api` (and typically require a Bearer token in the `Authorization` header).

---

## 1. Get All Addons

Retrieves a list of all available addon items.

- **URL:** `/api/addons`
- **Method:** `GET`
- **Access:** Private

### Parameters

| Type | Name | Required | Description |
| :--- | :--- | :--- | :--- |
| **Query** | `search` | No | A string to filter addons by title using a case-insensitive regex match. |

### Response Example (Success)

```json
[
  {
    "_id": "65c4ecb9f8d2e8b1a8c9e4a1",
    "title": "Extra Cheese",
    "price": 1.50
  },
  {
    "_id": "65c4ecb9f8d2e8b1a8c9e4a2",
    "title": "Bacon Strip",
    "price": 2.00
  }
]
```

### React Example

```jsx
import axios from 'axios';

const fetchAddons = async (token, searchTerm = '') => {
  try {
    const config = {
      headers: { Authorization: `Bearer ${token}` }
    };
    
    // Pass search as a query parameter if it exists
    const url = searchTerm ? `/api/addons?search=${searchTerm}` : '/api/addons';
    
    const { data } = await axios.get(url, config);
    return data;
  } catch (error) {
    console.error('Error fetching addons:', error);
  }
};
```

---

## 2. Get All Menu Items

Retrieves a list of all main menu items.

- **URL:** `/api/menu-items`
- **Method:** `GET`
- **Access:** Private

### Parameters

| Type | Name | Required | Description |
| :--- | :--- | :--- | :--- |
| **Query** | `search` | No | A string to filter menu items by title using a case-insensitive regex match. |

### Response Example (Success)

```json
[
  {
    "_id": "65c4ecb9f8d2e8b1a8c9e4b1",
    "title": "Classic Burger",
    "price": 8.99
  }
]
```

### React Example

```jsx
import { useEffect, useState } from 'react';
import axios from 'axios';

const MenuList = ({ token }) => {
  const [items, setItems] = useState([]);

  useEffect(() => {
    const getItems = async () => {
      try {
        const { data } = await axios.get('/api/menu-items', {
          headers: { Authorization: `Bearer ${token}` }
        });
        setItems(data);
      } catch (err) {
        console.error(err);
      }
    };
    if (token) getItems();
  }, [token]);

  return (
    <ul>
      {items.map(item => <li key={item._id}>{item.title}</li>)}
    </ul>
  );
};
```

---

## 3. Get Prioritized Recommendations

Generates a prioritized list of items to restock based on forecasted demand, current stock levels, and available budget.

- **URL:** `/api/recommendations/prioritize`
- **Method:** `GET`
- **Access:** Private

### Parameters

| Type | Name | Required | Description |
| :--- | :--- | :--- | :--- |
| **Query** | `budget` | No | Maximum spending limit. If provided, this overrides the user's saved budget. If neither is present, it defaults to Infinity (Unlimited). |

### Response Example (Success)

```json
{
  "budget": 500,
  "remainingBudget": 45.50,
  "totalRecommendedCost": 454.50,
  "recommendedItems": [
    {
      "item": {
        "_id": "65c4ecb9f8d2e8b1a8c9e4b1",
        "title": "Classic Burger",
        "type": "MenuItem",
        "price": 8.99
      },
      "currentStock": 10,
      "predictedDemand": 50,
      "neededQuantity": 40,
      "priorityScore": 40,
      "recommendedQuantity": 40,
      "recommendedCost": 359.60,
      "notes": "Full fulfillment"
    }
  ]
}
```

### React Example

```jsx
const getRecommendations = async (token, customBudget) => {
  const config = {
    headers: { Authorization: `Bearer ${token}` },
    params: {}
  };

  if (customBudget) {
    config.params.budget = customBudget;
  }
  
  const { data } = await axios.get('/api/recommendations/prioritize', config);
  console.log('Recommendations:', data.recommendedItems);
};
```

---

## 4. Get Forecast Accuracy (MAPE)

Calculates the Mean Absolute Percentage Error (MAPE) for a specific item's forecast over a given period.

- **URL:** `/api/analytics/accuracy/:itemId`
- **Method:** `GET`
- **Access:** Private

### Parameters

| Type | Name | Required | Description |
| :--- | :--- | :--- | :--- |
| **Path** | `itemId` | Yes | The MongoDB ObjectId of the Menu Item. |
| **Query** | `startDate` | No | Start date of the evaluation period (YYYY-MM-DD). Defaults to 30 days ago. |
| **Query** | `endDate` | No | End date of the evaluation period (YYYY-MM-DD). Defaults to today. |

### Response Example (Success)

```json
{
  "success": true,
  "item": "Classic Burger",
  "period": {
    "start": "2023-12-01",
    "end": "2023-12-31"
  },
  "mape": 12.5,
  "accuracy": 87.5
}
```

### React Example

```jsx
const checkAccuracy = async (token, itemId) => {
  const startDate = '2024-01-01';
  const endDate = '2024-01-31';

  try {
    const { data } = await axios.get(`/api/analytics/accuracy/${itemId}`, {
      params: { startDate, endDate },
      headers: { Authorization: `Bearer ${token}` }
    });

    console.log(`Forecast Accuracy for ${data.item}:`, data);
  } catch (err) {
    console.error(err);
  }
};
```
