function uploadFile(endpoint) {
    let formData = new FormData(document.getElementById("pdfForm"));

    fetch(endpoint, {
        method: "POST",
        body: formData
    })
    .then(response => {
        if (response.ok) return response.blob();
        throw new Error("Operation failed");
    })
    .then(blob => {
        let link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = "processed.pdf";  
        link.click();
        document.getElementById("status").innerText = "✅ File processed successfully!";
    })
    .catch(error => {
        document.getElementById("status").innerText = "❌ Error: " + error.message;
    });
}