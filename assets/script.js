document.addEventListener('DOMContentLoaded', () => {

    // Get all "navbar-burger" elements
    const $navbarBurgers = Array.prototype.slice.call(document.querySelectorAll('.navbar-burger'), 0);
  
    // Check if there are any navbar burgers
    if ($navbarBurgers.length > 0) {
  
      // Add a click event on each of them
      $navbarBurgers.forEach( el => {
        el.addEventListener('click', () => {
  
          // Get the target from the "data-target" attribute
          const target = el.dataset.target;
          const $target = document.getElementById(target);
  
          // Toggle the "is-active" class on both the "navbar-burger" and the "navbar-menu"
          el.classList.toggle('is-active');
          $target.classList.toggle('is-active');
  
        });
      });
    }
    const html = document.querySelector('html');
    // Get all "modals openers"
    const $modals = Array.prototype.slice.call(document.querySelectorAll('.modal-open'), 0);
    if ($modals.length > 0){
      $modals.forEach( el => {
        el.addEventListener('click', () => {
          const modals =  el.parentNode.getElementsByClassName("modal");
          if (modals.length>0){
            const modal = modals[0];
            modal.classList.add('is-active'); // open first modal (should be only one)
            html.classList.add('is-clipped');
            modal.getElementsByClassName('modal-close')[0].addEventListener('click', function(e){
              modal.classList.remove('is-active');
              html.classList.remove('is-clipped');
              clone = modal.cloneNode(true);
            });
            modal.getElementsByClassName('modal-background')[0].addEventListener('click', function(e){
              e.preventDefault();
              modal.classList.remove('is-active');
              html.classList.remove('is-clipped');
              clone = modal.cloneNode(true);
            });
          }
        });
      });
    }
  });