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


let formChanged = false;

const profileForm = document.querySelector("#profile-form");

if (profileForm) {
    const saveButton = document.querySelector("#save-button");

    const initialDisplayName = document.querySelector("#display_name").value;
    const initialEmail = document.querySelector("#email").value;

    function checkFormChanges() {
        const displayName = document.querySelector("#display_name").value;
        const email = document.querySelector("#email").value;

        const currentPassword = document.querySelector("#current_password").value;
        const newPassword = document.querySelector("#new_password").value;
        const confirmPassword = document.querySelector("#confirm_password").value;

        const hasChanges =
            displayName !== initialDisplayName ||
            email !== initialEmail ||
            currentPassword !== "" ||
            newPassword !== "" ||
            confirmPassword !== "";

        saveButton.disabled = !hasChanges;
        formChanged = hasChanges;
    }

    profileForm.addEventListener("input", checkFormChanges);

    profileForm.addEventListener("submit", function () {
        formChanged = false;
    });

    checkFormChanges();
}


window.addEventListener("beforeunload", function (event) {
    if (formChanged) {
        event.preventDefault();
        event.returnValue = "";
    }
});