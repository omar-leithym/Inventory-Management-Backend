/**
 * File: userController.js
 * Description: Controller for user authentication, profile management, and settings.
 * Dependencies: express-async-handler, userModel, jwt, bcrypt, validator, libphonenumber-js
 * 
 * This controller manages user registration, login, profile updates, and
 * configurable settings for inventory management preferences.
 */

const asyncHandler = require("express-async-handler");
const User = require("../models/userModel");
const jwt = require("jsonwebtoken");
const bcrypt = require("bcrypt");
const validator = require("validator");
const { parsePhoneNumberFromString } = require("libphonenumber-js");
const passwordSchema = require("../utils/validation");

/**
 * Generate JWT token for user authentication.
 * 
 * @param {string} id - User ID
 * @returns {string} JWT token valid for 30 days
 */
const genToken = (id) => {
    return jwt.sign({ id }, process.env.JWT_SECRET, {
        expiresIn: "30d"
    });
};

/**
 * Register a new user account.
 * 
 * Validates user input, checks for existing accounts, and creates
 * a new user with hashed password.
 * 
 * @route   POST /api/users/register
 * @access  Public
 */
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

/**
 * Authenticate user and return token.
 * 
 * Verifies credentials and returns JWT for subsequent requests.
 * 
 * @route   POST /api/users/login
 * @access  Public
 */
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

/**
 * Get authenticated user profile.
 * 
 * Returns user details for the currently logged-in user.
 * 
 * @route   GET /api/users/getuser
 * @access  Private
 */
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

/**
 * Update user profile information.
 * 
 * Allows users to update their email, first name, and last name.
 * Validates email uniqueness before updating.
 * 
 * @route   PATCH /api/users/updateuser/:id
 * @access  Private
 */
const updateUser = asyncHandler(async (req, res) => {
    const { email, firstName, lastName } = req.body;

    const user = await User.findById(req.params.id || req.user.id);

    if (!user) {
        res.status(404);
        throw new Error("User not found");
    }

    // Check email uniqueness if updating email
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

/**
 * Search for users by email or phone.
 * 
 * Performs case-insensitive search and excludes current user from results.
 * 
 * @route   GET /api/users/search
 * @access  Private
 */
const searchUsers = asyncHandler(async (req, res) => {
    const { query } = req.query;

    if (!query) {
        res.status(400);
        throw new Error('Search query is required');
    }

    // Search by email or phone
    const users = await User.find({
        $or: [
            { email: { $regex: query, $options: 'i' } },
            { phone: { $regex: query, $options: 'i' } }
        ],
        _id: { $ne: req.user.id }
    }).select('firstName lastName _id email');

    res.status(200).json(users);
});

/**
 * Update user inventory management settings.
 * 
 * Allows users to configure demand window, lead time, safety stock buffer,
 * low stock threshold, and budget limits for personalized recommendations.
 * 
 * @route   PUT /api/users/settings
 * @access  Private
 */
const updateSettings = asyncHandler(async (req, res) => {
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
        user.budget = budgetLimit;
    }

    // Mark nested field as modified for Mongoose
    user.markModified('settings');
    const updatedUser = await user.save();

    res.status(200).json(updatedUser.settings);
});

/**
 * Get user inventory management settings.
 * 
 * Returns current configuration for demand forecasting and stock management.
 * 
 * @route   GET /api/users/settings
 * @access  Private
 */
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