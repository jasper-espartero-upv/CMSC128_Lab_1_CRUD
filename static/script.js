
const undoPopup = document.getElementById("undo-popup");
if (undoPopup) {
    setTimeout(() => {
        undoPopup.remove();

        fetch("/clear-undo", {
            method: "POST"
        });
    }, 5000);
}

const flashPopup = document.querySelector(".flash-popup");
if (flashPopup) {
    setTimeout(() => {
        flashPopup.remove();
    }, 3000);
}

const menuButtons = document.querySelectorAll(".menu-button");

menuButtons.forEach(button => {
    button.addEventListener("click", (event) => {
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

const addCard = document.getElementById("add-card");
const addModal = document.getElementById("add-modal");
const closeModal = document.getElementById("close-modal");

addCard.addEventListener("click", () => {
    addModal.style.display = "flex";
});

closeModal.addEventListener("click", () => {
    addModal.style.display = "none";
});

addModal.addEventListener("click", (event) => {
    if (event.target === addModal) {
        addModal.style.display = "none";
    }
});

const editButtons = document.querySelectorAll(".edit-button");

const editModal = document.getElementById("edit-modal");
const closeEditModal = document.getElementById("close-edit-modal");

const editForm = document.getElementById("edit-form");

const editTitle = document.getElementById("edit-title");
const editDueDate = document.getElementById("edit-due-date");
const editPriority = document.getElementById("edit-priority");
const editCategory = document.getElementById("edit-category");


editButtons.forEach(button => {

    button.addEventListener("click", () => {

        const id = button.dataset.id;

        editTitle.value = button.dataset.title;
        editDueDate.value = button.dataset.dueDate;
        editPriority.value = button.dataset.priority;
        editCategory.value = button.dataset.category;

        editForm.action = `/update/${id}`;

        editModal.style.display = "flex";

    });

});


closeEditModal.addEventListener("click", () => {
    editModal.style.display = "none";
});


editModal.addEventListener("click", (event) => {

    if (event.target === editModal) {
        editModal.style.display = "none";
    }

});
