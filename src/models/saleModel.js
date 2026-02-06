const mongoose = require("mongoose");

const saleSchema = mongoose.Schema({
    user: {
        type: mongoose.Schema.Types.ObjectId,
        required: true,
        ref: 'User'
    },
    menuItem: {
        type: mongoose.Schema.Types.ObjectId,
        required: [true, "Please add a menu item"],
        ref: 'MenuItem'
    },
    addons: [{
        type: mongoose.Schema.Types.ObjectId,
        ref: 'Addon'
    }],
    quantity: {
        type: Number,
        default: 1
    },
    price: {
        type: Number,
        required: [true, "Please add the total price"]
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
