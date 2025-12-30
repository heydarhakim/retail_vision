const API_URL = "http://localhost:8000/api/v1";

document.addEventListener("DOMContentLoaded", async () => {
    // Load Stores
    try {
        const res = await fetch(`${API_URL}/stores`);
        const stores = await res.json();
        const select = document.getElementById("storeSelect");
        select.innerHTML = stores.map(s => `<option value="${s.id}">${s.name} (${s.location})</option>`).join("");
    } catch (e) {
        console.error("Failed to load stores", e);
    }
});

async function runAudit() {
    const storeId = document.getElementById("storeSelect").value;
    const fileInput = document.getElementById("imageInput");
    const statusDiv = document.getElementById("status");

    if (!fileInput.files[0]) return alert("Please select an image");

    // UI Reset
    statusDiv.innerText = "Uploading & Processing...";
    statusDiv.className = "text-xs bg-yellow-500 px-2 py-1 rounded text-white";
    document.getElementById("overlays").innerHTML = '';

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    try {
        const res = await fetch(`${API_URL}/audit/${storeId}`, {
            method: "POST",
            body: formData
        });

        if (!res.ok) throw new Error("Audit failed");

        const data = await res.json();
        renderResults(data);
        statusDiv.innerText = "Complete";
        statusDiv.className = "text-xs bg-green-500 px-2 py-1 rounded text-white";

    } catch (e) {
        console.error(e);
        statusDiv.innerText = "Error";
        statusDiv.className = "text-xs bg-red-500 px-2 py-1 rounded text-white";
    }
}

function renderResults(data) {
    // 1. Show Image
    const img = document.getElementById("displayImage");
    const container = document.getElementById("canvasContainer");
    document.getElementById("placeholderText").classList.add("hidden");
    
    // Use the backend returned path, adjusting for local docker access
    img.src = `http://localhost:8000${data.image_path}`;
    img.classList.remove("hidden");

    img.onload = () => {
        // 2. Draw BBoxes
        const overlayContainer = document.getElementById("overlays");
        overlayContainer.innerHTML = '';
        
        // Get displayed dimensions
        const displayedWidth = img.clientWidth;
        const displayedHeight = img.clientHeight;
        
        // Calculate offsets to center bounding boxes over the contained image
        const containerWidth = container.clientWidth;
        const containerHeight = container.clientHeight;
        const offsetX = (containerWidth - displayedWidth) / 2;
        const offsetY = (containerHeight - displayedHeight) / 2;

        data.detections.forEach(det => {
            const [x1, y1, x2, y2] = det.bbox; // Normalized 0-1
            
            const box = document.createElement("div");
            box.className = "bbox-overlay";
            
            // Color Logic
            let color = "#22c55e"; // Green
            if (det.confidence < 0.5) color = "#eab308"; // Yellow (Low Conf)
            // Note: Red would typically be used for 'misplaced' logic calculated in JS or backend
            
            box.style.borderColor = color;
            box.style.left = `${(x1 * displayedWidth) + offsetX}px`;
            box.style.top = `${(y1 * displayedHeight) + offsetY}px`;
            box.style.width = `${(x2 - x1) * displayedWidth}px`;
            box.style.height = `${(y2 - y1) * displayedHeight}px`;

            const label = document.createElement("div");
            label.className = "label";
            label.style.backgroundColor = color;
            label.innerText = `${det.class_name} ${(det.confidence*100).toFixed(0)}%`;
            
            box.appendChild(label);
            overlayContainer.appendChild(box);
        });
    };

    // 3. Update Dashboard
    document.getElementById("resultsPanel").classList.remove("hidden");
    document.getElementById("scoreBadge").innerText = `${data.compliance_score}%`;
    
    const missingList = document.getElementById("missingList");
    missingList.innerHTML = data.missing_items.length 
        ? data.missing_items.map(i => `<li>${i}</li>`).join("") 
        : "<li class='text-green-600 list-none'>All items present</li>";

    const misplacedList = document.getElementById("misplacedList");
    misplacedList.innerHTML = data.misplaced_items.length 
        ? data.misplaced_items.map(i => `<li>${i}</li>`).join("") 
        : "<li class='text-green-600 list-none'>Planogram compliant</li>";
}