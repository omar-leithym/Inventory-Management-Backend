const mongoose = require('mongoose');
const dotenv = require('dotenv');
const path = require('path');

// Load environment
const envPath = path.resolve(__dirname, '..', 'src', '.env');
dotenv.config({ path: envPath });

const Sale = require('../src/models/saleModel');
const Stock = require('../src/models/stockModel');

/**
 * This script processes all existing sales and deducts their quantities from stock.
 * Use this to sync historical sales data with current stock levels.
 */
async function syncSalesToStock() {
    try {
        console.log("Connecting to MongoDB...");
        await mongoose.connect(process.env.MONGO_URI);
        console.log("Connected.\n");

        // Get all sales
        const allSales = await Sale.find({}).sort('createdAt');
        console.log(`Found ${allSales.length} sales to process\n`);

        if (allSales.length === 0) {
            console.log("No sales to process.");
            return;
        }

        let processedCount = 0;
        let skippedCount = 0;
        const stockUpdates = new Map(); // Track cumulative changes per stock item

        console.log("=== PROCESSING SALES ===\n");

        for (const sale of allSales) {
            console.log(`Sale ID: ${sale._id}`);
            console.log(`  User: ${sale.user}`);
            console.log(`  MenuItem: ${sale.menuItem}`);
            console.log(`  Quantity: ${sale.quantity}`);
            console.log(`  Date: ${sale.createdAt}`);

            // Process MenuItem
            const menuItemKey = `${sale.user}_${sale.menuItem}_MenuItem`;

            const menuItemStock = await Stock.findOne({
                user: sale.user,
                item: sale.menuItem,
                itemType: 'MenuItem'
            });

            if (menuItemStock) {
                // Track the change
                if (!stockUpdates.has(menuItemKey)) {
                    stockUpdates.set(menuItemKey, {
                        stock: menuItemStock,
                        originalQty: menuItemStock.quantity,
                        totalDeduction: 0
                    });
                }
                stockUpdates.get(menuItemKey).totalDeduction += sale.quantity;
                console.log(`  ✅ Will deduct ${sale.quantity} from MenuItem stock`);
            } else {
                console.log(`  ⚠️  No stock entry found for MenuItem ${sale.menuItem}`);
                skippedCount++;
            }

            // Process Addons
            if (sale.addons && sale.addons.length > 0) {
                for (const addonId of sale.addons) {
                    const addonKey = `${sale.user}_${addonId}_Addon`;

                    const addonStock = await Stock.findOne({
                        user: sale.user,
                        item: addonId,
                        itemType: 'Addon'
                    });

                    if (addonStock) {
                        if (!stockUpdates.has(addonKey)) {
                            stockUpdates.set(addonKey, {
                                stock: addonStock,
                                originalQty: addonStock.quantity,
                                totalDeduction: 0
                            });
                        }
                        stockUpdates.get(addonKey).totalDeduction += sale.quantity;
                        console.log(`  ✅ Will deduct ${sale.quantity} from Addon ${addonId} stock`);
                    } else {
                        console.log(`  ⚠️  No stock entry found for Addon ${addonId}`);
                        skippedCount++;
                    }
                }
            }

            processedCount++;
            console.log("");
        }

        // Apply all stock updates
        console.log("=== APPLYING STOCK UPDATES ===\n");

        for (const [key, update] of stockUpdates.entries()) {
            const newQuantity = update.originalQty - update.totalDeduction;
            update.stock.quantity = newQuantity;
            await update.stock.save();

            console.log(`Updated Stock:`);
            console.log(`  Item: ${update.stock.item} (${update.stock.itemType})`);
            console.log(`  Original: ${update.originalQty}`);
            console.log(`  Deducted: ${update.totalDeduction}`);
            console.log(`  New Quantity: ${newQuantity}`);
            console.log("");
        }

        console.log("=== SUMMARY ===");
        console.log(`Total sales processed: ${processedCount}`);
        console.log(`Stock entries updated: ${stockUpdates.size}`);
        console.log(`Items skipped (no stock): ${skippedCount}`);

    } catch (error) {
        console.error("❌ Error:", error.message);
        console.error(error);
    } finally {
        await mongoose.disconnect();
        console.log("\nDisconnected from MongoDB.");
    }
}

// Run the sync
syncSalesToStock();
