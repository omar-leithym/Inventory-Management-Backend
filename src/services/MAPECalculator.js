const mongoose = require('mongoose');
const Forecast = require('../models/ForecastModel');
const Sale = require('../models/saleModel');

/**
 * Service to calculate Forecast Accuracy using MAPE
 * Formula: Mean Absolute Percentage Error
 */
class MAPECalculator {

    /**
     * Calculate MAPE for a specific item over a date range
     * @param {string} itemId - Menu Item ID
     * @param {string} userId - User ID
     * @param {Date} startDate 
     * @param {Date} endDate 
     */
    async calculateItemMAPE(itemId, userId, startDate, endDate) {
        // 1. Fetch Forecasts
        const forecasts = await Forecast.find({
            user: userId,
            menuItem: itemId,
            targetDate: { $gte: startDate, $lte: endDate }
        });

        if (!forecasts.length) return { mape: 0, message: "No forecasts found" };

        // 2. Fetch Actual Sales (Aggregated by Day)
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

        // Map sales to a dictionary for easy lookup: { "2023-10-27": 15 }
        const salesMap = {};
        sales.forEach(s => {
            salesMap[s._id] = s.totalQuantity;
        });

        // 3. Calculate Error
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
                // If predicted > 0 but actual 0, strict MAPE is undefined (division by 0).
                // Common practice: use a small number or cap error at 100%? 
                // Or skip? For simplicity, we skip strictly undefined days or assume 100% error.
                // Let's count it as 100% error (1.0) if we predicted something but sold nothing.
                else {
                    totalErrorPercent += 1; // 100% error
                    count++;
                }
            } else {
                // Standard MAPE Calculation
                // | (Actual - Predicted) / Actual |
                const error = Math.abs((actual - predicted) / actual);
                totalErrorPercent += error;
                count++;
            }
        }

        if (count === 0) return { mape: 0, count: 0 };

        // Return raw error ratio (e.g., 0.1 for 10%)
        return {
            itemId,
            mape: parseFloat((totalErrorPercent / count).toFixed(4)),
            daysAnalyzed: count
        };
    }
}

module.exports = MAPECalculator;