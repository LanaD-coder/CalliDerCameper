from modeltranslation.translator import translator, TranslationOptions
from .models import Campervan

class VanTranslationOptions(TranslationOptions):
    fields = ('name', 'description',)

translator.register(Campervan, VanTranslationOptions)
