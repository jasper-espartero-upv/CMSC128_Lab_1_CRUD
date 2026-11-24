// ==================== UNDO POPUP ====================

const undoPopup = document.getElementById("undo-popup");

if (undoPopup) {
    setTimeout(() => {
        undoPopup.remove();

        fetch("/clear-undo", {
            method: "POST"
        });
    }, 5000);
}


// ==================== FLASH POPUP ====================

const flashPopup = document.querySelector(".flash-popup");

if (flashPopup) {
    setTimeout(() => {
        flashPopup.remove();
    }, 3000);
}


// ==================== TASK MENU ====================

const menuButtons = document.querySelectorAll(".menu-button");

menuButtons.forEach(button => {
    button.addEventListener("click", event => {
        event.stopPropagation();

        const menu = button.parentElement;

        document.querySelectorAll(".task-menu").forEach(otherMenu => {
            if (otherMenu !== menu) {
                otherMenu.classList.remove("active");
            }
        });

        menu.classList.toggle("active");
    });
});

document.addEventListener("click", () => {
    document.querySelectorAll(".task-menu").forEach(menu => {
        menu.classList.remove("active");
    });
});


// ==================== ADD MODAL ====================

const addCard = document.getElementById("add-card");
const addModal = document.getElementById("add-modal");
const closeModal = document.getElementById("close-modal");

if (addCard && addModal) {
    addCard.addEventListener("click", () => {
        addModal.style.display = "flex";
    });
}

if (closeModal && addModal) {
    closeModal.addEventListener("click", () => {
        addModal.style.display = "none";
    });
}

if (addModal) {
    addModal.addEventListener("click", event => {
        if (event.target === addModal) {
            addModal.style.display = "none";
        }
    });
}


// ==================== EDIT MODAL ====================

const editButtons = document.querySelectorAll(".edit-button");

const editModal = document.getElementById("edit-modal");
const closeEditModal = document.getElementById("close-edit-modal");
const editForm = document.getElementById("edit-form");

const editTitle = document.getElementById("edit-title");
const editDueDate = document.getElementById("edit-due-date");
const editPriority = document.getElementById("edit-priority");
const editCategory = document.getElementById("edit-category");

if (editModal && editForm) {
    editButtons.forEach(button => {
        button.addEventListener("click", () => {
            const id = button.dataset.id;

            if (editTitle) {
                editTitle.value = button.dataset.title || "";
            }

            if (editDueDate) {
                editDueDate.value = button.dataset.dueDate || "";
            }

            if (editPriority) {
                editPriority.value = button.dataset.priority || "";
            }

            if (editCategory) {
                editCategory.value = button.dataset.category || "";
            }

            editForm.action = `/update/${id}`;
            editModal.style.display = "flex";
        });
    });
}

if (closeEditModal && editModal) {
    closeEditModal.addEventListener("click", () => {
        editModal.style.display = "none";
    });
}

if (editModal) {
    editModal.addEventListener("click", event => {
        if (event.target === editModal) {
            editModal.style.display = "none";
        }
    });
}


// ==================== ACCOUNT PAGE: BACK/FORWARD CACHE ====================

window.addEventListener("pageshow", event => {
    if (event.persisted) {
        window.location.reload();
    }
});


// ==================== LOGOUT POPUP ====================

function openLogoutPopup() {
    const logoutPopup = document.getElementById("logout-popup");

    if (logoutPopup) {
        logoutPopup.classList.add("show");
    }
}

function closeLogoutPopup() {
    const logoutPopup = document.getElementById("logout-popup");

    if (logoutPopup) {
        logoutPopup.classList.remove("show");
    }
}


// ==================== PROFILE FORM ====================

let formChanged = false;

const profileForm = document.querySelector("#profile-form");

if (profileForm) {
    const saveButton = document.querySelector("#save-button");

    const displayNameInput = document.querySelector("#display_name");
    const emailInput = document.querySelector("#email");
    const currentPasswordInput = document.querySelector("#current_password");
    const newPasswordInput = document.querySelector("#new_password");
    const confirmPasswordInput = document.querySelector("#confirm_password");

    const initialDisplayName = displayNameInput?.value ?? "";
    const initialEmail = emailInput?.value ?? "";

    function checkFormChanges() {
        const displayName = displayNameInput?.value ?? "";
        const email = emailInput?.value ?? "";

        const currentPassword = currentPasswordInput?.value ?? "";
        const newPassword = newPasswordInput?.value ?? "";
        const confirmPassword = confirmPasswordInput?.value ?? "";

        const hasChanges =
            displayName !== initialDisplayName ||
            email !== initialEmail ||
            currentPassword !== "" ||
            newPassword !== "" ||
            confirmPassword !== "";

        if (saveButton) {
            saveButton.disabled = !hasChanges;
        }

        formChanged = hasChanges;
    }

    profileForm.addEventListener("input", checkFormChanges);

    profileForm.addEventListener("submit", () => {
        formChanged = false;
    });

    checkFormChanges();
}


// ==================== UNSAVED PROFILE CHANGES WARNING ====================

window.addEventListener("beforeunload", event => {
    if (formChanged) {
        event.preventDefault();
        event.returnValue = "";
    }
});

// ==================== LIST DROPDOWN ====================

const listDropdownButton = document.getElementById("list-dropdown-button");
const listDropdownMenu = document.getElementById("list-dropdown-menu");

if (listDropdownButton && listDropdownMenu) {

    // Open or close the dropdown when the arrow is clicked
    listDropdownButton.addEventListener("click", function (event) {
        event.stopPropagation();

        const isOpen = listDropdownMenu.style.display === "block";

        listDropdownMenu.style.display = isOpen ? "none" : "block";
    });

    // Close the dropdown when clicking outside it
    document.addEventListener("click", function (event) {
        if (
            !listDropdownButton.contains(event.target) &&
            !listDropdownMenu.contains(event.target)
        ) {
            listDropdownMenu.style.display = "none";
        }
    });

}


/* ==================== COLLABORATOR MODAL ==================== */

const openCollaboratorModal = document.getElementById("open-collaborator-modal");
const closeCollaboratorModal = document.getElementById("close-collaborator-modal");
const collaboratorModal = document.getElementById("collaborator-modal");

if (openCollaboratorModal && closeCollaboratorModal && collaboratorModal) {
    openCollaboratorModal.addEventListener("click", function () {
        collaboratorModal.style.display = "flex";
    });

    closeCollaboratorModal.addEventListener("click", function () {
        collaboratorModal.style.display = "none";
    });

    collaboratorModal.addEventListener("click", function (event) {
        if (event.target === collaboratorModal) {
            collaboratorModal.style.display = "none";
        }
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            collaboratorModal.style.display = "none";
        }
    });
}


// ==================== PASSWORD REQUIREMENTS ====================

const passwordInput = document.getElementById("password");

if (passwordInput) {
    passwordInput.addEventListener("input", function () {
        const password = passwordInput.value;

        updatePasswordCheck(
            "length-check",
            password.length >= 8
        );

        updatePasswordCheck(
            "uppercase-check",
            /[A-Z]/.test(password)
        );

        updatePasswordCheck(
            "lowercase-check",
            /[a-z]/.test(password)
        );

        updatePasswordCheck(
            "number-check",
            /[0-9]/.test(password)
        );

        updatePasswordCheck(
            "special-check",
            /[^A-Za-z0-9]/.test(password)
        );

        const allValid =
            password.length >= 8 &&
            /[A-Z]/.test(password) &&
            /[a-z]/.test(password) &&
            /[0-9]/.test(password) &&
            /[^A-Za-z0-9]/.test(password);

        const status = document.getElementById("password-status");

        if (allValid) {
            status.textContent = "Password meets all requirements";
            status.classList.add("password-valid");
        } else {
            status.textContent = "Password requirements:";
            status.classList.remove("password-valid");
        }
    });
}

function updatePasswordCheck(id, valid) {
    const check = document.getElementById(id);
    const light = check.querySelector(".check-light");

    if (valid) {
        light.classList.add("valid");
    } else {
        light.classList.remove("valid");
    }
}

// ==================== PASSWORD VISIBILITY ====================

document.querySelectorAll(".toggle-password").forEach(function (button) {
    button.addEventListener("click", function () {
        const password = document.getElementById(button.dataset.target);
        const icon = button.querySelector("img");

        if (password.type === "password") {
            password.type = "text";
            icon.src = "/static/images/eye_off_icon.png";
        } else {
            password.type = "password";
            icon.src = "/static/images/eye_icon.png";
        }
    });
});

// ==================== DELETE MODAL ====================

const deleteModal = document.getElementById("delete-modal");
const cancelDelete = document.getElementById("cancel-delete");
const deleteForm = document.getElementById("delete-form");
const deleteTaskTitle = document.getElementById("delete-task-title");

document.querySelectorAll(".delete-button").forEach(function (button) {
    button.addEventListener("click", function () {
        const todoId = button.dataset.id;
        const todoTitle = button.dataset.title;

        deleteTaskTitle.textContent = todoTitle;
        deleteForm.action = "/delete/" + todoId;

        deleteModal.style.display = "flex";
    });
});

cancelDelete.addEventListener("click", function () {
    deleteModal.style.display = "none";
});

deleteModal.addEventListener("click", function (event) {
    if (event.target === deleteModal) {
        deleteModal.style.display = "none";
    }
});