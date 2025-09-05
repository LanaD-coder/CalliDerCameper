from django.forms.widgets import ClearableFileInput
from django.utils.safestring import mark_safe

class SignaturePadWidget(ClearableFileInput):
    template_name = 'widgets/signature_pad.html'

    class Media:
        js = [
            'http://cdn.jsdelivr.net/npm/signature_pad@4.0.0/dist/signature_pad.umd.min.js',
            '/static/js/signature_widget.js',
        ]
        css = {
            'all': ['/static/css/signature_widget.css'],  # optional styles
        }

    def render(self, name, value, attrs=None, renderer=None):
        # Render the default file input plus the canvas
        output = super().render(name, value, attrs, renderer)
        canvas_html = '<canvas id="signature-pad" width="400" height="150" style="border:1px solid #000;"></canvas>'
        clear_button = '<button type="button" id="clear-signature">Clear</button>'
        return mark_safe(f"{canvas_html}{clear_button}<br>{output}")
