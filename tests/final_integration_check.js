/**
 * File: final_integration_check.js
 * Description: Integration test to verify full system flow (User Settings -> Stock Calculation -> Alerts).
 * Dependencies: mongoose, dotenv, userModel, stockModel, menuItemModel, StockFlowCalculation, AlertGenerator
 * Author: Sample Team
 */

const mongoose = require('mongoose');
const dotenv = require('dotenv');
dotenv.config({ path: 'src/.env' });

const User = require('../src/models/userModel');
const Stock = require('../src/models/stockModel');
const MenuItem = require('../src/models/menuItemModel');
const FreshFlowStockCalculator = require('../src/services/StockFlowCalculation');
const AlertGenerator = require('../src/services/AlertGenerator');

async function verifyAll() {
    console.log("🚀 Starting Final System Verification...");

    try {
        const mongoURI = process.env.MONGO_URI || 'mongodb://localhost:27017/inventory-management';
        await mongoose.connect(mongoURI);
        console.log("✅ Connected to MongoDB.");

        // 1. Setup Test User with Custom Settings
        const user = await User.findOneAndUpdate(
            { email: 'test_integration@example.com' },
            {
                firstName: 'Test',
                lastName: 'Integration',
                password: 'password123',
                phone: '+1234567890',
                settings: {
                    demandWindow: 7,
                    leadTime: 5,           // Custom Lead Time
                    safetyStockBuffer: 50, // Custom Buffer (1.5x)
                    lowStockThreshold: 40  // Custom Alert Threshold (Cratically low at 40%)
                }
            },
            { upsert: true, new: true }
        );
        console.log("✅ Test user configured with custom settings.");

        // 2. Simulate Stock Recommendations logic
        console.log("🧪 Simulating Stock Recommendations flow...");

        // Mocking the inputs for a single item
        const mockCatalog = [{ id: new mongoose.Types.ObjectId(), name: 'Test Item', type: 'MenuItem' }];
        const mockStock = [{ item: mockCatalog[0].id, quantity: 45 }]; // Stock health below target

        const settings = user.settings;
        const demandDays = settings.demandWindow;

        const calculator = new FreshFlowStockCalculator();
        const recommendations = await calculator.calculateAllStockNeeds(
            mockCatalog,
            mockStock,
            demandDays,
            settings.leadTime,
            settings.safetyStockBuffer
        );

        const rec = recommendations[0];
        console.log(`- Aim Stock Level: ${rec.aimStockLevel}`);
        // Math: (10*5 [LT] + 70 [Cycle]) * 1.5 [Buff] = 120 * 1.5 = 180
        if (rec.aimStockLevel !== 180) {
            throw new Error(`Calculation Fail: Expected 180, got ${rec.aimStockLevel}`);
        }
        console.log("✅ Calculation logic correct.");

        // 3. Verify Alerts
        const alertGen = new AlertGenerator();
        const alerts = alertGen.generateStockAlerts(recommendations, settings.lowStockThreshold);

        // Stock Health: 45 / 180 = 25%.
        // 25% < 40% (lowStockThreshold) -> Should be CRITICAL.
        const alert = alerts[0];
        console.log(`- Alert Severity: ${alert.severity}`);
        if (alert.severity !== 'CRITICAL') {
            throw new Error(`Alert Logic Fail: Expected CRITICAL at 25% health with 40% threshold, got ${alert.severity}`);
        }
        console.log("✅ Alert logic correct.");

        console.log("\n🎊 INTEGRATION SUCCESS: The system is correctly using user-defined settings!");
        process.exit(0);

    } catch (error) {
        console.error("❌ INTEGRATION FAILED:", error.message);
        process.exit(1);
    }
}

verifyAll();
