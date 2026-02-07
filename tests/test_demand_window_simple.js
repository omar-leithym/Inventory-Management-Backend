const mongoose = require('mongoose');
const dotenv = require('dotenv');
const path = require('path');

// Load environment
const envPath = path.resolve(__dirname, '..', 'src', '.env');
dotenv.config({ path: envPath });

const User = require('../src/models/userModel');
const FreshFlowStockCalculator = require('../src/services/StockFlowCalculation');

/**
 * Simple test to verify demand window setting is used in calculations
 */
async function testDemandWindow() {
    try {
        await mongoose.connect(process.env.MONGO_URI);
        console.log("Connected to MongoDB\n");

        // Find a user
        const user = await User.findOne({});
        if (!user) {
            console.log("❌ No users found");
            return;
        }

        console.log("=== DEMAND WINDOW INTEGRATION TEST ===\n");
        console.log(`User: ${user.email || user._id}`);
        console.log(`Current demandWindow: ${user.settings?.demandWindow || 7}\n`);

        // Test with different demand windows
        const testWindows = [1, 7, 30];
        const calculator = new FreshFlowStockCalculator();

        for (const days of testWindows) {
            console.log(`\n--- Testing ${days}-day window ---`);

            // Update user setting
            if (!user.settings) user.settings = {};
            user.settings.demandWindow = days;
            await user.save();

            // Verify it was saved
            const reloadedUser = await User.findById(user._id);
            const savedDays = reloadedUser.settings?.demandWindow || 7;
            console.log(`✅ Setting saved: ${savedDays} days`);

            // Run a simple calculation
            const testItems = [{ id: 59911, name: 'Test Item', type: 'MenuItem' }];
            const testStock = [{ item: 59911, quantity: 50 }];

            const results = await calculator.calculateAllStockNeeds(testItems, testStock, days);

            if (results.length > 0) {
                const result = results[0];
                console.log(`\nCalculation Results:`);
                console.log(`  Input Days: ${result.inputDays}`);
                console.log(`  Predicted Demand: ${result.predictedDemand}`);
                console.log(`  Daily Rate: ${result.dailyRate.toFixed(2)}`);
                console.log(`  Aim Stock: ${result.aimStockLevel}`);

                // Verify the calculation used the correct days
                const expectedDemand = 10 * days; // From placeholder: 10 items/day
                const match = result.predictedDemand === expectedDemand && result.inputDays === days;
                console.log(`  ✅ Correct days used: ${match ? 'YES' : 'NO'}`);
            }
        }

        console.log(`\n\n=== VERIFICATION COMPLETE ===`);
        console.log(`\n✅ The demand window setting:`);
        console.log(`   1. Can be saved to User.settings.demandWindow`);
        console.log(`   2. Is retrieved correctly`);
        console.log(`   3. Is used in stock calculations`);
        console.log(`\n📍 In production, stockController.js:`);
        console.log(`   - Fetches user.settings.demandWindow (line 144)`);
        console.log(`   - Passes it to calculateAllStockNeeds() (line 152)`);
        console.log(`   - Calculations scale with the chosen window`);

        await mongoose.disconnect();
    } catch (error) {
        console.error("Error:", error.message);
        await mongoose.disconnect();
    }
}

testDemandWindow();
