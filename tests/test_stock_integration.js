const mongoose = require('mongoose');
const dotenv = require('dotenv');
const path = require('path');

// Manually Load Env
const envPath = path.resolve(__dirname, '..', 'src', '.env');
console.log(`Loading .env from: ${envPath}`);
dotenv.config({ path: envPath });

const MenuItem = require('../src/models/menuItemModel');
const Addon = require('../src/models/addonModel');
const Stock = require('../src/models/stockModel');
const FreshFlowStockCalculator = require('../src/services/StockFlowCalculation');
const AlertGenerator = require('../src/services/AlertGenerator');

async function testWithRealData() {
    try {
        console.log("Connecting to MongoDB...");
        if (!process.env.MONGO_URI) {
            throw new Error("MONGO_URI not found in .env");
        }
        await mongoose.connect(process.env.MONGO_URI);
        console.log("Connected.");

        // 1. Fetch referenced data (Catalog)
        console.log("Fetching Catalog...");
        const menuItems = await MenuItem.find({});
        const addons = await Addon.find({});

        const allCatalogItems = [
            ...menuItems.map(item => ({ id: item._id, name: item.title || item.name, type: 'MenuItem' })),
            ...addons.map(item => ({ id: item._id, name: item.name, type: 'Addon' }))
        ];
        console.log(`Found ${allCatalogItems.length} catalog items.`);

        // 2. Fetch a sample user from Stock to test with
        // Get unique users who have stock
        const distinctUsers = await Stock.distinct('user');

        if (distinctUsers.length === 0) {
            console.log("No stock data found in DB.");
            return;
        }

        const testUserId = distinctUsers[0];
        console.log(`Testing with User ID: ${testUserId}`);

        // 3. Fetch Stock for this user
        const userStock = await Stock.find({ user: testUserId });
        console.log(`Found ${userStock.length} stock entries for user.`);

        // 4. Run Calculation (TESTING BOTH 7 DAYS AND 1 DAY)
        const calculator = new FreshFlowStockCalculator();

        console.log("\n--- RUNNING CALCULATION FOR 7 DAYS (WEEKLY) ---");
        const resultsWeekly = await calculator.calculateAllStockNeeds(allCatalogItems, userStock, 7);
        displayResults(resultsWeekly, userStock, "WEEKLY");

        console.log("\n--- RUNNING CALCULATION FOR 1 DAY (DAILY) ---");
        const resultsDaily = await calculator.calculateAllStockNeeds(allCatalogItems, userStock, 1);
        displayResults(resultsDaily, userStock, "DAILY");

    } catch (error) {
        console.error("Error:", error);
    } finally {
        await mongoose.disconnect();
        console.log("\nDisconnected from MongoDB.");
    }
}

function displayResults(results, userStock, label) {
    // 5. Generate Alerts
    const AlertGenerator = require('../src/services/AlertGenerator');
    const alertGen = new AlertGenerator();
    const alerts = alertGen.generateStockAlerts(results);
    const summary = alertGen.getDashboardSummary(alerts);

    console.log(`\n=== ALERTS DASHBOARD SUMMARY [${label}] ===`);
    console.log(JSON.stringify(summary, null, 2));

    // 6. Display Detailed Results (Filtered for meaningful item)
    console.log(`\n=== Calculation Results (Active Item Only) [${label}] ===`);

    // Filter to show only the item we know has stock (or specific ID)
    const targetItem = results.find(r => r.menuItemId.toString() === "6984c05bb162ac961c44eafb");

    if (targetItem) {
        const r = targetItem;
        const stockEntry = userStock.find(s =>
            (s.item && s.item.toString() === r.menuItemId.toString())
        );

        console.log(`\nItem: ${r.menuItemId}`);
        console.log(`Input Days: ${r.inputDays}`);
        console.log(`Prediction: ${r.predictedDemand}`);
        console.log(`Aim/Target: ${r.aimStockLevel} (Current: ${r.currentStock}) -> To Order: ${r.calculatedStock}`);

        // Show Alert if exists
        const itemAlert = alerts.find(a => a.menuItemId.toString() === r.menuItemId.toString());
        if (itemAlert) {
            console.log(`⚠️  ALERT [${itemAlert.severity}]: ${itemAlert.title} -> ${itemAlert.message}`);
        } else {
            console.log("🟢 Status: OK");
        }
    } else {
        console.log("Target item not found in results.");
    }
}

testWithRealData();
