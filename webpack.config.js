const path = require("path");
const glob = require("glob");
module.exports = {
  entry: {
    main: {
      import: "./euphrosyne/assets/js/main.js",
      filename: "../[name].js",
    },
    ...Object.assign(
      {},
      ...glob.sync("./**/assets/js/pages/*.js").map((file) => {
        return { [file.split("/").pop().split(".").shift()]: file };
      })
    ),
  },
  output: {
    path: path.resolve(__dirname, "euphrosyne/assets/dist/pages"),
    publicPath: "/static/pages/",
    filename: "[name].js",
    chunkFilename: "[id]-[chunkhash].js",
  },
  devServer: {
    port: 8081,
    devMiddleware: {
      writeToDisk: true,
    },
  },
  module: {
    rules: [
      {
        test: /\.css$/i,
        use: ["style-loader", "css-loader"],
      },
      {
        test: /\.s[ac]ss$/i,
        use: ["style-loader", "css-loader", "sass-loader"],
      },
    ],
  },
};
