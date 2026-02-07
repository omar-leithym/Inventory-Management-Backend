const asyncHandler = require("express-async-handler");
const Sale = require("../models/saleModel");

// @desc    Log a new sale
// @route   POST /api/sales
// @access  Private
const createSale = asyncHandler(async (req, res) => {
    const { menuItemId, addonIds, quantity, price, discount } = req.body;

    if (!menuItemId || !price) {
        res.status(400);
        throw new Error('Please include menu item and price');
    }

    const sale = await Sale.create({
        user: req.user.id,
        menuItem: menuItemId,
        addons: addonIds || [],
        quantity: quantity || 1,
        price,
        discount: discount || 0
    });

    res.status(201).json(sale);
});

// @desc    Get user sales
// @route   GET /api/sales
// @access  Private
const getSales = asyncHandler(async (req, res) => {
    const sales = await Sale.find({ user: req.user.id })
        .populate('menuItem')
        .populate('addons')
        .sort('-createdAt');
    res.status(200).json(sales);
});

// @desc    Get sale by ID
// @route   GET /api/sales/:id
// @access  Private
const getSaleById = asyncHandler(async (req, res) => {
    const sale = await Sale.findById(req.params.id)
        .populate('menuItem')
        .populate('addons');

    if (!sale) {
        res.status(404);
        throw new Error('Sale not found');
    }

    // Check for user
    if (!req.user) {
        res.status(401);
        throw new Error('User not found');
    }

    // Make sure the logged in user matches the sale user
    if (sale.user.toString() !== req.user.id) {
        res.status(401);
        throw new Error('User not authorized');
    }

    res.status(200).json(sale);
});

module.exports = {
    createSale,
    getSales,
    getSaleById
};
