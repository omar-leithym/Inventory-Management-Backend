const asyncHandler = require("express-async-handler");
const Restock = require("../models/restockModel");
const Stock = require("../models/stockModel");

// @desc    Log a new restock (add to inventory)
// @route   POST /api/restock
// @access  Private
const createRestock = asyncHandler(async (req, res) => {
    const { menuItemId, addonIds, quantity, price } = req.body;

    if (!menuItemId || !price) {
        res.status(400);
        throw new Error('Please include menu item and price');
    }

    const restock = await Restock.create({
        user: req.user.id,
        menuItem: menuItemId,
        addons: addonIds || [],
        quantity: quantity || 1,
        pricePerUnit: price
    });

    // Auto-add stock for MenuItem
    let menuItemStock = await Stock.findOne({
        user: req.user.id,
        item: menuItemId,
        itemType: 'MenuItem'
    });

    if (menuItemStock) {
        menuItemStock.quantity += (quantity || 1);
        await menuItemStock.save();
        console.log(`✅ Added ${quantity || 1} to MenuItem ${menuItemId}. New quantity: ${menuItemStock.quantity}`);
    } else {
        // Create new stock entry if it doesn't exist
        await Stock.create({
            user: req.user.id,
            item: menuItemId,
            itemType: 'MenuItem',
            quantity: quantity || 1
        });
        console.log(`✅ Created new stock entry for MenuItem ${menuItemId} with quantity ${quantity || 1}`);
    }

    // Auto-add stock for each Addon
    if (addonIds && addonIds.length > 0) {
        for (const addonId of addonIds) {
            let addonStock = await Stock.findOne({
                user: req.user.id,
                item: addonId,
                itemType: 'Addon'
            });

            if (addonStock) {
                addonStock.quantity += (quantity || 1);
                await addonStock.save();
                console.log(`✅ Added ${quantity || 1} to Addon ${addonId}. New quantity: ${addonStock.quantity}`);
            } else {
                // Create new stock entry if it doesn't exist
                await Stock.create({
                    user: req.user.id,
                    item: addonId,
                    itemType: 'Addon',
                    quantity: quantity || 1
                });
                console.log(`✅ Created new stock entry for Addon ${addonId} with quantity ${quantity || 1}`);
            }
        }
    }

    res.status(201).json(restock);
});

// @desc    Get user restocks
// @route   GET /api/restock
// @access  Private
const getRestocks = asyncHandler(async (req, res) => {
    const restocks = await Restock.find({ user: req.user.id })
        .populate('menuItem')
        .populate('addons')
        .sort('-createdAt');
    res.status(200).json(restocks);
});

// @desc    Get restock by ID
// @route   GET /api/restock/:id
// @access  Private
const getRestockById = asyncHandler(async (req, res) => {
    const restock = await Restock.findById(req.params.id)
        .populate('menuItem')
        .populate('addons');

    if (!restock) {
        res.status(404);
        throw new Error('Restock transaction not found');
    }

    // Check for user
    if (!req.user) {
        res.status(401);
        throw new Error('User not found');
    }

    // Make sure the logged in user matches the restock user
    if (restock.user.toString() !== req.user.id) {
        res.status(401);
        throw new Error('User not authorized');
    }

    res.status(200).json(restock);
});

module.exports = {
    createRestock,
    getRestocks,
    getRestockById
};
