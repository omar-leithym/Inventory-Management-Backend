const asyncHandler = require("express-async-handler");
const Stock = require("../models/stockModel");
const MenuItem = require("../models/menuItemModel");
const Addon = require("../models/addonModel");

// @desc    Add item to stock
// @route   POST /api/stock
// @access  Private
const addStock = asyncHandler(async (req, res) => {
    const { itemId, itemType, quantity } = req.body;

    // Validate itemType
    if (itemType !== 'MenuItem' && itemType !== 'Addon') {
        res.status(400);
        throw new Error('Invalid item type. Must be MenuItem or Addon');
    }

    // Check if item exists in the respective collection
    let itemExists;
    if (itemType === 'MenuItem') {
        itemExists = await MenuItem.findById(itemId);
    } else {
        itemExists = await Addon.findById(itemId);
    }

    if (!itemExists) {
        res.status(404);
        throw new Error(`${itemType} not found`);
    }

    // Check if user already has this item in stock
    const stockItem = await Stock.findOne({
        user: req.user.id,
        item: itemId,
        itemType: itemType
    });

    if (stockItem) {
        // Update quantity
        stockItem.quantity += parseInt(quantity || 0);
        await stockItem.save();
        res.status(200).json(stockItem);
    } else {
        // Create new stock entry
        const newStock = await Stock.create({
            user: req.user.id,
            item: itemId,
            itemType: itemType,
            quantity: quantity || 0
        });
        res.status(201).json(newStock);
    }
});

// @desc    Get user stock
// @route   GET /api/stock
// @access  Private
const getStock = asyncHandler(async (req, res) => {
    const stock = await Stock.find({ user: req.user.id })
        .populate('item') // This works because of refPath in model
        .sort('-createdAt');
    res.status(200).json(stock);
});

// @desc    Update stock quantity
// @route   PUT /api/stock/:id
// @access  Private
const updateStock = asyncHandler(async (req, res) => {
    const stock = await Stock.findById(req.params.id);

    if (!stock) {
        res.status(404);
        throw new Error('Stock item not found');
    }

    // Check for user
    if (!req.user) {
        res.status(401);
        throw new Error('User not found');
    }

    // Make sure the logged in user matches the stock user
    if (stock.user.toString() !== req.user.id) {
        res.status(401);
        throw new Error('User not authorized');
    }

    const { quantity } = req.body;

    stock.quantity = quantity;
    await stock.save();

    res.status(200).json(stock);
});

// @desc    Delete stock item
// @route   DELETE /api/stock/:id
// @access  Private
const deleteStock = asyncHandler(async (req, res) => {
    const stock = await Stock.findById(req.params.id);

    if (!stock) {
        res.status(404);
        throw new Error('Stock item not found');
    }

    // Check for user
    if (!req.user) {
        res.status(401);
        throw new Error('User not found');
    }

    // Make sure the logged in user matches the stock user
    if (stock.user.toString() !== req.user.id) {
        res.status(401);
        throw new Error('User not authorized');
    }

    await stock.deleteOne();

    res.status(200).json({ id: req.params.id });
});

module.exports = {
    addStock,
    getStock,
    updateStock,
    deleteStock
};
