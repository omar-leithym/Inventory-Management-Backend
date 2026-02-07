/**
 * File: menuItemController.js
 * Description: Controller for managing menu items.
 * Dependencies: express-async-handler, menuItemModel
 * Author: Sample Team
 */

const asyncHandler = require("express-async-handler");
const MenuItem = require("../models/menuItemModel");

/**
 * Retrieves all menu items, optionally filtered by a search query.
 * 
 * Query Params:
 *     search (string): Optional search term to filter items by title.
 * 
 * Returns:
 *     Array: List of menu item objects.
 * 
 * Example Response:
 *     [
 *         {
 *             "_id": "64e5f...",
 *             "title": "Classic Burger",
 *             "price": 8.99
 *         }
 *     ]
 * 
 * @route   GET /api/menu-items
 * @access  Private
 */
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
