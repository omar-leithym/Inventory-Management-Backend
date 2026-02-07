/**
 * File: MAPECalculator.js
 * Description: Service for calculating forecast accuracy using MAPE (Mean Absolute Percentage Error).
 * Dependencies: mongoose, ForecastModel, saleModel
 * 
 * This service evaluates the accuracy of demand forecasts by comparing predicted
 * quantities against actual sales data over specified time periods.
 */

const mongoose = require('mongoose');
const Forecast = require('../models/ForecastModel');
const Sale = require('../models/saleModel');

class MAPECalculator {

    /**
     * Calculate MAPE for a specific item over a date range.
     * 
     * Formula: MAPE = (1/n) * Σ |Actual - Predicted| / Actual
     * 
     * This method fetches forecasts and actual sales, then computes the mean
     * absolute percentage error to measure prediction accuracy.
     * 
     * @param {string} itemId - Menu Item ID
     * @param {string} userId - User ID
     * @param {Date} startDate - Start of analysis period
     * @param {Date} endDate - End of analysis period
     * @returns {Object} MAPE result with accuracy metrics
     */
    async calculateItemMAPE(itemId, userId, startDate, endDate) {
        // Fetch Forecasts
        const forecasts = await Forecast.find({
            user: userId,
            menuItem: itemId,
            targetDate: { $gte: startDate, $lte: endDate }
        });

        if (!forecasts.length) return { mape: 0, message: "No forecasts found" };

        // Fetch Actual Sales (Aggregated by Day)
        const sales = await Sale.aggregate([
            {
                $match: {
                    user: new mongoose.Types.ObjectId(userId),
                    menuItem: new mongoose.Types.ObjectId(itemId),
                    createdAt: { $gte: startDate, $lte: endDate }
                }
            },
            {
                $group: {
                    _id: { $dateToString: { format: "%Y-%m-%d", date: "$createdAt" } },
                    totalQuantity: { $sum: "$quantity" }
                }
            }
        ]);

        // Map sales to dictionary for easy lookup: { "2023-10-27": 15 }
        const salesMap = {};
        sales.forEach(s => {
            salesMap[s._id] = s.totalQuantity;
        });

        // Calculate Error
        let totalErrorPercent = 0;
        let count = 0;

        for (const forecast of forecasts) {
            const dateKey = forecast.targetDate.toISOString().split('T')[0];
            const actual = salesMap[dateKey] || 0;
            const predicted = forecast.predictedQuantity;

            // Handle edge case: Actual is 0
            if (actual === 0) {
                // If predicted is also 0, perfect accuracy (0% error)
                if (predicted === 0) {
                    count++;
                    continue;
                }
                // If predicted > 0 but actual 0, count as 100% error
                else {
                    totalErrorPercent += 1;
                    count++;
                }
            } else {
                // Standard MAPE Calculation: | (Actual - Predicted) / Actual |
                const error = Math.abs((actual - predicted) / actual);
                totalErrorPercent += error;
                count++;
            }
        }

        if (count === 0) return { mape: 0, count: 0 };

        // Return error ratio (e.g., 0.1 for 10%)
        return {
            itemId,
            mape: parseFloat((totalErrorPercent / count).toFixed(4)),
            daysAnalyzed: count
        };
    }
}

module.exports = MAPECalculator;