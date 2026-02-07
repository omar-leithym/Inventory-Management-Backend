const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
const dotenv = require("dotenv").config();
const errorHandler = require("./middleware/errorMiddleware");
const userRoutes = require("./routes/userRoutes");

const app = express();

const PORT = process.env.PORT || 5000;

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.use(cors());

// Routes
app.use("/api/users", userRoutes);
app.use("/api/stock", require("./routes/stockRoutes"));
app.use("/api/sales", require("./routes/saleRoutes"));
app.use("/api/analytics", require("./routes/analyticsRoutes"));
app.use("/api/menu-items", require("./routes/menuItemRoutes"));
app.use("/api/addons", require("./routes/addonRoutes"));

// Error Middleware
app.use(errorHandler);

// Connect to MongoDB and start server
mongoose.connect(process.env.MONGO_URI)
    .then(() => {
        app.listen(PORT, () => {
            console.log(`Server running on port ${PORT}`);
        });
    })
    .catch((err) => console.log(err));
