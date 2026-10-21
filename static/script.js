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
