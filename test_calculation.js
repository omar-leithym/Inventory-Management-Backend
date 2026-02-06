const FreshFlowStockCalculator = require('./src/services/StockFlowCalculation');

async function testStockCalculation() {
    const calculator = new FreshFlowStockCalculator();

    console.log("=== Testing Stock Calculation Logic ===");

    // Test Case 1: User's Example
    // Input: 7 Days, Prediction 70, Stock 0
    // Expected: Target = 108
    const result1 = calculator.calculateStockNeeds('item1', 70, 0, 7);
    console.log("\nTest Case 1 (Stock 0):");
    console.log("Prediction: 70, Stock: 0");
    console.log("Expected Target: 108");
    console.log("Calculated Target (Aim):", result1.aimStockLevel);
    console.log("Replenishment Needed:", result1.calculatedStock);

    if (result1.aimStockLevel === 108 && result1.calculatedStock === 108) {
        console.log("PASS");
    } else {
        console.log("FAIL");
    }

    // Test Case 2: Partial Stock
    // Input: 7 Days, Prediction 70, Stock 50
    // Expect: Target 108, Replenishment = 108 - 50 = 58
    const result2 = calculator.calculateStockNeeds('item2', 70, 50, 7);
    console.log("\nTest Case 2 (Stock 50):");
    console.log("Expected Replenishment: 58");
    console.log("Calculated Replenishment:", result2.calculatedStock);

    if (result2.calculatedStock === 58) {
        console.log("PASS");
    } else {
        console.log("FAIL");
    }

    // Test Case 3: Excess Stock
    // Input: 7 Days, Prediction 70, Stock 200
    // Expect: Target 108, Replenishment = 0
    const result3 = calculator.calculateStockNeeds('item3', 70, 200, 7);
    console.log("\nTest Case 3 (High Stock):");
    console.log("Expected Replenishment: 0");
    console.log("Calculated Replenishment:", result3.calculatedStock);

    if (result3.calculatedStock === 0) {
        console.log("PASS");
    } else {
        console.log("FAIL");
    }
}

testStockCalculation();
