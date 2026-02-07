const express = require('express');
const router = express.Router();
const { addStock, getStock, updateStock, deleteStock, getStockRecommendations } = require('../controllers/stockController');
const { protect } = require('../middleware/authMiddleware');

// Metrics/Recommendations routes (Specific routes first)
router.get('/recommendations', protect, getStockRecommendations);

router.route('/')
    .get(protect, getStock)
    .post(protect, addStock);

router.route('/:id')
    .put(protect, updateStock)
    .delete(protect, deleteStock);

module.exports = router;
