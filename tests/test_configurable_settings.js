/**
 * File: test_configurable_settings.js
 * Description: Verification tests for user-configurable settings in stock calculations.
 * Dependencies: mongoose, dotenv, userModel, StockFlowCalculation, AlertGenerator
 * Author: Sample Team
 */

const mongoose = require('mongoose');
const dotenv = require('dotenv');
dotenv.config();

const User = require('../src/models/userModel');
const FreshFlowStockCalculator = require('../src/services/StockFlowCalculation');
const AlertGenerator = require('../src/services/AlertGenerator');

async function testConfigurableSettings() {
    console.log("🚀 Starting Configurable Settings Verification Tests...\n");

    try {
        // 1. Test Calculation Logic with Custom Parameters
        console.log("--- Testing Calculation Logic ---");
        const calculator = new FreshFlowStockCalculator();
        const baseDays = 7;
        const predictedDemand = 70; // 10 per day
        const currentStock = 50;

        // Default Case (LeadTime=2, Buffer=20%)
        // Target = (LeadTimeDemand + CycleDemand) * (1 + Buffer/100)
        // Target = (10*2 + 70) * 1.2 = 90 * 1.2 = 108
        const defaultCalc = calculator.calculateStockNeeds('item1', predictedDemand, currentStock, baseDays, 2, 1.2);
        console.log(`Default Target (LT=2, Buff=20%): ${defaultCalc.aimStockLevel}`);
        if (defaultCalc.aimStockLevel !== 108) throw new Error(`Expected 108, got ${defaultCalc.aimStockLevel}`);

        // Custom Case (LeadTime=5, Buffer=50%)
        // Target = (10*5 + 70) * 1.5 = 120 * 1.5 = 180
        const customCalc = calculator.calculateStockNeeds('item1', predictedDemand, currentStock, baseDays, 5, 1.5);
        console.log(`Custom Target (LT=5, Buff=50%): ${customCalc.aimStockLevel}`);
        if (customCalc.aimStockLevel !== 180) throw new Error(`Expected 180, got ${customCalc.aimStockLevel}`);
        console.log("✅ Calculation logic verified.\n");

        // 2. Test Alert Logic with Custom Threshold
        console.log("--- Testing Alert Logic ---");
        const alertGen = new AlertGenerator();
        const mockResult = {
            menuItemId: 'item1',
            currentStock: 30,
            aimStockLevel: 100, // Stock health = 30%
            calculatedStock: 70,
            itemType: 'MenuItem'
        };

        // Case 1: Default threshold (20%). 30% is NOT critically low.
        const defaultAlert = alertGen.evaluateItem(mockResult, 20);
        console.log(`Default Alert Severity (30% vs 20%): ${defaultAlert.severity}`);
        if (defaultAlert.severity !== 'WARNING') throw new Error(`Expected WARNING, got ${defaultAlert.severity}`);

        // Case 2: Custom threshold (40%). 30% IS critically low.
        const customAlert = alertGen.evaluateItem(mockResult, 40);
        console.log(`Custom Alert Severity (30% vs 40%): ${customAlert.severity}`);
        if (customAlert.severity !== 'CRITICAL') throw new Error(`Expected CRITICAL, got ${customAlert.severity}`);
        console.log("✅ Alert logic verified.\n");

        console.log("🎊 All unit-level verification tests passed!");
        process.exit(0);

    } catch (error) {
        console.error("❌ Test failed:", error.message);
        process.exit(1);
    }
}

testConfigurableSettings();
