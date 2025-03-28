class ResponseHandling:
    def __init__(self, text: str):
        self.text = text
        pass

    @classmethod
    def handle_response(text: str) -> str:
        text = text.lower()
        if 'hello' in text or 'hi' in text:
            return "Hello! I am a bot to help you with your trading. How can I help you today?"
        
        if 'how are you' in text:
            return "I am a bot. I don't have feelings, but thanks for asking!"
        
        return "I'm sorry, I don't understand."



if __name__ == "__main__":
    ...