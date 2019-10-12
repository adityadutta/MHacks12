from google.cloud import translate
import iso639 as iso

def createTranslation(text, language):
    translate_client = translate.Client()
    language = iso.to_iso639_1(language)

    try:
        translation = translate_client.translate(
            text,
            target_language=language
        )
    except: 
        return 'Unfortunately, that language is not supported.'
    return translation['translatedText']