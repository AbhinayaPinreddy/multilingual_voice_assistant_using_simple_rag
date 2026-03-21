from stt import listen
from tts import speak
from translator import to_english, from_english
from retriever import retrieve
from llm import generate


def build_context(results):
    if not results:
        return "No products found."

    text = ""
    for p in results:
        text += f"""
        Name: {p['name']}
        Price: ₹{p['price']}
        Description: {p['description']}
        """
    return text


def run():
    print("Voice Agent Started...")

    while True:
        # 1. Listen
        user_text, lang = listen()
        print("User:", user_text, "| Lang:", lang)

        if not user_text:
            continue

        # 2. Translate
        query_en = to_english(user_text, lang)

        # 3. Retrieve
        results = retrieve(query_en)

        # 4. Build context
        context = build_context(results)

        # 5. LLM
        answer_en = generate(context, query_en)

        # 6. Translate back
        final_answer = from_english(answer_en, lang)

        print("Bot:", final_answer)

        # 7. Speak
        speak(final_answer, lang)


if __name__ == "__main__":
    run()
