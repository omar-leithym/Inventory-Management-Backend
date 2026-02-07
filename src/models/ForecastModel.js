const mongoose = require("mongoose");

const addonSchema = mongoose.Schema({
    user: {
        type: mongoose.Schema.Types.ObjectId,
        required: true,
        ref: 'User'
    },
    menuItem: {
        type: Number,
        required: [true, "Please add a menu item"],
        ref: 'MenuItem'
    },
    addons: [{
        type: mongoose.Schema.Types.ObjectId,
        ref: 'Addon'
    }],
    predictedQuantity: [{
        type: Number,
        required: true
    }]
}, {
    timestamps: true
});

const Forecast = mongoose.model('forecast', addonSchema);
module.exports = Forecast;
