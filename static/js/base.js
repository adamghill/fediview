window.addEventListener("load", function () {
  document.querySelectorAll("[data-panelbear]").forEach(function (el) {
    if (el && el.dataset && el.dataset.panelbear) {
      el.addEventListener("click", function () {
        if (typeof panelbear !== "undefined") {
          panelbear("track", el.dataset.panelbear);
        }
      });
    }
  });
});
