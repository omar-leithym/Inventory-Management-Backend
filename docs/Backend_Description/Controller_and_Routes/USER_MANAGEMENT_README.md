# User Management API

User authentication, profile management, and settings configuration service.

---

## Overview

The User Management API provides endpoints for user registration, authentication, profile updates, and configurable settings for inventory management preferences.

---

## Base URL

- Local: `http://localhost:5000/api/users`
- Production: `https://your-domain.com/api/users`

---

## Authentication

Most endpoints require JWT authentication via the `Authorization` header:

```http
Authorization: Bearer <your_jwt_token>
```

Obtain a token via the `/register` or `/login` endpoints.

---

## Endpoints

### `POST /api/users/register`

Register a new user account.

**Authentication:** None required

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "firstName": "John",
  "lastName": "Doe",
  "phone": "+1-555-123-4567"
}
```

**Required Fields:**
- `email` *(string)*: Valid email address
- `password` *(string)*: Must meet security criteria
- `firstName` *(string)*: User's first name
- `lastName` *(string)*: User's last name
- `phone` *(string)*: Valid international phone number

**Password Requirements:**
- Minimum length enforced by validation schema
- Must meet complexity requirements

**Response (201 Created):**
```json
{
  "id": "507f191e810c19729de860ea",
  "email": "user@example.com",
  "firstName": "John",
  "lastName": "Doe",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Response (400 Bad Request):**
```json
{
  "message": "Email exists"
}
```

```json
{
  "message": "Password doesn't meet criteria"
}
```

```json
{
  "message": "Invalid phone number"
}
```

```json
{
  "message": "Invalid email address"
}
```

---

### `POST /api/users/login`

Authenticate user and receive JWT token.

**Authentication:** None required

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Required Fields:**
- `email` *(string)*: Registered email address
- `password` *(string)*: User password

**Response (201 Created):**
```json
{
  "id": "507f191e810c19729de860ea",
  "email": "user@example.com",
  "firstName": "John",
  "lastName": "Doe",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Response (400 Bad Request):**
```json
{
  "message": "Invalid credentials"
}
```

```json
{
  "message": "Please add email and password"
}
```

---

### `GET /api/users/getuser`

Retrieve authenticated user's profile information.

**Authentication:** Required

**Response (200 OK):**
```json
{
  "id": "507f191e810c19729de860ea",
  "email": "user@example.com",
  "firstName": "John",
  "lastName": "Doe"
}
```

**Error Response (404 Not Found):**
```json
{
  "message": "User not found"
}
```

---

### `PATCH /api/users/updateuser/:id`

Update user profile information.

**Authentication:** Required

**URL Parameters:**
- `id` *(string)*: User ID to update

**Request Body:**
```json
{
  "email": "newemail@example.com",
  "firstName": "Jane",
  "lastName": "Smith"
}
```

**Optional Fields:**
- `email` *(string)*: New email address (must be unique)
- `firstName` *(string)*: Updated first name
- `lastName` *(string)*: Updated last name

**Response (200 OK):**
```json
{
  "id": "507f191e810c19729de860ea",
  "firstName": "Jane",
  "lastName": "Smith",
  "email": "newemail@example.com",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Response (400 Bad Request):**
```json
{
  "message": "Email already exists"
}
```

**Error Response (404 Not Found):**
```json
{
  "message": "User not found"
}
```

---

### `GET /api/users/search`

Search for users by email or phone.

**Authentication:** Required

**Query Parameters:**
- `query` *(string, required)*: Search term (email or phone)

**Example:**
```http
GET /api/users/search?query=john
```

**Response (200 OK):**
```json
[
  {
    "_id": "507f191e810c19729de860ea",
    "firstName": "John",
    "lastName": "Doe",
    "email": "john@example.com"
  },
  {
    "_id": "507f191e810c19729de860eb",
    "firstName": "Johnny",
    "lastName": "Smith",
    "email": "johnny@example.com"
  }
]
```

**Notes:**
- Case-insensitive search
- Excludes the authenticated user from results
- Searches both email and phone fields

**Error Response (400 Bad Request):**
```json
{
  "message": "Search query is required"
}
```

---

### `PUT /api/users/settings`

Update user's inventory management settings.

**Authentication:** Required

**Request Body:**
```json
{
  "demandWindow": 7,
  "leadTime": 2,
  "safetyStockBuffer": 20,
  "lowStockThreshold": 20,
  "budgetLimit": 5000
}
```

**Optional Fields:**
- `demandWindow` *(integer)*: Days to predict demand (1-30)
- `leadTime` *(integer)*: Supplier delivery time in days (0-14)
- `safetyStockBuffer` *(integer)*: Safety stock percentage (0-100)
- `lowStockThreshold` *(integer)*: % threshold for critical alerts (0-50)
- `budgetLimit` *(number)*: Monthly budget cap

**Parameter Details:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `demandWindow` | Integer | 7 | Prediction horizon in days |
| `leadTime` | Integer | 2 | Restock lead time |
| `safetyStockBuffer` | Integer | 20 | Safety stock % (20 = 20%) |
| `lowStockThreshold` | Integer | 20 | Critical alert threshold % |
| `budgetLimit` | Number | - | Optional spending limit |

**Response (200 OK):**
```json
{
  "demandWindow": 7,
  "leadTime": 2,
  "safetyStockBuffer": 20,
  "lowStockThreshold": 20,
  "budgetLimit": 5000
}
```

**Error Response (404 Not Found):**
```json
{
  "message": "User not found"
}
```

**Notes:**
- Settings are stored in nested `settings` object
- `budgetLimit` also syncs to top-level `budget` field
- Partial updates supported (send only fields to change)

---

### `GET /api/users/settings`

Retrieve user's current settings.

**Authentication:** Required

**Response (200 OK):**
```json
{
  "demandWindow": 7,
  "leadTime": 2,
  "safetyStockBuffer": 20,
  "lowStockThreshold": 20,
  "budgetLimit": 5000
}
```

**Default Response (if no settings configured):**
```json
{
  "demandWindow": 7
}
```

**Error Response (404 Not Found):**
```json
{
  "message": "User not found"
}
```

---

## Error Responses

### 400 Bad Request
Invalid input or validation failure:
```json
{
  "message": "Please fill in all fields"
}
```

### 401 Unauthorized
Missing or invalid authentication token:
```json
{
  "message": "Not authorized, no token"
}
```

### 404 Not Found
Resource not found:
```json
{
  "message": "User not found"
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

const API_BASE = 'http://localhost:5000/api/users';
let authToken = null;

const client = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' }
});

// Add auth token to requests
client.interceptors.request.use(config => {
  if (authToken) {
    config.headers.Authorization = `Bearer ${authToken}`;
  }
  return config;
});

// Register new user
async function register(userData) {
  const res = await axios.post(`${API_BASE}/register`, userData);
  authToken = res.data.token;
  return res.data;
}

// Login
async function login(email, password) {
  const res = await axios.post(`${API_BASE}/login`, {
    email,
    password
  });
  authToken = res.data.token;
  return res.data;
}

// Get current user
async function getUser() {
  const res = await client.get('/getuser');
  return res.data;
}

// Update user profile
async function updateUser(userId, updates) {
  const res = await client.patch(`/updateuser/${userId}`, updates);
  return res.data;
}

// Search users
async function searchUsers(query) {
  const res = await client.get('/search', {
    params: { query }
  });
  return res.data;
}

// Update settings
async function updateSettings(settings) {
  const res = await client.put('/settings', settings);
  return res.data;
}

// Get settings
async function getSettings() {
  const res = await client.get('/settings');
  return res.data;
}

// Example usage
(async () => {
  try {
    // Register
    const user = await register({
      email: 'test@example.com',
      password: 'SecurePass123!',
      firstName: 'Test',
      lastName: 'User',
      phone: '+1-555-123-4567'
    });
    console.log('✅ Registered:', user.email);

    // Update settings
    await updateSettings({
      demandWindow: 14,
      leadTime: 3,
      safetyStockBuffer: 25,
      lowStockThreshold: 15
    });
    console.log('✅ Settings updated');

    // Get settings
    const settings = await getSettings();
    console.log('📊 Current settings:', settings);

    // Search users
    const results = await searchUsers('test');
    console.log('🔍 Search results:', results.length);

  } catch (error) {
    if (error.response) {
      console.error(`HTTP ${error.response.status}:`, error.response.data);
    } else {
      console.error('Error:', error.message);
    }
  }
})();
```

---

## Database Schema

```javascript
const userSchema = new Schema({
  email: {
    type: String,
    required: true,
    unique: true,
    lowercase: true,
    trim: true
  },
  password: {
    type: String,
    required: true
  },
  firstName: {
    type: String,
    required: true,
    trim: true
  },
  lastName: {
    type: String,
    required: true,
    trim: true
  },
  phone: {
    type: String,
    required: true
  },
  settings: {
    demandWindow: {
      type: Number,
      default: 7
    },
    leadTime: {
      type: Number,
      default: 2
    },
    safetyStockBuffer: {
      type: Number,
      default: 20
    },
    lowStockThreshold: {
      type: Number,
      default: 20
    },
    budgetLimit: Number
  },
  budget: Number
}, {
  timestamps: true
});
```

---

## Security Notes

- Passwords are hashed using bcrypt with salt rounds
- JWT tokens expire after 30 days
- Email validation uses `validator` library
- Phone validation uses `libphonenumber-js`
- Password strength enforced via `password-schema`

---

## Environment Variables

```env
JWT_SECRET=your_secret_key_here_min_32_characters
MONGO_URI=mongodb://localhost:27017/freshflow
PORT=5000
```

---

## Installation & Setup

### Prerequisites
- Node.js 14.x+
- MongoDB 4.4+

### Install Dependencies
```bash
npm install express express-async-handler jsonwebtoken bcrypt validator libphonenumber-js
```

### Start Server
```bash
npm start
```

---

## License

MIT License
