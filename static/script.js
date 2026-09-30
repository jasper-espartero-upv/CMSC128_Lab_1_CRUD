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

const profileForm = document.querySelector("#profile-form");

if (profileForm) {
    let formChanged = false;

    profileForm.addEventListener("input", function () {
        formChanged = true;
    });

    profileForm.addEventListener("submit", function () {
        formChanged = false;
    });

    window.addEventListener("beforeunload", function (event) {
        if (formChanged) {
            event.preventDefault();
            event.returnValue = "";
        }
    });
}