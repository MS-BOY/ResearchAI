from deep_translator import GoogleTranslator


# ==========================================
# Translate Text
# ==========================================

def translate_text(
    text,
    target_language="bn"
):

    if not text:
        return ""


    try:

        translator = GoogleTranslator(

            source="auto",

            target=target_language

        )


        # Google Translator-এর জন্য
        # text ছোট অংশে ভাগ করা হচ্ছে

        chunks = []


        max_length = 3000


        for i in range(
            0,
            len(text),
            max_length
        ):

            chunk = text[
                i:i + max_length
            ]

            chunks.append(
                chunk
            )


        translated_chunks = []


        for chunk in chunks:

            try:

                translated = translator.translate(
                    chunk
                )


                if translated:

                    translated_chunks.append(
                        translated
                    )


            except Exception as e:

                print(
                    "⚠️ Chunk translation failed:",
                    e
                )


                # Translation fail করলে
                # original text রাখা হবে

                translated_chunks.append(
                    chunk
                )


        return "\n\n".join(
            translated_chunks
        )


    except Exception as e:

        print(
            "❌ Translation failed:",
            e
        )

        return text


# ==========================================
# Bangla
# ==========================================

def translate_to_bangla(text):

    return translate_text(
        text,
        "bn"
    )


# ==========================================
# English
# ==========================================

def translate_to_english(text):

    return translate_text(
        text,
        "en"
    )