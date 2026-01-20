document.addEventListener("DOMContentLoaded", () => {
  const micBtn = document.querySelector(".mic-btn");
  const output = document.getElementById("voice-output");
  const statusText = document.getElementById("voice-status");

  micBtn.addEventListener("click", () => {
    statusText.textContent = "Listening...";
    output.textContent = "— Listening… —";

    // Call Python backend
    fetch("/listen", { method: "POST" })
      .then(res => res.json())
      .then(data => {
        if (data.status === "success") {
          output.textContent = data.text;
          statusText.textContent = "Done";
        } else {
          output.textContent = "Error: " + data.text;
          statusText.textContent = "Error";
        }
      })
      .catch(err => {
        output.textContent = "Error calling backend";
        statusText.textContent = "Error";
      });
  });
});

function setActive(element) {
    // Remove 'active' from all buttons
    document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
    
    // Add 'active' to the clicked button
    element.classList.add('active');
}

