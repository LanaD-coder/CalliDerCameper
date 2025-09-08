from django.core.mail.backends.smtp import EmailBackend
import ssl
import certifi

class IonosSSLBackend(EmailBackend):
    def open(self):
        if self.connection:
            return False
        # use certifi CA bundle
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        return super().open()
