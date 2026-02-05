const mongoose = require("mongoose");

const addonSchema = mongoose.Schema({
    title: {
        type: String,
        required: [true, "Please add a title"],
        unique: true
    },
    price: {
        type: Number,
        required: [true, "Please add a price"],
        default: 0
    },
    selectAsDefault: {
        type: Boolean,
        default: false
    },
    category_id: {
        type: Number
    },
    created: {
        type: Date
    },
    updated: {
        type: Date
    }
}, {
    timestamps: false // We are manually setting created/updated from CSV
});

const Addon = mongoose.model('Addon', addonSchema);
module.exports = Addon;
