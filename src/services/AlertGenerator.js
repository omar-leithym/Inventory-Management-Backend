/**
 * File: AlertGenerator.js
 * Description: Service for generating actionable stock alerts based on inventory calculations.
 * Dependencies: None
 * 
 * This service analyzes stock calculation results and generates categorized alerts
 * to help users maintain optimal inventory levels and prevent stockouts.
 */

class AlertGenerator {

  /**
   * Generate alerts from stock calculation results.
   * 
   * Analyzes each item in the stock results and creates alerts based on
   * current stock levels relative to target levels.
   * 
   * @param {Array} stockResults - Output from FreshFlowStockCalculator
   * @param {number} lowStockThreshold - Custom percentage threshold for critically low stock (default: 20)
   * @returns {Array} List of alerts with severity levels and recommended actions
   */
  generateStockAlerts(stockResults, lowStockThreshold = 20) {
    const alerts = [];

    stockResults.forEach(item => {
      const alert = this.evaluateItem(item, lowStockThreshold);
      if (alert) {
        alerts.push(alert);
      }
    });

    return alerts;
  }

  /**
   * Evaluate a single item for alert generation.
   * 
   * Determines if an item requires attention based on stock levels and generates
   * appropriate alerts with severity classification (CRITICAL, WARNING, INFO).
   * 
   * @param {Object} itemResult - Single item result from calculator
   * @param {number} lowStockThreshold - Custom percentage threshold
   * @returns {Object|null} Alert object if action needed, null otherwise
   */
  evaluateItem(itemResult, lowStockThreshold) {
    const {
      menuItemId,
      currentStock,
      aimStockLevel,
      calculatedStock,
      itemType
    } = itemResult;

    // Skip trivial items with very low demand unless completely out
    if (aimStockLevel < 2 && currentStock > 0) return null;

    // CRITICAL: Out of Stock
    if (currentStock <= 0) {
      return {
        menuItemId,
        severity: 'CRITICAL',
        title: 'Out of Stock',
        message: 'Item usage is halted. Immediate replenishment required.',
        action: `Order ${calculatedStock} units immediately.`,
        itemType
      };
    }

    // WARNING: Below Safety Level (Replenishment Needed)
    if (currentStock < aimStockLevel) {
      // Calculate stock health as percentage of target
      const stockHealth = (currentStock / aimStockLevel) * 100;

      // If stock is critically low (below user threshold)
      if (stockHealth < lowStockThreshold) {
        return {
          menuItemId,
          severity: 'CRITICAL',
          title: 'Critically Low Stock',
          message: `Stock at ${Math.round(stockHealth)}% of target. Risk of stockout.`,
          action: `Order ${calculatedStock} units ASAP.`,
          itemType
        };
      }

      return {
        menuItemId,
        severity: 'WARNING',
        title: 'Replenishment Needed',
        message: `Current stock (${currentStock}) is below target (${aimStockLevel}).`,
        action: `Add ${calculatedStock} units to next order.`,
        itemType
      };
    }

    // INFO: Overstocked
    if (currentStock > aimStockLevel * 2) {
      const excess = currentStock - aimStockLevel;
      return {
        menuItemId,
        severity: 'INFO',
        title: 'Overstocked',
        message: `Stock is double the requirement. Potential waste.`,
        action: `Hold ordering. Excess: ${excess} units.`,
        itemType
      };
    }

    return null;
  }

  /**
   * Generate dashboard summary from alerts.
   * 
   * Aggregates alerts by severity level to provide a quick overview
   * for dashboard display.
   * 
   * @param {Array} alerts - Array of generated alerts
   * @returns {Object} Summary containing counts by severity and full alert list
   */
  getDashboardSummary(alerts) {
    return {
      totalAlerts: alerts.length,
      critical: alerts.filter(a => a.severity === 'CRITICAL').length,
      warning: alerts.filter(a => a.severity === 'WARNING').length,
      info: alerts.filter(a => a.severity === 'INFO').length,
      items: alerts
    };
  }
}

module.exports = AlertGenerator;