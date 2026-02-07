# Inventory Management Frontend Documentation

This document provides a comprehensive overview of the Frontend application, its architecture, technical stack, and integration patterns.

---

## 🚀 Technical Stack

The frontend is built as a modern Single Page Application (SPA) focusing on performance, scalability, and a premium UI/UX.

### Core Technologies
- **Framework:** [React 18](https://reactjs.org/)
- **Build Tool:** [Vite](https://vitejs.dev/) - Lightning-fast HMR and optimized builds.
- **UI Component Library:** [Material UI (MUI) v7+](https://mui.com/) - Using Emotion for CSS-in-JS styling.
- **Routing:** [React Router v7](https://reactrouter.com/) - Handling navigation and protected routes.
- **Charts:** [Recharts](https://recharts.org/) - For data visualization and KPI dashboards.
- **API Client:** [Axios](https://axios-http.com/) - For handling HTTP requests to the backend services.

---

## 📂 Project Structure

The project follows a modular directory structure for scalability:

- `src/components/`: Reusable UI components (Buttons, Cards, Modals).
- `src/pages/`: Main views (Dashboard, Auth, Inventory, Settings).
- `src/services/`: API client configurations and endpoint definitions.
- `src/hooks/`: Custom React hooks for shared logic.
- `src/context/`: Global state management (Auth, Theme).
- `src/utils/`: Helper functions and formatters.
- `src/theme.js`: Centralized MUI theme configuration.

---

## 🛠️ Getting Started

### Prerequisites
- **Node.js:** v16.x or higher
- **npm:** v8.x or higher

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd Frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

The application will be available at `http://localhost:3001`.
---

## 🛣️ Routing Architecture

The application uses **React Router v7** to handle navigation. Routes are defined centrally in [src/routes.jsx](cci:7://file:///d:/Inventory-Management-Backend/Frontend/src/routes.jsx:0:0-0:0).

### Public Routes
- `/login`: User authentication gateway.
- `/register`: Account creation.

### Protected Routes (Require Authentication)
- `/dashboard`: High-level metrics, KPI cards, and sales charts.
- `/inventory`: Inventory management table with restock alerts.
- `/recommendations`: AI-driven discount and stock suggestions.
- `/settings`: Global application variables and user profile.

---

## 🔐 State Management (Context API)

We use the React Context API for global state to avoid "prop drilling."

### AuthContext
Located in `src/context/AuthContext.jsx`, this provider manages:
- **User State:** Persists login status across sessions.
- **JWT Handling:** Automatically attaches tokens to authenticated API requests.
- **Permission Guards:** Redirects unauthenticated users to the `/login` page.

### Theme Configuration
Located in [src/theme.js](cci:7://file:///d:/Inventory-Management-Backend/Frontend/src/theme.js:0:0-0:0), the MUI theme is customized for a "premium" aesthetic:
- **Palette:** Custom dark/light mode support with professional accent colors.
- **Typography:** Custom font weights and sizes for better readability.
- **Components:** Global overrides for standardized button and card styling.

---

## 📡 API Integration & Services

The frontend communicates with the backend using **Axios**. All API logic is encapsulated in the `src/services/` directory to maintain clean separation of concerns.

### Base Configuration (`src/services/api.js`)
- **Centralized Instance:** A pre-configured Axios instance with a common `baseURL`.
- **Interceptors:** A request interceptor automatically adds the `Authorization: Bearer <token>` header to all outgoing requests if a user is logged in.
- **Error Handling:** Centralized handling for common HTTP errors (e.g., redirecting to login on 401s).

### Key Services
- **Auth Service (`authService.js`):** Handles login, registration, and logout persistence.
- **Forecast Service (`forecastService.js`):** Interfaces with the Python Demand Prediction API to fetch future inventory projections.
- **Inventory Service (`inventoryService.js`):** Manages CRUD operations for stock items, categories, and restock alerts.
- **Promotion Service (`promotionService.js`):** Fetches AI-recommended discounts for clearing slow-moving inventory based on the prediction model.

### Example Usage in Components
```javascript
import { inventoryService } from '../services/inventoryService';

const loadInventory = async () => {
  try {
    const data = await inventoryService.getAllItems();
    setItems(data);
  } catch (error) {
    console.error("Critical: Failed to load inventory data", error);
  }
};

---

## 🧠 Advanced Logic & Utilities

### Custom React Hooks (`src/hooks/`)
We use custom hooks to encapsulate complex state transitions and side effects:
- **useAuth:** A concise wrapper around `AuthContext` to access user details and login status.
- **useDashboard:** Orchestrates the fetching of all dashboard metrics (KPIs, charts, recent orders) and handles loading/error states for the main view.

### Application Utilities (`src/utils/`)
Consistency in data presentation is managed through centralized helper functions:
- **formatters.js:** Contains logic for currency formatting (e.g., EGP/USD), date parsing, and decimal precision for growth percentages.
- **constants.js:** Stores application-wide static data, such as API endpoint configurations, status code mappings, and chart color palettes.

---

## ⚡ Performance & Optimization

- **Component Memoization:** Heavy charts and data tables use `React.memo` to prevent unnecessary re-renders during global state updates.
- **Lazy Loading:** Routes are dynamically imported (where applicable) to reduce the initial bundle size.
- **Efficient API Fetching:** Data is cached locally where possible to minimize redundant network requests.

---

## 🚀 Build & Deployment

The application is optimized for production using **Vite**:

1. **Production Build:**
   ```bash
   npm run build