const express = require('express');
const router = express.Router();
const { getForecastAccuracy } = require('../controllers/analyticsController');
const { protect } = require('../middleware/authMiddleware');

router.get('/accuracy/:itemId', protect, getForecastAccuracy);

module.exports = router;
