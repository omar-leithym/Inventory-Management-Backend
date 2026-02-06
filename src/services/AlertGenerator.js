/**
 * Alert Generator Service
 * Generates alerts by comparing AI predictions with historical sales
 */


class AlertGenerator {
 
  /**
   * Generate alert for a menu item
   * @param {Object} item - Menu item with stats
   * @param {Object} prediction - AI prediction for this item
   * @returns {Object} Alert object
   */
  generateAlert(item, prediction) {
    const { stats } = item;
    const { predicted_tomorrow, predicted_weekly } = prediction;


    // Calculate percentage difference from average
    const dailyDifference = stats.averageDailySales > 0
      ? ((predicted_tomorrow - stats.averageDailySales) / stats.averageDailySales) * 100
      : (predicted_tomorrow > 0 ? 100 : 0);


    // Determine severity and message
    let severity, message, action;


    if (dailyDifference > 100) {
      // Predicted sales more than double the average
      severity = 'CRITICAL';
      message = `Predicted sales ${Math.round(dailyDifference)}% above normal - MAJOR SPIKE`;
      action = 'Stock up immediately on all ingredients for this item';
    }
    else if (dailyDifference > 50) {
      // Predicted sales 50-100% above average
      severity = 'WARNING';
      message = `Predicted sales ${Math.round(dailyDifference)}% above normal`;
      action = 'Prepare extra ingredients for this item';
    }
    else if (dailyDifference < -50) {
      // Predicted sales 50% below average
      severity = 'INFO';
      message = `Predicted sales ${Math.round(Math.abs(dailyDifference))}% below normal`;
      action = 'Consider running a promotion or special for this item';
    }
    else if (stats.trend > 20) {
      // Item is trending up
      severity = 'INFO';
      message = `Item trending up ${Math.round(stats.trend)}% week-over-week`;
      action = 'Popular item - ensure consistent availability';
    }
    else if (stats.trend < -20) {
      // Item is trending down
      severity = 'INFO';
      message = `Item trending down ${Math.round(Math.abs(stats.trend))}% week-over-week`;
      action = 'Declining popularity - consider menu refresh';
    }
    else {
      // Normal range
      severity = 'OK';
      message = 'Predicted sales within normal range';
      action = null;
    }


    return {
      severity,
      message,
      action,
      dailyDifference: Math.round(dailyDifference),
      trend: Math.round(stats.trend)
    };
  }


  /**
   * Generate alerts for all items
   * @param {Array} itemsWithStats - Array of items with statistics
   * @param {Array} predictions - Array of AI predictions
   * @returns {Array} Array of items with alerts
   */
  generateAllAlerts(itemsWithStats, predictions) {
    return itemsWithStats.map(item => {
      // Find prediction for this item
      const prediction = predictions.find(p =>
        parseInt(p.menu_item_id) === parseInt(item.id)
      ) || {
        menu_item_id: item.id,
        predicted_tomorrow: item.stats.averageDailySales,
        predicted_weekly: item.stats.averageWeeklySales
      };


      const alert = this.generateAlert(item, prediction);


      return {
        id: item.id,
        title: item.title,
        price: item.price,
        current_stats: {
          total_sales: item.stats.totalSales,
          last_7_days: item.stats.last7DaysSales,
          last_30_days: item.stats.last30DaysSales,
          average_daily: Math.round(item.stats.averageDailySales * 10) / 10,
          average_weekly: Math.round(item.stats.averageWeeklySales * 10) / 10,
          trend_percentage: Math.round(item.stats.trend)
        },
        prediction: {
          tomorrow: prediction.predicted_tomorrow,
          weekly: prediction.predicted_weekly
        },
        alert
      };
    });
  }


  /**
   * Get summary statistics
   * @param {Array} itemsWithAlerts - Array of items with alerts
   * @returns {Object} Summary object
   */
  getSummary(itemsWithAlerts) {
    const critical = itemsWithAlerts.filter(i => i.alert.severity === 'CRITICAL');
    const warnings = itemsWithAlerts.filter(i => i.alert.severity === 'WARNING');
    const info = itemsWithAlerts.filter(i => i.alert.severity === 'INFO');
    const ok = itemsWithAlerts.filter(i => i.alert.severity === 'OK');


    return {
      total_items: itemsWithAlerts.length,
      critical_alerts: critical.length,
      warning_alerts: warnings.length,
      info_alerts: info.length,
      ok_items: ok.length,
      top_critical_items: critical.slice(0, 5).map(i => ({
        title: i.title,
        message: i.alert.message
      }))
    };
  }
}


module.exports = AlertGenerator;