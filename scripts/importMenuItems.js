const fs = require('fs');
const mongoose = require('mongoose');
const dotenv = require('dotenv');
const path = require('path');
const MenuItem = require('../src/models/menuItemModel');

// Load environment variables
dotenv.config({ path: path.join(__dirname, '../.env') });

const filePath = path.join(__dirname, '../data/dim_menu_items.csv');

mongoose.connect(process.env.MONGO_URI)
    .then(() => {
        console.log('Connected to MongoDB');
        importData();
    })
    .catch((err) => {
        console.error('Error connecting to MongoDB:', err);
        process.exit(1);
    });

const parseLine = (line) => {
    const row = [];
    let current = '';
    let inQuote = false;
    for (let i = 0; i < line.length; i++) {
        const char = line[i];
        if (char === '"') {
            inQuote = !inQuote;
        } else if (char === ',' && !inQuote) {
            row.push(current);
            current = '';
            continue;
        }
        current += char;
    }
    row.push(current);

    return row.map(val => {
        val = val.trim();
        if (val.startsWith('"') && val.endsWith('"')) {
            return val.substring(1, val.length - 1).replace(/""/g, '"');
        }
        return val;
    });
};

const importData = async () => {
    try {
        const data = fs.readFileSync(filePath, 'utf8');
        const lines = data.split(/\r?\n/);

        if (lines.length < 2) {
            console.log('No data found in CSV');
            process.exit(0);
        }

        const headerLine = lines[0];
        const headers = parseLine(headerLine);
        const hIdx = {};
        headers.forEach((h, i) => hIdx[h] = i);

        const itemsToInsert = [];
        const seenItems = new Set();

        let count = 0;
        let skipped = 0;
        let duplicatesSkipped = 0;

        console.log(`Found ${lines.length - 1} rows. Processing...`);

        // Check columns exist
        if (hIdx['status'] === undefined || hIdx['title'] === undefined || hIdx['price'] === undefined) {
            console.error('Missing required columns in CSV');
            process.exit(1);
        }

        for (let i = 1; i < lines.length; i++) {
            const line = lines[i].trim();
            if (!line) continue;

            const row = parseLine(line);

            const status = row[hIdx['status']];
            const title = row[hIdx['title']];
            const price = row[hIdx['price']];
            const type = row[hIdx['type']];
            const created = row[hIdx['created']];

            // Filter Logic: "if status indicates its inacive dont include it"
            if (status === 'Inactive') {
                skipped++;
                continue;
            }

            // Deduplication Logic: Exact Match (Title + Type + Price)
            // Using a composite key
            const uniqueKey = `${title}|${type}|${price}`;

            if (seenItems.has(uniqueKey)) {
                duplicatesSkipped++;
                continue;
            }
            seenItems.add(uniqueKey);

            const item = {
                title: title,
                type: type || 'Normal',
                price: parseFloat(price) || 0,
                created: new Date(parseInt(created) * 1000)
            };

            itemsToInsert.push(item);
            count++;
        }

        if (itemsToInsert.length > 0) {
            await MenuItem.deleteMany({});
            console.log('Cleared existing MenuItems');

            await MenuItem.insertMany(itemsToInsert);
            console.log(`Successfully inserted ${count} menu items.`);
            console.log(`Skipped ${skipped} rows (Inactive).`);
            console.log(`Skipped ${duplicatesSkipped} rows (Exact Duplicates).`);
        } else {
            console.log('No valid menu items found to insert.');
        }

        process.exit(0);

    } catch (error) {
        console.error('Error importing data:', error);
        process.exit(1);
    }
};
