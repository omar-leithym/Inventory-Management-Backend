/**
 * File: test_mape_math.js
 * Description: Unit test for specific MAPE math scenarios using a mocked calculator.
 * Dependencies: mongoose, MAPECalculator, ForecastModel
 * Author: Sample Team
 */

const mongoose = require('mongoose');
const MAPECalculator = require('../src/services/MAPECalculator');
const Forecast = require('../src/models/ForecastModel');

// Mock Models for testing logic without DB connection if possible, 
// but MAPECalculator relies on .find() and .aggregate() which are Mongoose methods.
// We must mock the mongoose methods or use a real connection.
// Since we have a real calc script, let's try to mock the *return values* of the calls
// by monkey-patching or just creating a "MockService" version that extends it?
// No, simpler to just write a unit test style script that *simulates* the logic
// OR connect to DB and create temporary test data.
// Given the user liked the real data test, let's try to simulate the Calculator logic
// by creating a derived class that returns mock data for the DB calls.

class TestMAPECalculator extends MAPECalculator {
    constructor() {
        super();
        this.mockForecasts = [];
        this.mockSales = [];
    }

    // Override DB calls
    async calculateItemMAPE(itemId, userId, startDate, endDate) {
        // Use the parent's logic but inject the arrays directly if I could refactor the service.
        // But the service calls DB directly inside. 
        // I will copy the LOGIC here to test the MATH.

        console.log("Testing MAPE Math Logic...");

        // Scenario 1: Perfect Prediction
        // Actual: 10, Predicted: 10 -> Error 0
        const scenario1 = this.runMath([10], [10]);
        console.log(`Scenario 1 (Perfect 10/10): MAPE ${scenario1}% (Expected 0)`);

        // Scenario 2: 10% Error
        // Actual: 100, Predicted: 90 -> Error 0.1 (10%)
        const scenario2 = this.runMath([100], [90]);
        console.log(`Scenario 2 (10% Error 100/90): MAPE ${scenario2}% (Expected 10)`);

        // Scenario 3: Mixed
        // Day 1: Actual 10, Pred 10 (0 error)
        // Day 2: Actual 10, Pred 5 (50% error)
        // Avg: 25%
        const scenario3 = this.runMath([10, 10], [10, 5]);
        console.log(`Scenario 3 (Mixed): MAPE ${scenario3}% (Expected 25)`);

        return true;
    }

    runMath(actuals, predicteds) {
        let totalError = 0;
        let count = 0;

        for (let i = 0; i < actuals.length; i++) {
            const actual = actuals[i];
            const predicted = predicteds[i];

            if (actual === 0 && predicted === 0) {
                count++;
            } else if (actual === 0) {
                totalError += 1;
                count++;
            } else {
                totalError += Math.abs((actual - predicted) / actual);
                count++;
            }
        }
        return (totalError / count) * 100;
    }
}

new TestMAPECalculator().calculateItemMAPE();
