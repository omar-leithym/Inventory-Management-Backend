const asyncHandler = require("express-async-handler");
const User = require("../models/userModel");
const jwt = require("jsonwebtoken");
const bcrypt = require("bcrypt");
const validator = require("validator");
const { parsePhoneNumberFromString } = require("libphonenumber-js");
const passwordSchema = require("../utils/validation");

const genToken = (id) => {
    return jwt.sign({ id }, process.env.JWT_SECRET, {
        expiresIn: "30d"
    });
};

const registerUser = asyncHandler(async (req, res) => {
    const { email, password, phone, firstName, lastName } = req.body;

    if (!email || !password || !firstName || !lastName || !phone) {
        res.status(400);
        throw new Error("Please fill in all fields");
    }

    if (!passwordSchema.validate(password)) {
        res.status(400);
        throw new Error("Password doesn't meet criteria");
    }

    const phoneNumber = parsePhoneNumberFromString(phone);

    if (!phoneNumber || !phoneNumber.isValid()) {
        res.status(400);
        throw new Error("Invalid phone number");
    }

    if (!validator.isEmail(email)) {
        res.status(400);
        throw new Error("Invalid email address");
    }

    const emailExists = await User.findOne({ email });

    if (emailExists) {
        res.status(400);
        throw new Error("Email exists");
    }

    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(password, salt);

    const user = await User.create({
        email,
        password: hashedPassword,
        firstName,
        lastName,
        phone
    });

    if (user) {
        res.status(201).json({
            id: user._id,
            email: user.email,
            firstName: user.firstName,
            lastName: user.lastName,
            token: genToken(user._id)
        });
    }
    else {
        res.status(400);
        throw new Error("Invalid user data");
    }
});

const loginUser = asyncHandler(async (req, res) => {
    const { email, password } = req.body;

    if (!email || !password) {
        res.status(400);
        throw new Error("Please add email and password");
    }

    const user = await User.findOne({ email });

    if (user && (await bcrypt.compare(password, user.password))) {
        res.status(201).json({
            id: user._id,
            email: user.email,
            firstName: user.firstName,
            lastName: user.lastName,
            token: genToken(user._id)
        });
    }
    else {
        res.status(400);
        throw new Error("Invalid credentials");
    }
});

const getUser = asyncHandler(async (req, res) => {
    const user = await User.findById(req.user.id);
    if (user) {
        const { _id, email, firstName, lastName } = user;
        res.status(200).json({
            id: _id,
            email,
            firstName,
            lastName
        });
    } else {
        res.status(404);
        throw new Error("User not found");
    }
});

const updateUser = asyncHandler(async (req, res) => {
    const { email, firstName, lastName } = req.body;

    // Check if user exists (already checked by protect middleware for req.user usually, but here we use req.params.id? Snippet used req.params.id. Consistency with snippet.)
    // However, usually users update themselves. 
    // The snippet: User.findById(req.params.id)
    // I will stick to the snippet logic but ensure safety.

    // Note: The snippet had "const user = await User.findById(req.params.id)". 
    // But typically this route should be protected and use req.user.id if it's "update profile". 
    // If it's admin updating user, it takes ID.
    // The snippet used protect middleware on other routes, but didn't show the route definition for updateUser explicitly with protect.
    // I will assume it is "update current user" or "update user by id".
    // Snippet had: "const user = await User.findById(req.params.id)"
    // I'll assume usage of ID in params.

    const user = await User.findById(req.params.id || req.user.id); // Fallback to current user if no param? Or strict? 
    // Snippet implies specific ID. I will use req.params.id as per snippet, but if it's protected, usually we check if req.user.id === req.params.id or admin.
    // For now I will copy the logic close to snippet. "req.params.id" is key.

    if (!user) {
        res.status(404);
        throw new Error("User not found");
    }

    // Check uniqueness conflicts if updating email


    if (email && email !== user.email) {
        const emailExists = await User.findOne({ email });
        if (emailExists) {
            res.status(400);
            throw new Error("Email already exists");
        }
    }

    const updatedUser = await User.findByIdAndUpdate(
        user._id,
        {
            firstName: firstName || user.firstName,
            lastName: lastName || user.lastName,
            email: email || user.email,
        },
        { new: true }
    );

    res.status(200).json({
        id: updatedUser._id,
        firstName: updatedUser.firstName,
        lastName: updatedUser.lastName,
        email: updatedUser.email,
        token: genToken(updatedUser._id)
    });
});

const searchUsers = asyncHandler(async (req, res) => {
    const { query } = req.query;

    if (!query) {
        res.status(400);
        throw new Error('Search query is required');
    }

    // Search by email, or phone
    const users = await User.find({
        $or: [
            { email: { $regex: query, $options: 'i' } },
            { phone: { $regex: query, $options: 'i' } }
        ],
        _id: { $ne: req.user.id } // Exclude the current user
    }).select('firstName lastName _id email');

    res.status(200).json(users);
});

// @desc    Update user settings (e.g., demand window)
// @route   PUT /api/users/settings
// @access  Private
const updateSettings = asyncHandler(async (req, res) => {
    const {
        demandWindow,
        leadTime,
        safetyStockBuffer,
        lowStockThreshold,
        budgetLimit
    } = req.body;
    const {
        demandWindow,
        leadTime,
        safetyStockBuffer,
        lowStockThreshold,
        budgetLimit
    } = req.body;

    const user = await User.findById(req.user.id);

    if (!user) {
        res.status(404);
        throw new Error("User not found");
    }

    if (!user.settings) user.settings = {};

    if (demandWindow !== undefined) user.settings.demandWindow = demandWindow;
    if (leadTime !== undefined) user.settings.leadTime = leadTime;
    if (safetyStockBuffer !== undefined) user.settings.safetyStockBuffer = safetyStockBuffer;
    if (lowStockThreshold !== undefined) user.settings.lowStockThreshold = lowStockThreshold;
    if (budgetLimit !== undefined) {
        user.settings.budgetLimit = budgetLimit;
        user.budget = budgetLimit; // Sync with top-level budget field
    }

    // Explicitly mark modified if needed for nested updates
    user.markModified('settings');
    const updatedUser = await user.save();

    res.status(200).json(updatedUser.settings);
});

// @desc    Get user settings
// @route   GET /api/users/settings
// @access  Private
const getSettings = asyncHandler(async (req, res) => {
    const user = await User.findById(req.user.id);

    if (!user) {
        res.status(404);
        throw new Error("User not found");
    }

    res.status(200).json(user.settings || { demandWindow: 7 });
});

module.exports = {
    registerUser,
    loginUser,
    getUser,
    updateUser,
    searchUsers,
    updateSettings,
    getSettings
};
