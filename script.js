(function () {
  "use strict";

  var header = document.getElementById("site-header");
  var onScroll = function () {
    header.classList.toggle("is-scrolled", window.scrollY > 4);
  };
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  var navToggle = document.getElementById("nav-toggle");
  var siteNav = document.getElementById("site-nav");
  navToggle.addEventListener("click", function () {
    var open = siteNav.classList.toggle("is-open");
    navToggle.setAttribute("aria-expanded", String(open));
  });
  var closeMenu = function () {
    siteNav.classList.remove("is-open");
    navToggle.setAttribute("aria-expanded", "false");
  };
  siteNav.querySelectorAll("a").forEach(function (link) {
    link.addEventListener("click", closeMenu);
  });
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closeMenu();
  });
  document.addEventListener("click", function (event) {
    if (!siteNav.classList.contains("is-open")) return;
    if (!siteNav.contains(event.target) && !navToggle.contains(event.target)) closeMenu();
  });

  var themeToggle = document.getElementById("theme-toggle");
  var root = document.documentElement;
  var syncThemeButton = function () {
    var current = root.getAttribute("data-theme");
    var prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    var isDark = current ? current === "dark" : prefersDark;
    themeToggle.setAttribute("aria-pressed", String(isDark));
    themeToggle.setAttribute("aria-label", isDark ? "Включить светлую тему" : "Включить тёмную тему");
  };
  syncThemeButton();
  themeToggle.addEventListener("click", function () {
    var current = root.getAttribute("data-theme");
    var prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    var isDark = current ? current === "dark" : prefersDark;
    var next = isDark ? "light" : "dark";
    root.setAttribute("data-theme", next);
    localStorage.setItem("bs-theme", next);
    syncThemeButton();
  });

  if ("IntersectionObserver" in window) {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
    );
    document.querySelectorAll(".reveal").forEach(function (el) {
      observer.observe(el);
    });
  } else {
    document.querySelectorAll(".reveal").forEach(function (el) {
      el.classList.add("is-visible");
    });
  }

  var track = document.getElementById("screenshot-track");
  var prev = document.getElementById("gallery-prev");
  var next = document.getElementById("gallery-next");
  if (track && prev && next) {
    var originals = Array.from(track.querySelectorAll(".screenshot-card"));
    var prependFragment = document.createDocumentFragment();
    var appendFragment = document.createDocumentFragment();

    originals.forEach(function (card) {
      var before = card.cloneNode(true);
      var after = card.cloneNode(true);
      before.setAttribute("aria-hidden", "true");
      after.setAttribute("aria-hidden", "true");
      before.querySelectorAll("img").forEach(function (image) { image.loading = "lazy"; });
      after.querySelectorAll("img").forEach(function (image) { image.loading = "lazy"; });
      prependFragment.appendChild(before);
      appendFragment.appendChild(after);
    });
    track.insertBefore(prependFragment, track.firstChild);
    track.appendChild(appendFragment);

    var setWidth = 0;
    var originalStart = 0;
    var normalizeCarousel = function () {
      if (!setWidth) return;
      if (track.scrollLeft < originalStart - setWidth * 0.5) {
        track.scrollLeft += setWidth;
      } else if (track.scrollLeft >= originalStart + setWidth * 1.5) {
        track.scrollLeft -= setWidth;
      }
    };
    var measureCarousel = function () {
      var firstOriginal = originals[0];
      var firstTrailingClone = track.children[originals.length * 2];
      if (!firstOriginal || !firstTrailingClone) return;
      originalStart = firstOriginal.offsetLeft;
      setWidth = firstTrailingClone.offsetLeft - originalStart;
      track.scrollLeft = originalStart;
    };
    requestAnimationFrame(measureCarousel);
    window.addEventListener("resize", function () {
      requestAnimationFrame(measureCarousel);
    });

    var scrollTimer = 0;
    track.addEventListener("scroll", function () {
      window.clearTimeout(scrollTimer);
      scrollTimer = window.setTimeout(normalizeCarousel, 140);
    }, { passive: true });

    var scrollByCard = function (direction) {
      var card = track.querySelector(".screenshot-card");
      var amount = card ? card.getBoundingClientRect().width + 24 : 300;
      track.scrollBy({ left: amount * direction, behavior: "smooth" });
    };
    prev.addEventListener("click", function () { scrollByCard(-1); });
    next.addEventListener("click", function () { scrollByCard(1); });
  }

  var yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = String(new Date().getFullYear());
})();
