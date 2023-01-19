window.addEventListener("load", function (event) {
  document.querySelectorAll("[data-panelbear]").forEach(function (el) {
    el.addEventListener("click", function () {
      if (typeof panelbear !== "undefined") {
        panelbear("track", el.dataset.panelbear);
      }
    });
  });
});
