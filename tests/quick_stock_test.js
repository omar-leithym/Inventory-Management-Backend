const mongoose = require('mongoose');
const dotenv = require('dotenv');
const path = require('path');

// Load environment
const envPath = path.resolve(__dirname, '..', 'src', '.env');
dotenv.config({ path: envPath });

const Stock = require('../src/models/stockModel');

async function quickTest() {
    try {
        await mongoose.connect(process.env.MONGO_URI);
        console.log("Connected to MongoDB\n");

        const testUserId = "6986658482828edcd3983313";
        const testItemId = 59911;

        // Try to find stock
        const stock = await Stock.findOne({
            user: testUserId,
            item: testItemId,
            itemType: 'MenuItem'
        });

        if (stock) {
            console.log("✅ SUCCESS! Stock found:");
            console.log(`   Item ID: ${stock.item}`);
            console.log(`   Quantity: ${stock.quantity}`);
            console.log(`   Type: ${stock.itemType}`);
        } else {
            console.log("❌ No stock found");
        }

        await mongoose.disconnect();
    } catch (error) {
        console.error("Error:", error.message);
        await mongoose.disconnect();
    }
}

quickTest();
