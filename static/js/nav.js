document.addEventListener('DOMContentLoaded', function() {
  var navToggle = document.querySelector('.nav-mobile .nav-toggle');
  var navDropdown = document.querySelector('.nav-mobile .nav-dropdown-menu');
  if(navToggle && navDropdown) {
    navToggle.addEventListener('click', function(e) {
      e.preventDefault();
      navDropdown.classList.toggle('open');
    });
  }
});
