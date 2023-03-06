import "dotenv/config";
import path from "path";
import { globSync } from "glob";
import globAll from "glob-all";
import { fileURLToPath } from "url";
import { dirname } from "path";

import MiniCssExtractPlugin from "mini-css-extract-plugin";
import CssMinimizerPlugin from "css-minimizer-webpack-plugin";
import { PurgeCSSPlugin } from "purgecss-webpack-plugin";
import webpack from "webpack";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const PATHS = {
  euphrosyne: path.join(__dirname, "euphrosyne"),
  euphro_auth: path.join(__dirname, "euphro_auth"),
  lab: path.join(__dirname, "lab"),
};

export default {
  entry: {
    main: [
      "promise-polyfill/src/polyfill",
      "whatwg-fetch",
      "./euphrosyne/assets/js/main.js",
      "@gouvfr/dsfr/dist/core/core.module.min.js",
      "@gouvfr/dsfr/dist/dsfr/dsfr.min.css",
      // We have to import each stylesheet icon separately due to a webpack
      // compile error if we import utility.css or icons.css directly.
      // See https://github.com/GouvernementFR/dsfr/issues/309
      "@gouvfr/dsfr/dist/utility/icons/icons-design/icons-design.min.css",
      "@gouvfr/dsfr/dist/utility/icons/icons-communication/icons-communication.min.css",
      "@gouvfr/dsfr/dist/utility/icons/icons-system/icons-system.min.css",
      "@gouvfr/dsfr/dist/utility/icons/icons-document/icons-document.min.css",
      "@gouvfr/dsfr/dist/utility/colors/colors.min.css",
      "remixicon/fonts/remixicon.css",
      "./euphrosyne/assets/css/base.css",
    ],
    ...Object.assign(
      {},
      ...globSync("./**/assets/js/pages/*.js", { dotRelative: true }).map(
        (file) => {
          return {
            [file.split("/").pop().split(".").shift()]: {
              import: file,
              filename: "./pages/[name].js",
            },
          };
        }
      )
    ),
  },
  output: {
    path: path.resolve(
      dirname(fileURLToPath(import.meta.url)),
      "euphrosyne/assets/dist"
    ),
    publicPath: "/static/",
    filename: "[name].js",
  },
  module: {
    rules: [
      {
        test: /\.js$/i,
        enforce: "pre",
        use: ["source-map-loader"],
      },
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
      {
        test: /\.js$/,
        enforce: "pre",
        use: ["source-map-loader"],
      },
      {
        test: /\.html$/i,
        loader: "html-loader",
      },
    ],
  },
  optimization: {
    minimizer: [new CssMinimizerPlugin()],
  },
  plugins: [
    new webpack.EnvironmentPlugin({
      MATOMO_SITE_ID: null,
      EUPHROSYNE_TOOLS_API_URL: null,
    }),
    new MiniCssExtractPlugin(),
    new PurgeCSSPlugin({
      paths: globAll.sync(
        [
          `${PATHS.euphrosyne}/**/*`,
          `${PATHS.euphro_auth}/**/*`,
          `${PATHS.lab}/**/*`,
        ],
        {
          nodir: true,
        }
      ),
    }),
  ],
};
