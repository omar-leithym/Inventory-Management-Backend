const express = require("express");
const router = express.Router();
const { getMenuItems } = require("../controllers/menuItemController");
const { protect } = require("../middleware/authMiddleware");

router.get("/", protect, getMenuItems);

module.exports = router;
