window.addEventListener("pageshow", function (event) {
    if (event.persisted) {
        window.location.reload();
    }
});

window.addEventListener("pageshow", function (event) {
    if (event.persisted) {
        window.location.reload();
    }
});


function openLogoutPopup() {
    document.getElementById("logout-popup").classList.add("show");
}


function closeLogoutPopup() {
    document.getElementById("logout-popup").classList.remove("show");
}
