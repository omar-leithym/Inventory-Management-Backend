/**
 * File: saleRoutes.js
 * Description: Route definitions for sales management endpoints.
 * Dependencies: express, saleController, authMiddleware
 * 
 * Defines HTTP routes for creating and retrieving sales transactions.
 */

const express = require('express');
const router = express.Router();
const { createSale, getSales, getSaleById } = require('../controllers/saleController');
const { protect } = require('../middleware/authMiddleware');

router.route('/')
    .get(protect, getSales)
    .post(protect, createSale);

router.route('/:id')
    .get(protect, getSaleById);

module.exports = router;