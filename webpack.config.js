const path = require("path");

module.exports = {
    entry: "./frontend/index.js",
    output: {
        filename: "bundle.js",
        path: path.resolve(__dirname, "src", "rotest", "frontend", "static")
    },
    module: {
        rules: [
            {
                test: /\.jsx?/,
                include: path.resolve(__dirname, "frontend"),
                loader: "babel-loader"
            },
            {
                test: /\.(jpe?g|png|gif)$/i,
                loader: "file-loader",
                options: {
                    name: "[name].[ext]",
                    outputPath: "static/img/"
                }
            },
            {
                test: /\.css$/,
                loaders: ["style-loader", "css-loader"]
            }
        ]
    }
}