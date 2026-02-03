const express = require("express");
const router = express.Router();
const {
    registerUser,
    loginUser,
    getUser,
    updateUser,
    searchUsers
} = require("../controllers/userController");
const { protect } = require("../middleware/authMiddleware");

router.post("/register", registerUser);
router.post("/login", loginUser);
router.get("/getuser", protect, getUser);
router.patch("/updateuser/:id", protect, updateUser);
router.get("/search", protect, searchUsers);

module.exports = router;
