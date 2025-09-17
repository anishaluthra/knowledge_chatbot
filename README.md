# 🧠 Local Knowledge Chatbot

A privacy-first AI chatbot that stores conversations locally and uses semantic search with RAG (Retrieval-Augmented Generation) to answer questions based on previously stored knowledge.

## ✨ Features

- **🔒 Complete Privacy**: All data stored locally, no external API calls
- **🧠 Semantic Search**: Uses ChromaDB for intelligent knowledge retrieval
- **🤖 Local AI**: Powered by Ollama (runs entirely on your machine)
- **💬 RAG Pipeline**: Combines retrieval with AI generation for accurate responses
- **📱 Clean Interface**: Modern web UI for easy interaction
- **⚡ Fast Setup**: Get running in minutes

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- [Ollama](https://ollama.ai) installed

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/knowledge-chatbot.git
   cd knowledge-chatbot
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install and set up Ollama**
   ```bash
   # Install Ollama from https://ollama.ai
   # Then pull a model:
   ollama pull llama3.1
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

6. **Open the frontend**
   - Open `frontend.html` in your browser
   - Or use VS Code Live Server extension

## 💡 How It Works

### Store Knowledge
Add conversations, notes, or any information you want to remember:
```
"I learned that FastAPI is a modern Python web framework that's faster than Flask and includes automatic API documentation with Swagger UI."
```

### Query Knowledge
Ask questions about previously stored information:
```
"What did you learn about FastAPI?"
```

The system uses semantic search to find relevant information and generates contextual responses using your local AI model.

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Frontend HTML  │───▶│   FastAPI API    │───▶│   ChromaDB      │
│  (User Interface)│    │  (Backend Logic) │    │ (Vector Store)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Ollama (LLM)   │
                       │ (Knowledge Ext.)│
                       └─────────────────┘
```

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/chat` | POST | Store new knowledge from conversation |
| `/query` | POST | Query knowledge base with RAG |
| `/search` | GET | Direct semantic search |
| `/stats` | GET | Get database statistics |

## 🛠️ Configuration

### Changing the AI Model
Edit `main.py` and change the model name:
```python
self.model_name = "llama3.1"  # Change to your preferred model
```

Available models: `llama3.1`, `codellama`, `mistral`, `gemma`, etc.

### Database Location
ChromaDB data is stored in `./knowledge_db/` by default. Change in `main.py`:
```python
chroma_client = chromadb.PersistentClient(path="./your_custom_path")
```

## 🔧 Development

### Running Tests
```bash
# Test the API directly
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Test message", "user_id": "test"}'
```

### Adding Features
- **Speech Input**: Integrate Whisper for voice-to-text
- **Export Data**: Add endpoints to export knowledge in various formats
- **User Management**: Add authentication and user separation
- **Advanced RAG**: Implement re-ranking and hybrid search

## 🐛 Troubleshooting

### "Command not found: ollama"
```bash
# Install Ollama from https://ollama.ai
# Or via Homebrew on macOS:
brew install ollama
```

### CORS Errors in Frontend
- Make sure the backend is running on port 8000
- Check browser console for detailed error messages

### ChromaDB/NumPy Compatibility Issues
```bash
pip uninstall numpy chromadb -y
pip install --upgrade chromadb
```

### "Connection refused" Errors
- Ensure the backend is running: `python main.py`
- Check if port 8000 is available
- Try `http://127.0.0.1:8000` instead of `localhost:8000`

## 📝 License

MIT License - feel free to use this project however you'd like!

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## ⭐ Star This Project

If you find this useful, please give it a star on GitHub!

---

Built with ❤️ for privacy-conscious knowledge management