/**
 * File: inline_mape_test.js
 * Description: Standalone test for MAPE calculation logic using inline schema definitions.
 * Dependencies: mongoose, dotenv, path
 * Author: Sample Team
 */

const mongoose = require('mongoose');
const dotenv = require('dotenv');
const path = require('path');

// Manually Load Env (assuming script is in /tests folder)
const envPath = path.resolve(__dirname, '..', 'src', '.env');
console.log(`Loading .env from: ${envPath}`);
dotenv.config({ path: envPath });

if (!process.env.MONGO_URI) {
    console.error("FATAL: MONGO_URI is missing.");
    process.exit(1);
}

// INLINE MODEL DEFINITIONS to avoid "require" issues
// We only need Schema definitions to query.
const saleSchema = new mongoose.Schema({
    user: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
    menuItem: { type: mongoose.Schema.Types.ObjectId, ref: 'MenuItem' },
    quantity: { type: Number, default: 1 },
}, { timestamps: true });

const forecastSchema = new mongoose.Schema({
    user: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
    menuItem: { type: mongoose.Schema.Types.ObjectId, ref: 'MenuItem' },
    targetDate: { type: Date, required: true },
    predictedQuantity: { type: Number, required: true }
}, { timestamps: true });

// Prevent OverwriteModelError
const Sale = mongoose.models.Sale || mongoose.model('Sale', saleSchema);
const Forecast = mongoose.models.Forecast || mongoose.model('Forecast', forecastSchema);

async function calculateItemMAPE(itemId, userId, startDate, endDate) {
    console.log("Fetching Forecasts...");
    const forecasts = await Forecast.find({
        user: userId,
        menuItem: itemId,
        targetDate: { $gte: startDate, $lte: endDate }
    });

    if (!forecasts.length) return { mape: 0, message: "No forecasts found in range" };

    console.log(`Found ${forecasts.length} forecast(s). Fetching Sales...`);
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
    console.log(`Found sales for ${sales.length} day(s).`);

    const salesMap = {};
    sales.forEach(s => { salesMap[s._id] = s.totalQuantity; });

    let totalErrorPercent = 0;
    let count = 0;

    for (const forecast of forecasts) {
        const dateKey = forecast.targetDate.toISOString().split('T')[0];
        const actual = salesMap[dateKey] || 0;
        const predicted = forecast.predictedQuantity;

        console.log(`Date: ${dateKey} | Actual: ${actual} | Predicted: ${predicted}`);

        if (actual === 0) {
            if (predicted === 0) {
                count++;
            } else {
                totalErrorPercent += 1;
                count++;
            }
        } else {
            const error = Math.abs((actual - predicted) / actual);
            totalErrorPercent += error;
            count++;
        }
    }

    if (count === 0) return { mape: 0, count: 0 };
    return {
        itemId,
        mape: parseFloat((totalErrorPercent / count).toFixed(4)),
        daysAnalyzed: count
    };
}

async function run() {
    try {
        console.log("Connecting to MongoDB...");
        await mongoose.connect(process.env.MONGO_URI);
        console.log("Connected.");

        const forecast = await Forecast.findOne();
        if (!forecast) {
            console.log("No forecasts found in DB.");
        } else {
            console.log(`Testing with Forecast for Item: ${forecast.menuItem}`);

            const start = new Date(forecast.targetDate);
            start.setHours(0, 0, 0, 0);
            const end = new Date(forecast.targetDate);
            end.setHours(23, 59, 59, 999);

            const result = await calculateItemMAPE(forecast.menuItem, forecast.user, start, end);

            console.log("\n=== FINAL RESULT ===");
            console.log(JSON.stringify(result, null, 2));
        }

    } catch (err) {
        console.error("Error:", err);
    } finally {
        await mongoose.disconnect();
        console.log("Disconnected.");
    }
}

run();
