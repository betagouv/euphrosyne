const path = require("path");
const glob = require("glob");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const CssMinimizerPlugin = require("css-minimizer-webpack-plugin");

module.exports = {
  entry: {
    main: [
      "./node_modules/@gouvfr/dsfr/dist/core/core.min.css",
      "./euphrosyne/assets/css/base.css",
    ],
    ...Object.assign(
      {},
      ...glob.sync("./**/assets/js/pages/*.js").map((file) => {
        return {
          [file.split("/").pop().split(".").shift()]: {
            import: file,
            filename: "./pages/[name].js",
          },
        };
      })
    ),
  },
  output: {
    path: path.resolve(__dirname, "euphrosyne/assets/dist"),
    publicPath: "/static/",
    filename: "[name].js",
  },
  module: {
    rules: [
      {
        test: /\.css$/i,
        use: [MiniCssExtractPlugin.loader, "css-loader"],
      },
      {
        test: /\.(woff(2)?|ttf|eot)$/,
        type: "asset/resource",
        generator: {
          filename: "./fonts/[name][ext]",
        },
      },
    ],
  },
  optimization: {
    minimizer: [new CssMinimizerPlugin()],
  },
  plugins: [new MiniCssExtractPlugin()],
};
