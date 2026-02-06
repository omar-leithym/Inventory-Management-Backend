const express = require("express");
const router = express.Router();
const { getAddons } = require("../controllers/addonController");
const { protect } = require("../middleware/authMiddleware");

router.get("/", protect, getAddons);

module.exports = router;
