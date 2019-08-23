MathJax.Hub.Config({
    extensions: ["tex2jax.js"],
    jax: ["input/TeX", "output/HTML-CSS"],
    tex2jax: {
          inlineMath: [ ['$','$'], ["\\(","\\)"] ],
          displayMath: [ ['$$','$$'], ["\\[","\\]"] ],
          processEscapes: true
    },
    TeX: {
    equationNumbers: { 
      autoNumber: "AMS",
      formatNumber: function (n) { return n }
    },
    Commands: {
      RR: "{\\bf R}",
      pounds: '{\\unicode{xA3}}',
    }
  },
  "HTML-CSS": {
  availableFonts: ["TeX"],
  linebreaks: { 
    automatic: true, 
    width: "container"
  }
}
});
