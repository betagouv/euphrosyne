import "dotenv/config";
import path from "path";
import { globSync } from "glob";
import { fileURLToPath } from "url";
import { dirname } from "path";

import MiniCssExtractPlugin from "mini-css-extract-plugin";
import CssMinimizerPlugin from "css-minimizer-webpack-plugin";
import { PurgeCSSPlugin } from "purgecss-webpack-plugin";
import webpack from "webpack";

export default {
  entry: {
    main: [
      "promise-polyfill/src/polyfill",
      "whatwg-fetch",
      "./euphrosyne/assets/js/main.ts",
      "./euphrosyne/assets/css/base.css",
    ],
    anonymous: [
      "./euphrosyne/assets/js/anonymous.ts",
      "./euphrosyne/assets/css/base.css",
    ],
    dsfr: [
      "@gouvfr/dsfr/dist/dsfr/dsfr.min.css",
      "@gouvfr/dsfr/dist/dsfr.module.min.js",
    ],
    icons: [
      // We have to import each stylesheet icon separately due to a webpack
      // compile error if we import utility.css or icons.css directly.
      // See https://github.com/GouvernementFR/dsfr/issues/309
      "@gouvfr/dsfr/dist/utility/icons/icons-design/icons-design.min.css",
      "@gouvfr/dsfr/dist/utility/icons/icons-communication/icons-communication.min.css",
      "@gouvfr/dsfr/dist/utility/icons/icons-system/icons-system.min.css",
      "@gouvfr/dsfr/dist/utility/icons/icons-document/icons-document.min.css",
      "@gouvfr/dsfr/dist/utility/icons/icons-business/icons-business.min.css",
      "@gouvfr/dsfr/dist/utility/icons/icons-user/icons-user.min.css",
      "@gouvfr/dsfr/dist/utility/icons/icons-map/icons-map.min.css",
      "@gouvfr/dsfr/dist/utility/icons/icons-media/icons-media.min.css",
      "@gouvfr/dsfr/dist/utility/colors/colors.min.css",
      "remixicon/fonts/remixicon.css",
    ],
    hdf5: ["@h5web/app/styles.css"],
    // js/ts page files
    ...Object.assign(
      {},
      ...globSync("./**/assets/js/pages/*.{js,ts}", { dotRelative: true }).map(
        (file) => {
          return {
            [file.split("/").pop().split(".").shift()]: {
              import: file,
              filename: "./pages/[name].js",
            },
          };
        },
      ),
    ),
    // js/ts web-components files
    ...Object.assign(
      {},
      ...globSync("./**/assets/js/web-components/*.{js,ts}", {
        dotRelative: true,
      }).map((file) => {
        return {
          [file.split("/").pop().split(".").shift()]: {
            import: file,
            filename: "./web-components/[name].js",
          },
        };
      }),
    ),
  },
  output: {
    path: path.resolve(
      dirname(fileURLToPath(import.meta.url)),
      "euphrosyne/assets/dist",
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
        test: /\.tsx?$/,
        use: "ts-loader",
        exclude: /node_modules/,
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
  resolve: {
    extensions: [".ts", ".tsx", ".js"],
  },
  optimization: {
    minimizer: [new CssMinimizerPlugin()],
  },
  plugins: [
    new webpack.EnvironmentPlugin({
      MATOMO_SITE_ID: null,
      EUPHROSYNE_TOOLS_API_URL: null,
      GEONAMES_USERNAME: "",
      HDF5_ENABLE: "false",
    }),
    new MiniCssExtractPlugin(),
    new PurgeCSSPlugin({
      paths: globSync([`{euphrosyne,euphro_auth,lab}/**/*`], {
        nodir: true,
        dotRelative: true,
      }),
      safelist: {
        greedy: [/^fr-/],
      },
      only: ["main", "anonymous", "dsfr", "icons"],
    }),
  ],
  devtool: "source-map",
};
