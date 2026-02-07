# Middleware Documentation

This document explains the purpose, implementation, and security features of the backend middleware.

## 1. Authentication Middleware (`authMiddleware.js`)

**Path:** `src/middleware/authMiddleware.js`

### Purpose
The `protect` middleware is designed to secure API endpoints by ensuring that only authenticated users can access them. It verifies JSON Web Tokens (JWT) sent in the request headers.

### How it Works
1.  **Token Extraction**: It looks for the `Authorization` header in the incoming request. The header is expected to start with `Bearer`.
2.  **Verification**: It extracts the token string and uses the `jsonwebtoken` library to verify its validity against the `JWT_SECRET` environment variable.
3.  **User Retrieval**: Upon successful verification, it decodes the token to get the user's ID. It then fetches the user details from the database (excluding the password) and attaches the user object to the `req` object as `req.user`.
4.  **Error Handling**: If no token is provided, or if the token is invalid/expired, it throws an error ("Not authorized") and sets the response status to 401.

### Security Features
*   **JWT Verification**: Ensures that the token was issued by the server and has not been tampered with.
*   **RBAC Foundation**: By attaching the full user object to the request, downstream controllers can easily implement Role-Based Access Control (RBAC) (e.g., checking `req.user.isAdmin`).
*   **Stateless Authentication**: Does not require server-side session storage, making the application scalable.
*   **Password Exclusion**: When fetching the user, the password field is explicitly excluded (`.select('-password')`) to prevent accidental leakage of sensitive credentials.

---

## 2. Error Handling Middleware (`errorMiddleware.js`)

**Path:** `src/middleware/errorMiddleware.js`

### Purpose
The `errorHandler` middleware provides a consistent structure for handling errors across the entire application. It overrides the default Express error handler.

### How it Works
1.  **Status Code**: It sets the HTTP status code. If the response status code is already set (e.g., to 400 or 401), it uses that; otherwise, it defaults to 500 (Internal Server Error).
2.  **Response Format**: It sends a JSON response containing the `message` from the error object and, in non-production environments, the `stack` trace.

### Security Features
*   **Information Hiding**: In production environments (`NODE_ENV === 'production'`), the stack trace is set to `null`. This is a critical security practice because stack traces can reveal internal file paths, library versions, and logic flaws that attackers could exploit.
*   **Consistent Response**: Ensures that API clients always receive a predictable error format, preventing unexpected crashes or data leaks from detailed default error pages.
