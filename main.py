import gettext
import os
import locale

# Detect system language or default to English
lang = locale.getdefaultlocale()[0]
if lang and lang.startswith('de'):
    lang = 'de'
else:
    lang = 'en'

localedir = os.path.join(os.path.dirname(__file__), 'locales')
translation = gettext.translation('messages', localedir=localedir, languages=[lang], fallback=True)
translation.install()

print(_("Welcome to Calli the Camper!"))
print(_("Please select your language."))
