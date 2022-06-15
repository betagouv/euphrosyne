const htmlLoader = require("html-loader");

module.exports = {
  process(sourceText) {
    return {
      code: `module.exports = ${htmlLoader(sourceText)};`,
    };
  },
};
