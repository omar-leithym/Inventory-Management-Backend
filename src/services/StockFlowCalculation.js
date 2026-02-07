/**
 * File: StockFlowCalculation.js
 * Description: Service for converting AI-predicted demand into actionable stock requirements.
 * Dependencies: None (axios for future AI service integration)
 * 
 * This service calculates optimal stock levels based on demand predictions,
 * lead times, and safety buffers. It implements the formula:
 * Target Stock = (Lead Time Demand + Cycle Demand) × Buffer
 */

class FreshFlowStockCalculator {

  /**
   * Fetch AI prediction for item demand.
   * 
   * NOTE: This is a placeholder for AI model integration. In production,
   * this would make an HTTP request to the Python/Flask AI service.
   * 
   * @param {string} itemId - Menu Item ID
   * @param {number} days - Prediction period in days
   * @returns {Promise<number>} Predicted total demand for the period
   */
  async fetchAIPrediction(itemId, days) {
    // TODO: Connect to actual AI Model API
    // const response = await axios.post('http://ai-service/predict', { itemId, days });
    // return response.data.prediction;

    // Dummy data: assumes sales rate of approx 10 items/day
    return 10 * days;
  }

  /**
   * Calculate stock requirements based on demand prediction.
   * 
   * Uses the formula:
   * Target = (Lead Time Demand + Cycle Demand) × Buffer
   * 
   * Where:
   * - Lead Time Demand: Items sold while waiting for stock delivery
   * - Cycle Demand: Predicted demand for the planning period
   * - Buffer: Safety multiplier to prevent stockouts
   * 
   * @param {string} menuItemId - Menu item ID
   * @param {number} predictedDemand - Total predicted demand for the input days
   * @param {number} currentStock - Current inventory level
   * @param {number} days - Prediction period in days (default: 7)
   * @param {number} leadTime - Days to restock (default: 2)
   * @param {number} buffer - Safety multiplier (default: 1.2)
   * @returns {Object} Detailed stock calculation results
   */
  calculateStockNeeds(menuItemId, predictedDemand, currentStock, days = 7, leadTime = 2, buffer = 1.2) {
    // Calculate Daily Demand Rate
    const dailyRate = predictedDemand / days;

    // Calculate Lead Time Demand (Sold while waiting for stock)
    const leadTimeDemand = dailyRate * leadTime;

    // Calculate Cycle Demand (Demand for the planning period)
    const cycleDemand = predictedDemand;

    // Calculate Total Base Demand
    const baseDemand = leadTimeDemand + cycleDemand;

    // Apply Buffer to get Target Stock Level (Aim Number)
    const aimStockLevel = Math.ceil(baseDemand * buffer);

    // Calculate Replenishment Needed (Calculated Stock)
    // If current stock exceeds aim, no order needed
    const replenishmentNeeded = Math.max(0, aimStockLevel - currentStock);

    return {
      menuItemId,
      inputDays: days,
      predictedDemand,
      dailyRate,
      aimStockLevel,
      currentStock,
      calculatedStock: replenishmentNeeded,
      details: {
        leadTimeDemand,
        cycleDemand,
        baseDemand,
        bufferUsed: buffer
      }
    };
  }

  /**
   * Process stock calculations for multiple items.
   * 
   * Fetches AI predictions for each item and calculates their stock requirements
   * based on user-defined settings.
   * 
   * @param {Array} menuItems - List of catalog items
   * @param {Array} currentInventory - List of stock entries
   * @param {number} days - Prediction horizon (default: 7)
   * @param {number} leadTime - Custom lead time from settings (default: 2)
   * @param {number} bufferPercentage - Safety stock buffer percentage (default: 20)
   * @returns {Promise<Array>} Stock calculation results for all items
   */
  async calculateAllStockNeeds(menuItems, currentInventory, days = 7, leadTime = 2, bufferPercentage = 20) {
    const results = [];
    const bufferMultiplier = 1 + (bufferPercentage / 100);

    for (const item of menuItems) {
      // Find current stock for this item
      const stockEntry = currentInventory.find(inv =>
        inv.item && inv.item.toString() === item.id.toString()
      );
      const currentStockLevel = stockEntry ? stockEntry.quantity : 0;

      // Get Prediction from AI (Placeholder)
      const predictedDemand = await this.fetchAIPrediction(item.id, days);

      // Perform Calculation
      const calculation = this.calculateStockNeeds(
        item.id,
        predictedDemand,
        currentStockLevel,
        days,
        leadTime,
        bufferMultiplier
      );

      results.push(calculation);
    }

    return results;
  }
}

module.exports = FreshFlowStockCalculator;