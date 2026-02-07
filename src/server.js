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
// Connect to MongoDB and start server
mongoose.connect(process.env.MONGO_URI)
    .then(() => {
        app.listen(PORT, () => {
            console.log(`Server running on port ${PORT}`);
            startPythonServer();
        });
    })
    .catch((err) => console.log(err));

// Spawn Python API
const { spawn } = require("child_process");

let pythonProcess = null;

const startPythonServer = () => {
    // Check if python is available, otherwise use python3
    const command = process.platform === "win32" ? "python" : "python3";

    // Adjust path to src/api/discount_prediction.py
    // Assuming we are running from root, path is src/api/discount_prediction.py
    // If running from src, we might need adjustments, but standard is root.
    // However, the python script expects to be run as a module from root?
    // Let's try running it as a file first, or module if __init__ exists (it does).
    // The user said "on @[src/api]", and there is an __init__.py in src/api.
    // Correct way to run as module from root: python -m src.api.discount_prediction

    pythonProcess = spawn(command, ["-m", "src.api.discount_prediction"], {
        cwd: process.cwd(), // Ensure we run from the project root
        env: { ...process.env, PORT: "8000" } // Explicitly set Python port if needed, though script defaults to 8000 or env.PORT. 
        // CAUTION: process.env.PORT is likely 5000 for Node. Node uses 5000. 
        // Python script uses os.getenv("PORT", "8000"). If we inherit env, it sees 5000.
        // We MUST override PORT for Python to avoid conflict if Node is on 5000.
        // But wait, the Python script: app.run(port=int(os.getenv("PORT", "8000"))).
        // If we pass 8000 here, it will use 8000.
    });

    pythonProcess.stdout.on("data", (data) => {
        console.log(`[Python API]: ${data}`);
    });

    pythonProcess.stderr.on("data", (data) => {
        console.error(`[Python API Error]: ${data}`);
    });

    pythonProcess.on("close", (code) => {
        console.log(`[Python API] exited with code ${code}`);
    });
};

// Graceful shutdown
const cleanup = () => {
    if (pythonProcess) {
        console.log("Stopping Python API...");
        pythonProcess.kill();
    }
    process.exit();
};

process.on("SIGINT", cleanup);
process.on("SIGTERM", cleanup);
