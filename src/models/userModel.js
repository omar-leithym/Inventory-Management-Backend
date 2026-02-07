const mongoose = require("mongoose");

const userSchema = mongoose.Schema({

    email: {
        type: String,
        required: [true, "Please add an email"],
        unique: true
    },
    firstName: {
        type: String,
        required: [true, "Please add a first name"]
    },
    lastName: {
        type: String,
        required: [true, "Please add a last name"]
    },
    password: {
        type: String,
        required: [true, "Please add a password"]
    },
    phone: {
        type: String,
        required: [true, "Please add a phone number"]
    },
    settings: {
        demandWindow: {
            type: Number,
            default: 7, // Default to Weekly planning
            enum: [1, 7, 30] // Restrict to Daily, Weekly, Monthly
        }
    }
}, {
    timestamps: true
});

const User = mongoose.model('User', userSchema);
module.exports = User;
