document.addEventListener('DOMContentLoaded', function () {
    const canvas = document.getElementById('signature-pad');
    if (!canvas) return;

    const signaturePad = new SignaturePad(canvas);
    const clearButton = document.getElementById('clear-signature');
    const hiddenInput = document.getElementById('id_signature_data');

    // Update hidden input on signature end
    signaturePad.onEnd = function () {
        hiddenInput.value = signaturePad.toDataURL();
    };

    clearButton.addEventListener('click', function () {
        signaturePad.clear();
        hiddenInput.value = '';
    });
});