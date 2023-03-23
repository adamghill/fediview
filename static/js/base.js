window.addEventListener("load", function () {
  document.querySelectorAll("[data-track]").forEach(function (el) {
    if (el && el.dataset && el.dataset.track) {
      el.addEventListener("click", function () {
        if (typeof panelbear !== "undefined") {
          cronitor("track", el.dataset.track);
        }
      });
    }
  });
});
