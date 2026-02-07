/**
 * File: saleController.js
 * Description: Controller for managing sales transactions and stock updates.
 * Dependencies: express-async-handler, saleModel, stockModel
 * 
 * This controller handles sale creation, retrieval, and automatic stock deduction
 * for menu items and addons.
 */

const asyncHandler = require("express-async-handler");
const Sale = require("../models/saleModel");
const Stock = require("../models/stockModel");

/**
 * Log a new sale transaction.
 * 
 * Creates a sale record and automatically deducts inventory for the
 * menu item and any associated addons.
 * 
 * @route   POST /api/sales
 * @access  Private
 */
const createSale = asyncHandler(async (req, res) => {
    const { menuItemId, addonIds, quantity, pricePerUnit, discount } = req.body;

    if (!menuItemId || !pricePerUnit) {
        res.status(400);
        throw new Error('Please include menu item and price per unit');
    }

    const sale = await Sale.create({
        user: req.user.id,
        menuItem: menuItemId,
        addons: addonIds || [],
        quantity: quantity || 1,
        pricePerUnit,
        discount: discount || 0
    });

    // Auto-deduct stock for MenuItem
    const menuItemStock = await Stock.findOne({
        user: req.user.id,
        item: menuItemId,
        itemType: 'MenuItem'
    });

    if (menuItemStock) {
        menuItemStock.quantity -= (quantity || 1);
        await menuItemStock.save();
        console.log(`✅ Deducted ${quantity || 1} from MenuItem ${menuItemId}. New quantity: ${menuItemStock.quantity}`);
    } else {
        console.log(`⚠️  No stock entry found for MenuItem ${menuItemId}`);
    }

    // Auto-deduct stock for each Addon
    if (addonIds && addonIds.length > 0) {
        for (const addonId of addonIds) {
            const addonStock = await Stock.findOne({
                user: req.user.id,
                item: addonId,
                itemType: 'Addon'
            });

            if (addonStock) {
                addonStock.quantity -= (quantity || 1);
                await addonStock.save();
                console.log(`✅ Deducted ${quantity || 1} from Addon ${addonId}. New quantity: ${addonStock.quantity}`);
            } else {
                console.log(`⚠️  No stock entry found for Addon ${addonId}`);
            }
        }
    }

    res.status(201).json(sale);
});

/**
 * Get all sales for the authenticated user.
 * 
 * Returns sales sorted by creation date (newest first) with populated
 * menu item and addon details.
 * 
 * @route   GET /api/sales
 * @access  Private
 */
const getSales = asyncHandler(async (req, res) => {
    const sales = await Sale.find({ user: req.user.id })
        .populate('menuItem')
        .populate('addons')
        .sort('-createdAt');
    res.status(200).json(sales);
});

/**
 * Get a specific sale by ID.
 * 
 * Retrieves sale details and verifies user authorization.
 * 
 * @route   GET /api/sales/:id
 * @access  Private
 */
const getSaleById = asyncHandler(async (req, res) => {
    const sale = await Sale.findById(req.params.id)
        .populate('menuItem')
        .populate('addons');

    if (!sale) {
        res.status(404);
        throw new Error('Sale not found');
    }

    if (!req.user) {
        res.status(401);
        throw new Error('User not found');
    }

    // Verify user owns this sale
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