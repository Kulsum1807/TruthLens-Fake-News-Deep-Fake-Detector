document.addEventListener("DOMContentLoaded", function () {
  window.showTab = function (tab) {
    document.querySelectorAll(".tab-content").forEach((el) => {
      el.classList.add("hidden");
    });
    document.getElementById(tab + "-tab").classList.remove("hidden");
  };

  // ===========================
  // TEXT DETECTION
  // ===========================
  const textForm = document.getElementById("text-form");

  textForm.addEventListener("submit", function (e) {
    e.preventDefault();

    const input = document.getElementById("user_input").value;
    const resultDiv = document.getElementById("text-result");

    resultDiv.innerHTML = "🔎 Analyzing...";

    fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ user_input: input }),
    })
      .then((res) => res.json())
      .then((data) => {
        let linksHtml = "";

        if (data.links && data.links.length > 0) {
          linksHtml = "<br><strong>Sources:</strong><ul>";
          data.links.forEach((link) => {
            linksHtml += `<li><a href="${link[1]}" target="_blank">${link[0]}</a></li>`;
          });
          linksHtml += "</ul>";
        } else {
          linksHtml = "<br><em>Sources unavailable.</em>";
        }

        resultDiv.innerHTML = `
                <strong>Prediction:</strong> ${data.prediction}
                <div class="accuracy-bar-wrapper">
                    <div class="accuracy-bar" style="width:${data.accuracy}%">
                        ${data.accuracy}%
                    </div>
                </div>
                ${linksHtml}
            `;
      })
      .catch((err) => {
        resultDiv.innerHTML = "Error: " + err;
      });
  });

  // ===========================
  // IMAGE DETECTION
  // ===========================
  const imageForm = document.getElementById("image-form");

  imageForm.addEventListener("submit", function (e) {
    e.preventDefault();

    const fileInput = document.getElementById("image_file");
    const resultDiv = document.getElementById("image-result");

    resultDiv.innerHTML = "🖼️ Analyzing image...";

    const formData = new FormData();
    formData.append("image_file", fileInput.files[0]);

    fetch("/predict_image", {
      method: "POST",
      body: formData,
    })
      .then((res) => res.json())
      .then((data) => {
        resultDiv.innerHTML = `
                <strong>Prediction:</strong> ${data.prediction}
                <div class="accuracy-bar-wrapper">
                    <div class="accuracy-bar" style="width:${data.accuracy}%">
                        ${data.accuracy}%
                    </div>
                </div>
            `;
      })
      .catch((err) => {
        resultDiv.innerHTML = "Error: " + err;
      });
  });

  // ===========================
  // VIDEO DETECTION
  // ===========================
  const videoForm = document.getElementById("video-form");

  videoForm.addEventListener("submit", function (e) {
    e.preventDefault(); // prevents page refresh

    const fileInput = document.getElementById("video_file");
    const resultDiv = document.getElementById("video-result");

    resultDiv.innerHTML = "🎥 Analyzing video...";

    const formData = new FormData();
    formData.append("video_file", fileInput.files[0]);

    fetch("/predict_video", {
      method: "POST",
      body: formData,
    })
      .then((res) => res.json())
      .then((data) => {
        resultDiv.innerHTML = `
                <strong>Prediction:</strong> ${data.prediction}
                <div class="accuracy-bar-wrapper">
                    <div class="accuracy-bar" style="width:${data.accuracy}%">
                        ${data.accuracy}%
                    </div>
                </div>
            `;
      })
      .catch((err) => {
        resultDiv.innerHTML = "Error: " + err;
      });
  });
});
