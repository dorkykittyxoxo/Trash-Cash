document.addEventListener("DOMContentLoaded", function () {
    const uploadInput = document.createElement("input");
    uploadInput.type = "file";
    uploadInput.accept = "image/*";
    uploadInput.style.display = "none";

    const scanCard = document.querySelector(".cards .card:first-child"); 
    scanCard.style.cursor = "pointer";

    scanCard.addEventListener("click", function () {
        uploadInput.click();
    });

    uploadInput.addEventListener("change", function () {
        if (uploadInput.files.length > 0) {
            const file = uploadInput.files[0];
            classifyWaste(file);
        }
    });

    function classifyWaste(file) {
        const formData = new FormData();
        formData.append("image", file);

        fetch("http://127.0.0.1:5000/classify", {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            showResultModal(data);
        })
        .catch(error => {
            console.error("Error:", error);
            alert("Failed to classify waste. Please try again.");
        });
    }

    function showResultModal(data) {
        const modalContent = `
            <h2>Waste Classification Result</h2>
            <p><strong>Type:</strong> ${data.waste_type}</p>
            <p><strong>Points Earned:</strong> ${data.points}</p>
            <p><strong>Recycling Info:</strong> ${data.recycling_info}</p>
            <button onclick="closeModal()">Close</button>
        `;

        const modal = document.createElement("div");
        modal.classList.add("modal");
        modal.innerHTML = modalContent;
        document.body.appendChild(modal);

        modal.style.display = "block";
        document.getElementById("modalOverlay").style.display = "block";

        document.getElementById("modalOverlay").addEventListener("click", () => {
            closeModal();
        });

        function closeModal() {
            modal.style.display = "none";
            document.getElementById("modalOverlay").style.display = "none";
            document.body.removeChild(modal);
        }
    }

    document.body.appendChild(uploadInput);
});
