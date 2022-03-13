import path from "path";
import glob from "glob";
import globAll from "glob-all";
import { fileURLToPath } from "url";
import { dirname } from "path";

import MiniCssExtractPlugin from "mini-css-extract-plugin";
import CssMinimizerPlugin from "css-minimizer-webpack-plugin";
import PurgecssPlugin from "purgecss-webpack-plugin";

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
      "@gouvfr/dsfr/dist/core/core.module.min.js",
      "@gouvfr/dsfr/dist/dsfr/dsfr.min.css",
      "remixicon/fonts/remixicon.css",
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
    new MiniCssExtractPlugin(),
    new PurgecssPlugin({
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
