document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("canvas[id^='signature-canvas']").forEach(function (canvas) {
        const hiddenInputId = canvas.dataset.input;
        const existingImage = canvas.dataset.img;

        const signaturePad = new SignaturePad(canvas);
        const hiddenInput = document.getElementById(hiddenInputId);

        if (existingImage) {
            const img = new Image();
            img.onload = function () {
                canvas.getContext("2d").drawImage(img, 0, 0, canvas.width, canvas.height);
            };
            img.src = existingImage;
        }

        const form = canvas.closest("form");
        if (form) {
            form.addEventListener("submit", function () {
                if (!signaturePad.isEmpty()) {
                    hiddenInput.value = signaturePad.toDataURL();
                }
            });
        }

        const clearBtn = canvas.parentNode.querySelector(".clear-signature");
        if (clearBtn) {
            clearBtn.addEventListener("click", function () {
                signaturePad.clear();
                hiddenInput.value = "";
            });
        }
    });
});
