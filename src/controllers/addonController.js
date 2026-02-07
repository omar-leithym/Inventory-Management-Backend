/**
 * File: addonController.js
 * Description: Controller for managing addon items.
 * Dependencies: express-async-handler, addonModel
 * Author: Sample Team
 */

const asyncHandler = require("express-async-handler");
const Addon = require("../models/addonModel");

/**
 * Retrieves all addons, optionally filtered by a search query.
 * 
 * Query Params:
 *     search (string): Optional search term to filter addons by title.
 * 
 * Returns:
 *     Array: List of addon objects.
 * 
 * Example Response:
 *     [
 *         {
 *             "_id": "64e5f...",
 *             "title": "Extra Cheese",
 *             "price": 1.50
 *         }
 *     ]
 * 
 * @route   GET /api/addons
 * @access  Private
 */
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
