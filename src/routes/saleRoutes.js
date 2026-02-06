const express = require('express');
const router = express.Router();
const { createSale, getSales } = require('../controllers/saleController');
const { protect } = require('../middleware/authMiddleware');

router.route('/')
    .get(protect, getSales)
    .post(protect, createSale);

module.exports = router;
