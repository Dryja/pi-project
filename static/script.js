document.addEventListener("DOMContentLoaded",()=>{const $navbarBurgers=Array.prototype.slice.call(document.querySelectorAll(".navbar-burger"),0);$navbarBurgers.length>0&&$navbarBurgers.forEach(el=>{el.addEventListener("click",()=>{const target=el.dataset.target,$target=document.getElementById(target);el.classList.toggle("is-active"),$target.classList.toggle("is-active")})});const html=document.querySelector("html"),$modals=Array.prototype.slice.call(document.querySelectorAll(".modal-open"),0);$modals.length>0&&$modals.forEach(el=>{el.addEventListener("click",()=>{const modals=el.parentNode.getElementsByClassName("modal");if(modals.length>0){const modal=modals[0];modal.classList.add("is-active"),html.classList.add("is-clipped"),modal.getElementsByClassName("modal-close")[0].addEventListener("click",function(e){modal.classList.remove("is-active"),html.classList.remove("is-clipped"),clone=modal.cloneNode(!0)}),modal.getElementsByClassName("modal-background")[0].addEventListener("click",function(e){e.preventDefault(),modal.classList.remove("is-active"),html.classList.remove("is-clipped"),clone=modal.cloneNode(!0)})}})})});