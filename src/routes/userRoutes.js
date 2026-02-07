/**
 * File: userRoutes.js
 * Description: Route definitions for user authentication and profile management endpoints.
 * Dependencies: express, userController, authMiddleware
 * 
 * Defines HTTP routes for user registration, login, profile updates, search,
 * and settings management.
 */

const express = require("express");
const router = express.Router();
const {
    registerUser,
    loginUser,
    getUser,
    updateUser,
    searchUsers,
    updateSettings,
    getSettings
} = require("../controllers/userController");
const { protect } = require("../middleware/authMiddleware");

router.post("/register", registerUser);
router.post("/login", loginUser);
router.get("/getuser", protect, getUser);
router.patch("/updateuser/:id", protect, updateUser);
router.get("/search", protect, searchUsers);
router.put("/settings", protect, updateSettings);
router.get("/settings", protect, getSettings);

module.exports = router;