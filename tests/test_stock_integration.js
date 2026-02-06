const mongoose = require('mongoose');
const dotenv = require('dotenv');
// Adjust path to .env if it is in src, based on file listing
dotenv.config({ path: './src/.env' });

const MenuItem = require('../src/models/menuItemModel');
const Addon = require('../src/models/addonModel');
const Stock = require('../src/models/stockModel');
const FreshFlowStockCalculator = require('../src/services/StockFlowCalculation');

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

        // 4. Run Calculation
        const calculator = new FreshFlowStockCalculator();
        const results = await calculator.calculateAllStockNeeds(allCatalogItems, userStock, 7);

        // 5. Display Results
        console.log("\n=== Calculation Results (First 5 Items) ===");
        results.slice(0, 5).forEach(r => {
            const stockEntry = userStock.find(s =>
                (s.item && s.item.toString() === r.menuItemId.toString())
            );

            console.log(`\nItem: ${r.menuItemId}`);
            console.log(`Prediction: ${r.predictedDemand}`);
            console.log(`Current Stock (DB): ${r.currentStock} (Raw quantity: ${stockEntry ? stockEntry.quantity : 'N/A'})`);
            console.log(`Aim/Target: ${r.aimStockLevel}`);
            console.log(`To Order: ${r.calculatedStock}`);

            // Verification check logic (optional, just logging for user to see)
            if (Math.max(0, r.aimStockLevel - r.currentStock) === r.calculatedStock) {
                console.log("✅ Math Check Passed");
            } else {
                console.log("❌ Math Check Failed");
            }
        });

    } catch (error) {
        console.error("Error:", error);
    } finally {
        await mongoose.disconnect();
        console.log("\nDisconnected from MongoDB.");
    }
}

testWithRealData();
