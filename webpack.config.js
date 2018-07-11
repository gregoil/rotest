const path = require("path");

module.exports = {
    devtool: "source-map",
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
                test: /\.(jpe?g|png|gif|svg)$/i,
                loader: "file-loader",
                options: {
                    name: "[name].[ext]",
                    outputPath: "img/",
                    publicPath: "static/img/"
                }
            },
            {
                test: /\.css$/,
                loaders: ["style-loader", "css-loader"]
            }
        ]
    }
}