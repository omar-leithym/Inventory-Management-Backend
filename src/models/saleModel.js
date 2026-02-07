const mongoose = require("mongoose");

const saleSchema = mongoose.Schema({
    user: {
        type: mongoose.Schema.Types.ObjectId,
        required: true,
        ref: 'User'
    },
    menuItem: {
        type: Number,  // Custom integer ID instead of ObjectId
        required: [true, "Please add a menu item"],
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
    },
    discount: {
        type: Number,
        default: 0
    }
}, {
    timestamps: true
});

const Sale = mongoose.model('Sale', saleSchema);
module.exports = Sale;
