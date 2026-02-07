const mongoose = require("mongoose");

const menuItemSchema = mongoose.Schema({
    _id: Number,
    title: {
        type: String,
        required: [true, "Please add a title"]
    },
    type: {
        type: String,
        required: [true, "Please add a type"]
    },
    price: {
        type: Number,
        required: [true, "Please add a price"],
        default: 0
    },
    created: {
        type: Date
    }
}, {
    timestamps: false // We are manually setting created from CSV
});

const MenuItem = mongoose.model('MenuItem', menuItemSchema);
module.exports = MenuItem;
