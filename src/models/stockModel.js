const mongoose = require("mongoose");

const stockSchema = mongoose.Schema({
    user: {
        type: mongoose.Schema.Types.ObjectId,
        required: true,
        ref: 'User'
    },
    item: {
        type: Number,  // Custom integer IDs (e.g., 59911) instead of ObjectId
        required: true,
        ref: 'MenuItem'
    },
    itemType: {
        type: String,
        required: true,
        enum: ['MenuItem', 'Addon']
    },
    quantity: {
        type: Number,
        default: 0
    }
}, {
    timestamps: true
});

// Ensure a user has only one stock entry per item
stockSchema.index({ user: 1, item: 1, itemType: 1 }, { unique: true });

const Stock = mongoose.model('Stock', stockSchema);
module.exports = Stock;
