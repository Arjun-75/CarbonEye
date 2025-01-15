document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("upload-form");
    const processButton = document.getElementById("process-btn");
    const loadingIndicator = document.getElementById("loading-indicator");
    const resultContainer = document.getElementById("result-container");

    // Function to handle video upload and processing
    async function handleVideoUpload(event) {
        event.preventDefault();

        const formData = new FormData(form);
        const video = document.querySelector("#video").files[0];
        const distance = document.querySelector("#distance").value;

        // Validate inputs
        if (!video || isNaN(distance) || Number(distance) <= 0) {
            alert("Please ensure all fields are correctly filled.");
            return;
        }

        // Show loading indicator and disable the button
        loadingIndicator.style.display = "block";
        processButton.disabled = true;

        try {
            const response = await fetch("/process", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`Error: ${response.statusText}`);
            }

            const data = await response.json();

            // Display results
            resultContainer.innerHTML = `
                <h3>Processing Results</h3>
                <p><strong>Total Distance:</strong> ${data.distance} km</p>
                <p><strong>Number of Vehicles Detected:</strong> ${data.number_of_vehicles_detected}</p>
                <p><strong>CO₂ Emissions:</strong> ${data.co2_emissions.toFixed(2)} kg</p>
                <a href="${data.processed_video}" download class="download-link">Download Processed Video</a>
            `;
        } catch (error) {
            alert(`An error occurred: ${error.message}`);
        } finally {
            // Hide loading indicator and enable the button
            loadingIndicator.style.display = "none";
            processButton.disabled = false;
        }
    }

    // Attach the enhanced function to the form's submit event
    form.addEventListener("submit", handleVideoUpload);
});
