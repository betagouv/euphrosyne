var _paq = (window._paq = window._paq || []);
/* tracker methods like "setCustomDimension" should be called before "trackPageView" */
_paq.push(["trackPageView"]);
_paq.push(["enableLinkTracking"]);
(function () {
  var u = "https://stats.beta.gouv.fr/";
  _paq.push(["setTrackerUrl", u + "piwik.php"]);
  _paq.push(["setSiteId", process.env.MATOMO_SITE_ID]);
  var d = document,
    g = d.createElement("script"),
    s = d.getElementsByTagName("script")[0];
  g.async = true;
  g.src = u + "piwik.js";
  s.parentNode.insertBefore(g, s);
})();

// Matomo Tag Manager
var _mtm = (window._mtm = window._mtm || []);
_mtm.push({ "mtm.startTime": new Date().getTime(), event: "mtm.Start" });
(function () {
  var d = document,
    g = d.createElement("script"),
    s = d.getElementsByTagName("script")[0];
  g.async = true;
  g.src = "https://stats.beta.gouv.fr/js/container_RtFSe5hb.js";
  s.parentNode.insertBefore(g, s);
})();
