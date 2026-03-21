# Multilingual RAG Voice Assistant

## Overview
This project is a multilingual voice assistant built using a simple Retrieval-Augmented Generation (RAG) approach. It accepts voice input, retrieves relevant product information from a JSON file, and responds with voice output in the same language.

## Features
- Speech-to-Text using Faster Whisper
- Multilingual translation support
- Semantic retrieval using sentence-transformers
- JSON-based product database
- Response generation using Groq LLM
- Text-to-Speech using Edge TTS
- Works on both Windows and Linux

## Project Structure
```
llm.py           # LLM response generation
main.py          # Main pipeline
products.json    # Product data
retriever.py     # Retrieval logic
stt.py           # Speech-to-text
translator.py    # Translation functions
tts.py           # Text-to-speech
requirements.txt # Python dependencies
.env             # API key (not included in repo)
```

## Setup (Windows)

### 1. Create virtual environment
```
python -m venv venv
venv\Scripts\activate
```

### 2. Install dependencies
```
pip install -r requirements.txt
```

### 3. Add environment variable
Create a `.env` file:
```
GROQ_API_KEY=your_api_key_here
```

### 4. Run the project
```
python main.py
```

## Setup (Linux)

### 1. Install system dependencies
```
sudo apt update
sudo apt install -y portaudio19-dev python3-pyaudio python3-pygame alsa-utils pulseaudio
```

### 2. Create virtual environment
```
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python dependencies
```
pip install -r requirements.txt
```

### 4. Add environment variable
Create a `.env` file:
```
GROQ_API_KEY=your_api_key_here
```

### 5. Run the project
```
python3 main.py
```

## How It Works
1. User speaks a query
2. Speech is converted to text using Whisper
3. Text is translated to English (if needed)
4. Relevant products are retrieved from JSON using embeddings
5. LLM generates a response based on retrieved context
6. Response is translated back to original language
7. Text-to-Speech outputs the answer

## Notes
- Requires internet for translation, LLM, and TTS
- Works with a small dataset (products.json)
- Linux requires audio dependencies for microphone and speaker

## License
This project is for educational purposes.