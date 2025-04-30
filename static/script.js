// DOM Elements
const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const uploadBtn = document.getElementById("upload-btn");
let selectedFile = null;

// ===== Drag & Drop Functionality =====
// Highlight drop zone when dragging over
["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

["dragenter", "dragover"].forEach((eventName) => {
    dropZone.addEventListener(eventName, highlight, false);
});

["dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(eventName, unhighlight, false);
});

function highlight() {
    dropZone.classList.add("drop-zone--over");
}

function unhighlight() {
    dropZone.classList.remove("drop-zone--over");
}

// Handle dropped files
dropZone.addEventListener("drop", handleDrop, false);

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
}

// Handle clicked files
dropZone.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", function () {
    handleFiles(this.files);
});

let selectedFiles = [];

function handleFiles(files) {
    if (files.length > 0) {
        selectedFiles = Array.from(files); // Convert FileList to Array
        const fileNames = selectedFiles.map((file) => file.name).join(", ");
        dropZone.querySelector(
            ".drop-zone__prompt"
        ).textContent = `${selectedFiles.length} files selected: ${fileNames}`;
    }
}

// ===== Upload Functionality =====
uploadBtn.addEventListener("click", async () => {
    if (selectedFiles.length === 0) {
        alert("Please select at least one file");
        return;
    }

    try {
        // Create progress UI
        const progressContainer = document.createElement("div");
        progressContainer.className = "upload-progress mt-3";
        document.querySelector(".upload-area").appendChild(progressContainer);

        // Upload files sequentially
        for (let i = 0; i < selectedFiles.length; i++) {
            const file = selectedFiles[i];
            const progress = document.createElement("div");
            progress.className = "mb-2";
            progress.innerHTML = `
                <div class="d-flex justify-content-between">
                    <span>${file.name}</span>
                    <span class="status">Uploading...</span>
                </div>
                <div class="progress" style="height: 5px;">
                    <div class="progress-bar" role="progressbar" style="width: 0%"></div>
                </div>
            `;
            progressContainer.appendChild(progress);

            const formData = new FormData();
            formData.append("file", file);

            const response = await fetch("/upload", {
                method: "POST",
                body: formData,
            });

            const result = await response.json();
            if (result.url) {
                progress.querySelector(".status").textContent = "Uploaded!";
                progress.querySelector(".progress-bar").style.width = "100%";
            }
        }

        // Refresh file list after all uploads complete
        await fetchAndDisplayFiles();

        // Reset UI
        selectedFiles = [];
        dropZone.querySelector(".drop-zone__prompt").textContent =
            "Drop files here or click to upload (Multiple files allowed)";
    } catch (error) {
        alert(`Upload failed: ${error.message}`);
    }
});

// Function to fetch and display files
async function fetchAndDisplayFiles() {
    try {
        const response = await fetch("/list-files");
        const files = await response.json();
        const container = document.getElementById("file-list-container");
        container.innerHTML = "";

        if (files.length === 0) {
            container.innerHTML =
                '<div class="list-group-item text-muted">No files available</div>';
            return;
        }

        files.forEach((file) => {
            const fileItem = document.createElement("div");
            fileItem.className = "list-group-item file-item";
            fileItem.innerHTML = `
                <span class="file-name">${file.key}</span>
                <div>
                    <a href="${file.url}" class="btn btn-sm btn-success download-btn me-2" download>
                        <span class="material-icons">
                            download
                        </span>
                    </a>
                    <button class="btn btn-sm btn-primary copy-btn" data-url="${file.url}">
                        <span class="material-icons">
                            content_copy
                        </span>
                    </button>
                </div>
            `;
            container.appendChild(fileItem);
        });
        document.querySelectorAll(".copy-btn").forEach((btn) => {
            btn.addEventListener("click", copyToClipboard);
        });
    } catch (error) {
        console.error("Error fetching files:", error);
    }
}

function copyToClipboard(e) {
    let clickedOnIcon = false;
    if (e.target.tagName === "SPAN") {
        clickedOnIcon = true;
        target = e.target.parentElement; // Get the button element
    } else {
        target = e.target; // Get the button element
    }

    let url = target.getAttribute("data-url");
    console.log(url);

    navigator.clipboard
        .writeText(url)
        .then(() => {
            // Visual feedback
            const originalText = target.innerHTML;
            target.innerHTML = `<span class="material-icons">
                done_outline
            </span>`;
            target.classList.add("btn-success");
            target.classList.remove("btn-primary");

            setTimeout(() => {
                target.innerHTML = originalText;
                target.classList.remove("btn-success");
                target.classList.add("btn-primary");
            }, 2000);
        })
        .catch((err) => {
            console.error("Failed to copy: ", err);
            alert("Failed to copy link. Please try again.");
        });
}
// Call when page loads
document.addEventListener("DOMContentLoaded", fetchAndDisplayFiles);

// Refresh after upload
// Add this inside your upload success handler (after line 74 in previous script)
fetchAndDisplayFiles();
