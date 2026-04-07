import ssl
import certifi
from django.core.mail.backends.smtp import EmailBackend


class CustomEmailBackend(EmailBackend):
    def open(self):
        if self.connection:
            return False

        connection_params = {
            "local_hostname": getattr(self, "local_hostname", None),
            "timeout": self.timeout,
        }

        self.connection = self.connection_class(
            self.host, self.port, **connection_params
        )

        # ✅ BẮT BUỘC
        self.connection.ehlo()

        # 🔥 SSL FIX
        if self.use_tls:
            context = ssl.create_default_context(cafile=certifi.where())
            self.connection.starttls(context=context)
            self.connection.ehlo()

        if self.username and self.password:
            self.connection.login(self.username, self.password)

        return True