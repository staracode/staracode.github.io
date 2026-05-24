function showRegion() {
  const regions = document.querySelectorAll(".content-region");
  const links = document.querySelectorAll(".main-menu a");
  const fallback = links[0] ? links[0].getAttribute("href") : "";
  const requestedRegion = window.location.hash || fallback;
  const validRegions = Array.from(regions).map((region) => "#" + region.id);
  const target = validRegions.includes(requestedRegion) ? requestedRegion : fallback;

  regions.forEach((region) => {
    region.classList.toggle("show", "#" + region.id === target);
    region.classList.toggle("hide", "#" + region.id !== target);
  });

  links.forEach((link) => {
    link.classList.toggle("active", link.getAttribute("href") === target);
  });
}

window.addEventListener("DOMContentLoaded", showRegion);
window.addEventListener("hashchange", showRegion);
