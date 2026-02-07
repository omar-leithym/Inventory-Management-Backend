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

    // Budget Logic: Query > User > Infinity
    let budget = Infinity;
    if (req.query.budget !== undefined && req.query.budget !== null) {
        budget = parseFloat(req.query.budget);
    } else if (user.budget !== null && user.budget !== undefined) {
        budget = user.budget;
    }

    // 2. Fetch Forecasts with Population
    // Forecast model has 'addons' array (ObjectIds) and 'predictedQuantity' array (Numbers)
    const forecasts = await Forecast.find({ user: userId })
        .populate('menuItem')
        .populate('addons');

    // 3. Fetch Current Stock
    const stocks = await Stock.find({ user: userId });

    // 4. Calculate Needs
    let potentialPurchases = [];

    for (const forecast of forecasts) {
        if (!forecast.menuItem) continue;

        // --- Process Main Item ---
        // Assumption: predictedQuantity[0] is for the main MenuItem
        const mainPredicted = forecast.predictedQuantity[0] || 0;
        const mainItemId = forecast.menuItem._id.toString();

        const mainStockEntry = stocks.find(
            (s) => s.item.toString() === mainItemId && s.itemType === 'MenuItem'
        );
        const mainCurrentStock = mainStockEntry ? mainStockEntry.quantity : 0;
        const mainNeeded = mainPredicted - mainCurrentStock;

        if (mainNeeded > 0) {
            potentialPurchases.push({
                item: {
                    _id: forecast.menuItem._id,
                    title: forecast.menuItem.title,
                    type: 'MenuItem',
                    price: forecast.menuItem.price || 0
                },
                currentStock: mainCurrentStock,
                predictedDemand: mainPredicted,
                neededQuantity: mainNeeded,
                priorityScore: mainNeeded
            });
        }

        // --- Process Addons ---
        // Assumption: predictedQuantity[i+1] corresponds to addons[i]
        if (forecast.addons && forecast.addons.length > 0) {
            forecast.addons.forEach((addon, index) => {
                // predictedQuantity index is offset by 1 because 0 is main item
                const addonPredicted = forecast.predictedQuantity[index + 1] || 0;
                const addonId = addon._id.toString();

                const addonStockEntry = stocks.find(
                    (s) => s.item.toString() === addonId && s.itemType === 'Addon'
                );
                const addonCurrentStock = addonStockEntry ? addonStockEntry.quantity : 0;
                const addonNeeded = addonPredicted - addonCurrentStock;

                if (addonNeeded > 0) {
                    potentialPurchases.push({
                        item: {
                            _id: addon._id,
                            title: addon.title,
                            type: 'Addon',
                            price: addon.price || 0
                        },
                        currentStock: addonCurrentStock,
                        predictedDemand: addonPredicted,
                        neededQuantity: addonNeeded,
                        priorityScore: addonNeeded
                    });
                }
            });
        }
    }

    // 5. Prioritize (Largest Deficit First)
    potentialPurchases.sort((a, b) => b.priorityScore - a.priorityScore);

    // 6. Allocate Budget
    let remainingBudget = budget;
    let recommendedItems = [];

    for (const purchase of potentialPurchases) {
        // If budget is finite and exhausted, stop or skip
        // But we might want to check if we can afford *anything*, so maybe continue
        // prioritizing items we can afford?
        // For now, strict priority: if top priority can't be bought, we move next? 
        // Or we try to buy as much as possible.

        if (remainingBudget <= 0 && budget !== Infinity) break;

        let quantityToBuy = 0;
        let notes = "";

        if (budget === Infinity) {
            quantityToBuy = purchase.neededQuantity;
            notes = "Full fulfillment (No budget limit)";
        } else {
            const maxAffordable = Math.floor(remainingBudget / purchase.item.price);
            quantityToBuy = Math.min(purchase.neededQuantity, maxAffordable);
            notes = quantityToBuy < purchase.neededQuantity ? "Partial fulfillment due to budget" : "Full fulfillment";
        }

        if (quantityToBuy > 0) {
            const cost = quantityToBuy * purchase.item.price;
            if (budget !== Infinity) {
                remainingBudget -= cost;
            }

            recommendedItems.push({
                ...purchase,
                recommendedQuantity: quantityToBuy,
                recommendedCost: cost,
                notes
            });
        } else if (budget !== Infinity) {
            // Track unmet needs due to budget
            recommendedItems.push({
                ...purchase,
                recommendedQuantity: 0,
                recommendedCost: 0,
                notes: "Insufficient budget"
            });
        }
    }

    res.status(200).json({
        budget: budget === Infinity ? "Unlimited" : budget,
        remainingBudget: budget === Infinity ? "Unlimited" : remainingBudget,
        totalRecommendedCost: budget === Infinity ? recommendedItems.reduce((acc, i) => acc + i.recommendedCost, 0) : (budget - remainingBudget),
        recommendedItems
    });
});

module.exports = {
    getPrioritizedItems,
};
