/**
 * File: stockRoutes.js
 * Description: Route definitions for stock management and recommendations endpoints.
 * Dependencies: express, stockController, authMiddleware
 * 
 * Defines HTTP routes for stock CRUD operations and AI-powered stock recommendations.
 * Note: Specific routes (like /recommendations) must be defined before parameterized routes.
 */

const express = require('express');
const router = express.Router();
const { addStock, getStock, updateStock, deleteStock, getStockRecommendations, getStockById } = require('../controllers/stockController');
const { protect } = require('../middleware/authMiddleware');

// Specific routes first (before parameterized routes)
router.get('/recommendations', protect, getStockRecommendations);

router.route('/')
    .get(protect, getStock)
    .post(protect, addStock);

router.route('/:id')
    .get(protect, getStockById)
    .put(protect, updateStock)
    .delete(protect, deleteStock);

module.exports = router;