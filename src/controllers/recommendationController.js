const asyncHandler = require("express-async-handler");
const User = require("../models/userModel");
const Stock = require("../models/stockModel");
const Forecast = require("../models/ForecastModel");
const MenuItem = require("../models/menuItemModel");
const Addon = require("../models/addonModel");

// @desc    Get prioritized items for purchase
// @route   GET /api/recommendations/prioritize
// @access  Private
const getPrioritizedItems = asyncHandler(async (req, res) => {
    const userId = req.user.id;

    // 1. Fetch User Budget
    const user = await User.findById(userId);
    if (!user) {
        res.status(404);
        throw new Error("User not found");
    }

    const budget = user.budget || 0; // Default to 0 if null

    // 2. Fetch Forecasts
    // Assuming Forecast model tracks demand for MenuItems (and potentially Addons associated with them)
    const forecasts = await Forecast.find({ user: userId }).populate('menuItem');

    // 3. Fetch Current Stock
    const stocks = await Stock.find({ user: userId });

    // 4. Calculate Needs
    let potentialPurchases = [];

    for (const forecast of forecasts) {
        if (!forecast.menuItem) continue; // Skip if menuItem is missing

        const menuItem = forecast.menuItem;
        const itemId = menuItem._id.toString();

        // Calculate Total Predicted Demand from the array of predicted quantities
        const totalPredicted = forecast.predictedQuantity.reduce((a, b) => a + b, 0);

        // Find current stock for this item
        const stockEntry = stocks.find(
            (s) => s.item.toString() === itemId && s.itemType === 'MenuItem'
        );
        const currentStock = stockEntry ? stockEntry.quantity : 0;

        // Calculate Needed Quantity
        const needed = totalPredicted - currentStock;

        if (needed > 0) {
            // Calculate Cost
            const price = menuItem.price || 0;
            const totalCost = needed * price;

            potentialPurchases.push({
                item: {
                    _id: menuItem._id,
                    title: menuItem.title,
                    type: 'MenuItem',
                    price: price
                },
                currentStock,
                predictedDemand: totalPredicted,
                neededQuantity: needed,
                totalCost,
                priorityScore: needed // Simple priority: highest deficit first
            });
        }

        // TODO: Handle Addons if Forecast model supports them separately or if we need to infer addon demand
        // For now, focusing on MenuItems as per Forecast structure roughly seen.
    }

    // NOTE: If there are Addon forecasts, we should handle them too.
    // The Forecast model shown had 'addons' array, but 'predictedQuantity' array. 
    // It's ambiguous if predictedQuantity applies to the *combination* or just the main item.
    // Assuming Main Item for now to keep it simple as per "prioritize items to buy".

    // 5. Prioritize
    // Sort by priorityScore (descending) -> Largest Deficit first
    potentialPurchases.sort((a, b) => b.priorityScore - a.priorityScore);

    // 6. Allocate Budget
    let remainingBudget = budget;
    let recommendedItems = [];

    for (const purchase of potentialPurchases) {
        if (remainingBudget <= 0) break;

        // Determine how many we can buy with remaining budget
        const maxAffordable = Math.floor(remainingBudget / purchase.item.price);
        const quantityToBuy = Math.min(purchase.neededQuantity, maxAffordable);

        if (quantityToBuy > 0) {
            const cost = quantityToBuy * purchase.item.price;
            remainingBudget -= cost;

            recommendedItems.push({
                ...purchase,
                recommendedQuantity: quantityToBuy,
                recommendedCost: cost,
                notes: quantityToBuy < purchase.neededQuantity ? "Partial fulfillment due to budget" : "Full fulfillment"
            });
        } else {
            // Can't afford even one
            recommendedItems.push({
                ...purchase,
                recommendedQuantity: 0,
                recommendedCost: 0,
                notes: "Insufficient budget"
            });
        }
    }

    res.status(200).json({
        budget,
        remainingBudget,
        totalRecommendedCost: budget - remainingBudget,
        recommendedItems
    });
});

module.exports = {
    getPrioritizedItems,
};
