const express = require("express");
const router = express.Router();
const { getPrioritizedItems } = require("../controllers/recommendationController");
const { protect } = require("../middleware/authMiddleware");

router.get("/prioritize", protect, getPrioritizedItems);

module.exports = router;
