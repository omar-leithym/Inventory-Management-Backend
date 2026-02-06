const asyncHandler = require("express-async-handler");
const MenuItem = require("../models/menuItemModel");

// @desc    Get all menu items
// @route   GET /api/menu-items
// @access  Private
const getMenuItems = asyncHandler(async (req, res) => {
    const { search } = req.query;
    let query = {};

    if (search) {
        query.title = { $regex: search, $options: "i" };
    }

    const menuItems = await MenuItem.find(query).select("_id title price");
    res.status(200).json(menuItems);
});

module.exports = {
    getMenuItems
};
