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
