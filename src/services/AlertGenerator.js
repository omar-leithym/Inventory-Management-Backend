/**
 * Alert Generator Service
 * Generates actionable stock alerts based on FreshFlowStockCalculator results
 */
class AlertGenerator {

  /**
   * Generate alerts from stock calculation results
   * @param {Array} stockResults - Output from FreshFlowStockCalculator
   * @returns {Array} List of alerts
   */
  generateStockAlerts(stockResults) {
    const alerts = [];

    stockResults.forEach(item => {
      const alert = this.evaluateItem(item);
      if (alert) {
        alerts.push(alert);
      }
    });

    return alerts;
  }

  /**
   * Evaluate a single item for alerts
   * @param {Object} itemResult - Single item result from calculator
   */
  evaluateItem(itemResult) {
    const {
      menuItemId,
      currentStock,
      aimStockLevel,
      calculatedStock,
      itemType
    } = itemResult;

    // Skip trivial items (very low demand) unless completely out
    if (aimStockLevel < 2 && currentStock > 0) return null;

    // 1. CRITICAL: Out of Stock
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

    // 2. WARNING: Below Safety Level (Replenishment Needed)
    if (currentStock < aimStockLevel) {
      // Calculate how low we are (percentage of target)
      const stockHealth = (currentStock / aimStockLevel) * 100;

      // If stock is critically low (< 20% of target) -> High Importance
      if (stockHealth < 20) {
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

    // 3. INFO: Overstocked
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
   * Summarize alerts for dashboard
   * @param {Array} alerts 
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