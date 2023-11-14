window.onload = function() {
    var table = document.querySelector('table');
    var scroll = document.querySelector('.scroll');
  
    scroll.addEventListener('click', function(e) {
      e.preventDefault();
      table.scrollIntoView({ behavior: 'smooth' });
    });
  };