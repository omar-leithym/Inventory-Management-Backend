const express = require('express');
const router = express.Router();
const { createRestock, getRestocks, getRestockById } = require('../controllers/restockController');
const { protect } = require('../middleware/authMiddleware');

router.route('/')
    .get(protect, getRestocks)
    .post(protect, createRestock);

router.route('/:id')
    .get(protect, getRestockById);

module.exports = router;
