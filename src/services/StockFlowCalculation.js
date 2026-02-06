/**
 * FreshFlow Stock Calculator Service
 * Converts AI-predicted demand into required stock levels based on user-defined formulas.
 */
class FreshFlowStockCalculator {

  /**
   * PLACEHOLDER: Simulate fetching prediction from AI Model API
   * In production, this would be an HTTP request to the Python/Flask AI service.
   * @param {string} itemId 
   * @param {number} days 
   * @returns {Promise<number>} Predicted total demand for the period
   */
  async fetchAIPrediction(itemId, days) {
    // TODO: Connect to actual AI Model API here
    // const response = await axios.post('http://ai-service/predict', { itemId, days });
    // return response.data.prediction;

    // Returning dummy data for now to demonstrate the flow
    return 70; // Example: 70 items predicted for 7 days
  }

  /**
   * Calculate stock requirements based on the specific formula:
   * Target = (LeadTimeDemand + CycleDemand) * Buffer
   * 
   * @param {string} menuItemId - Menu item ID
   * @param {number} predictedDemand - Total predicted demand for the input days
   * @param {number} currentStock - Current inventory level
   * @param {number} days - Prediction period in days (default 7)
   * @param {number} leadTime - Days to restock (default 2)
   * @param {number} buffer - Safety multiplier (default 1.2)
   * @returns {Object} Stock calculation details
   */
  calculateStockNeeds(menuItemId, predictedDemand, currentStock, days = 7, leadTime = 2, buffer = 1.2) {
    // 1. Calculate Daily Demand Rate
    const dailyRate = predictedDemand / days;

    // 2. Calculate Lead Time Demand (Sold while waiting for stock)
    const leadTimeDemand = dailyRate * leadTime;

    // 3. Calculate Cycle Demand (Demand for the planning period)
    const cycleDemand = predictedDemand;

    // 4. Calculate Total Base Demand
    const baseDemand = leadTimeDemand + cycleDemand;

    // 5. Apply Buffer to get Target Stock Level (Aim Number)
    const aimStockLevel = Math.ceil(baseDemand * buffer);

    // 6. Calculate Replenishment Needed (Calculated Stock)
    // If current stock is higher than aim, we don't need to order (0)
    const replenishmentNeeded = Math.max(0, aimStockLevel - currentStock);

    return {
      menuItemId,
      inputDays: days,
      predictedDemand, // D_total
      dailyRate,       // R
      aimStockLevel,   // Target Stock (The "Aim number")
      currentStock,    // Current Stock
      calculatedStock: replenishmentNeeded, // Stock to order/add
      details: {
        leadTimeDemand,
        cycleDemand,
        baseDemand,
        bufferUsed: buffer
      }
    };
  }

  /**
   * Process multiple items
   * Fetches predictions internally via the placeholder
   * @param {Array} menuItems - List of items
   * @param {Array} currentInventory - List of stock entries
   * @param {number} days - Prediction horizon
   */
  async calculateAllStockNeeds(menuItems, currentInventory, days = 7) {
    const results = [];

    for (const item of menuItems) {
      // Find current stock for this item
      const stockEntry = currentInventory.find(inv => inv.menuItemId === item.id);
      const currentStockLevel = stockEntry ? stockEntry.units : 0;

      // Get Prediction from AI (Placeholder)
      const predictedDemand = await this.fetchAIPrediction(item.id, days);

      // Perform Calculation
      const calculation = this.calculateStockNeeds(
        item.id,
        predictedDemand,
        currentStockLevel,
        days
      );

      results.push(calculation);
    }

    return results;
  }
}

module.exports = FreshFlowStockCalculator;