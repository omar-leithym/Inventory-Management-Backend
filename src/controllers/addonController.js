const asyncHandler = require("express-async-handler");
const Addon = require("../models/addonModel");

// @desc    Get all addons
// @route   GET /api/addons
// @access  Private
const getAddons = asyncHandler(async (req, res) => {
    const { search } = req.query;
    let query = {};

    if (search) {
        query.title = { $regex: search, $options: "i" };
    }

    const addons = await Addon.find(query).select("_id title price");
    res.status(200).json(addons);
});

module.exports = {
    getAddons
};
