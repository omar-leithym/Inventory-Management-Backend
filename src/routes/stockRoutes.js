const express = require('express');
const router = express.Router();
const { addStock, getStock, updateStock, deleteStock } = require('../controllers/stockController');
const { protect } = require('../middleware/authMiddleware');

router.route('/')
    .get(protect, getStock)
    .post(protect, addStock);

router.route('/:id')
    .put(protect, updateStock)
    .delete(protect, deleteStock);

module.exports = router;
