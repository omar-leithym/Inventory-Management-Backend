const mongoose = require("mongoose");

const restockSchema = mongoose.Schema({
    user: {
        type: mongoose.Schema.Types.ObjectId,
        required: true,
        ref: 'User'
    },
    menuItem: {
        type: Number,  // Custom integer ID instead of ObjectId
        ref: 'MenuItem'
    },
    addons: [{
        type: Number,
        ref: 'Addon'
    }],
    quantity: {
        type: Number,
        default: 1
    },
    pricePerUnit: {
        type: Number,
        required: [true, "Please add the price per unit"]
    }
}, {
    timestamps: true
});

const Restock = mongoose.model('Restock', restockSchema);
module.exports = Restock;
