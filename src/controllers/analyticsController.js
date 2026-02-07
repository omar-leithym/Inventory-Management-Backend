/**
 * File: analyticsController.js
 * Description: Controller for analytics and forecasting accuracy (MAPE).
 * Dependencies: express-async-handler, MAPECalculator, menuItemModel
 * Author: Sample Team
 */

const asyncHandler = require("express-async-handler");
const MAPECalculator = require("../services/MAPECalculator");
const MenuItem = require("../models/menuItemModel");

/**
 * Get forecast accuracy (MAPE) for a specific menu item.
 * 
 * Calculates the Mean Absolute Percentage Error for an item over a specified date range.
 * Defaults to the last 30 days if no range is provided.
 * 
 * Request Parameters:
 *     itemId (string): The ID of the menu item.
 * 
 * Query Params:
 *     startDate (string): Start date (YYYY-MM-DD).
 *     endDate (string): End date (YYYY-MM-DD).
 * 
 * Returns:
 *     Object: JSON object containing MAPE analysis.
 * 
 * Example Response:
 *     {
 *         "success": true,
 *         "item": "Burger",
 *         "period": { "start": "2023-10-01", "end": "2023-10-31" },
 *         "mape": 12.5,
 *         "accuracy": 87.5
 *     }
 * 
 * @route   GET /api/analytics/accuracy/:itemId
 * @access  Private
 */
const getForecastAccuracy = asyncHandler(async (req, res) => {
    const { itemId } = req.params;
    let { startDate, endDate } = req.query;

    // Default to last 30 days if no range provided
    if (!startDate || !endDate) {
        endDate = new Date();
        startDate = new Date();
        startDate.setDate(endDate.getDate() - 30);
    } else {
        startDate = new Date(startDate);
        endDate = new Date(endDate);
    }

    // Validate Item Existence
    const item = await MenuItem.findById(itemId);
    if (!item) {
        res.status(404);
        throw new Error('Menu item not found');
    }

    const calculator = new MAPECalculator();

    // Calculate MAPE using the service
    // Pass user ID from the authenticated request
    const result = await calculator.calculateItemMAPE(
        itemId,
        req.user.id,
        startDate,
        endDate
    );

    res.status(200).json({
        success: true,
        item: item.title,
        period: {
            start: startDate.toISOString().split('T')[0],
            end: endDate.toISOString().split('T')[0]
        },
        ...result
    });
});

module.exports = {
    getForecastAccuracy
};
