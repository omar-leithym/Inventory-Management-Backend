/**
 * File: test_mape_integration.js
 * Description: Integration test to verify MAPE calculation with live database data.
 * Dependencies: mongoose, dotenv, path, userModel, menuItemModel, addonModel, saleModel, ForecastModel, MAPECalculator
 * Author: Sample Team
 */

const mongoose = require('mongoose');
const dotenv = require('dotenv');

// Handle both root execution and src execution for dotenv
const path = require('path');
const envPath = path.resolve(__dirname, 'src', '.env');
dotenv.config({ path: envPath });

console.log("Loading modules...");
try {
    const User = require('../src/models/userModel');
    const MenuItem = require('../src/models/menuItemModel');
    const Addon = require('../src/models/addonModel');
    const Sale = require('../src/models/saleModel');
    const Forecast = require('../src/models/ForecastModel');
    const MAPECalculator = require('../src/services/MAPECalculator');

    async function runTest() {
        if (!process.env.MONGO_URI) {
            console.error("Error: MONGO_URI not found in environment.");
            return;
        }

        console.log("Connecting do MongoDB...");
        await mongoose.connect(process.env.MONGO_URI);
        console.log("Connected.");

        // Find a Forecast to verify against
        const forecast = await Forecast.findOne();
        if (!forecast) {
            console.log("No forecasts found in DB. Please add one manually as discussed.");
        } else {
            console.log(`Found forecast for Item: ${forecast.menuItem} on Date: ${forecast.targetDate}`);

            // Calculate MAPE for that item/date range
            const calculator = new MAPECalculator();
            const start = new Date(forecast.targetDate);
            start.setHours(0, 0, 0, 0);
            const end = new Date(forecast.targetDate);
            end.setHours(23, 59, 59, 999);

            const result = await calculator.calculateItemMAPE(
                forecast.menuItem,
                forecast.user,
                start,
                end
            );

            console.log("\n=== MAPE Result ===");
            console.log(JSON.stringify(result, null, 2));
        }

        await mongoose.disconnect();
        console.log("Done.");
    }

    runTest().catch(err => console.error("Runtime Error:", err));

} catch (err) {
    console.error("Module Load Error:", err);
}
