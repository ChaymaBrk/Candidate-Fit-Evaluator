# 🤖 AI Candidate Fit Evaluator

## 📑 Table of Contents

- [Features](#-features)
- [Architecture](#️-architecture)
- [Quick Start](#-quick-start)
- [API Usage](#-api-usage)
- [Web UI](#-web-ui)
- [CLI Usage](#-cli-usage)
- [Configuration](#-configuration)
- [Evaluation Process](#-evaluation-process)
- [Development](#-development)
- [Health Check](#-health-check)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)
- [Contributing](#-contributing)
- [Support](#-support)

An intelligent FastAPI-based AI assistant that evaluates how well a candidate's resume matches a job description using LLMs and vector search.

## 🎯 Features

- **Document Parsing**: Supports PDF, DOCX, and TXT files
- **Intelligent Analysis**: Uses Groq Llama for semantic understanding
- **Vector Search**: FAISS-based similarity matching
- **Structured Results**: Detailed fit evaluation with explanations
- **Modular Architecture**: Clean, maintainable code structure
- **CLI Tool**: Command-line interface for testing
- **REST API**: FastAPI endpoints for integration

## 🏗️ Architecture

```
src/
├── models/
│   └── response_models.py      # Pydantic response models
├── services/
│   ├── candidate_evaluator.py  # Main orchestrator
│   ├── document_parser.py      # PDF/DOCX parsing
│   ├── text_chunker.py         # Semantic text chunking
│   ├── vector_store.py         # FAISS vector operations
│   └── llm_service.py          # Groq Llama integration
├── app.py                      # FastAPI application (serves API and web UI)
├── cli.py                      # Command-line interface
├── index.html                  # Web UI (served at /ui endpoint)
└── requirements.txt            # Dependencies
```

- **index.html**: Modern web UI for uploading resumes and job descriptions, visualizing results. Served at the `/ui` endpoint by FastAPI (`app.py`).
- **app.py**: FastAPI backend serving both REST API endpoints (e.g., `/evaluate-fit`) and the static web UI (`/ui`).
- **src/services/**: Core business logic for parsing, chunking, vector search, and LLM evaluation.
- **src/models/**: Pydantic models for structured API responses.
- **cli.py**: Command-line interface for local or scripted evaluation.

The web UI (`index.html`) interacts with the backend exclusively via the `/evaluate-fit` API endpoint, providing a seamless browser-based experience for users.

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd ai-candidate-fit-evaluator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup

Create a `.env` file in the root directory:


# Primary: Groq API key 
GROQ_API_KEY=your_groq_api_key_here


**Note**: The system works without API keys using fallback methods, but Groq provides the best results with the Llama model.

### 3. Running the API Server

```bash
# Start the FastAPI server
python app.py

# Or using uvicorn directly
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

### 4. API Documentation



## 📡 API Usage

### Main Endpoint: `/evaluate-fit`

**Method**: `POST`

**Parameters**:
- `resume_file`: PDF or DOCX file (required)
- `job_description_file`: PDF, DOCX, or TXT file (required)
- `candidate_name`: String (optional, metadata only)

**Example using curl**:

```bash
curl -X POST "http://localhost:8000/evaluate-fit" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "resume_file=@path/to/resume.pdf" \
  -F "job_description_file=@path/to/job_description.pdf" \
  -F "candidate_name=John Doe"
```

**Example using Python**:

```python
import requests

url = "http://localhost:8000/evaluate-fit"
files = {
    'resume_file': open('resume.pdf', 'rb'),
    'job_description_file': open('job_description.pdf', 'rb')
}
data = {'candidate_name': 'John Doe'}

response = requests.post(url, files=files, data=data)
result = response.json()
print(result)
```

### Response Format

```json
{
  "fit_score": "Strong Fit",
  "fit_percentage": 85.5,
  "candidate_profile": {
    "education": ["Master's in Computer Science"],
    "skills": ["Python", "FastAPI", "Machine Learning"],
    "experience": ["2 years at AI startup"],
    "certifications": [],
    "languages": []
  },
  "comparison_matrix": [
    { "requirement": "Python", "match": true },
    { "requirement": "3+ years experience", "match": false },
    { "requirement": "FastAPI", "match": true }
  ],
  "explanation": "The candidate matches most technical requirements but has limited years of experience.",
  "strengths": ["Strong technical skills", "Relevant experience"],
  "weaknesses": ["Limited years of experience"],
  "recommendations": ["Consider additional experience in leadership"],
  "processing_time": 2.34
}
```

## 🖥️ Web UI

The project includes a modern, user-friendly web interface for evaluating candidate fit, accessible via your browser.

### Accessing the Web UI

- **Endpoint:** [`/ui`](http://localhost:8000/ui)
- **File:** [`index.html`](index.html)

After starting the FastAPI server, open your browser and navigate to [http://localhost:8000/ui](http://localhost:8000/ui) to use the web interface.

### Features
- Upload a candidate's resume (PDF or DOCX) and a job description (PDF, DOCX, or TXT)
- Optionally enter the candidate's name
- Click "Evaluate Candidate Fit" to analyze the match
- View a detailed fit score, strengths, weaknesses, explanation, and a requirements comparison matrix
- All processing is done via the `/evaluate-fit` API endpoint

### How it Works
- The UI is served directly from the [`index.html`](index.html) file via the `/ui` endpoint in [`app.py`](app.py)
- The form submits files and data to the `/evaluate-fit` endpoint using JavaScript (fetch API)
- Results are displayed in a visually appealing, responsive layout

### Example
1. Go to [http://localhost:8000/ui](http://localhost:8000/ui)
2. Fill in the candidate name (optional)
3. Upload the resume and job description files
4. Click "Evaluate Candidate Fit"
5. View the results instantly in your browser

---

## 🖥️ CLI Usage

The CLI tool provides a convenient way to test the evaluator:

```bash
# Basic usage
python cli.py resume.pdf job_description.pdf

# With candidate name
python cli.py resume.pdf job_description.pdf --candidate-name "John Doe"

# Save results to JSON file
python cli.py resume.pdf job_description.pdf --output results.json

# JSON-only output
python cli.py resume.pdf job_description.pdf --json-only
```

## 🔧 Configuration

### Vector Store Settings

The system uses FAISS with the following default settings:
- **Embedding Model**: `all-MiniLM-L6-v2` (Sentence Transformers)
- **Index Type**: IndexFlatIP (Inner Product for cosine similarity)
- **Dimension**: 384 (Sentence Transformers output dimension)
- **Chunk Size**: 500 characters
- **Overlap**: 50 characters

### LLM Settings

- **Primary**: Groq meta-llama/llama-4-scout-17b-16e-instruct (if API key provided)
- **Fallback**: OpenAI GPT-3.5-turbo (if API key provided)
- **Secondary Fallback**: Keyword-based matching and similarity scoring

## 📊 Evaluation Process

1. **Document Parsing**: Extract text from PDF/DOCX files
2. **Text Chunking**: Split documents into semantic, CV-aware chunks
3. **Vector Embedding**: Generate embeddings using Sentence Transformers
4. **Requirement Extraction**: Extract job requirements using Groq Llama (JSON mode)
5. **Profile Extraction**: Extract candidate information from resume
6. **Similarity Matching**: Find relevant resume chunks for each requirement
7. **Requirement Evaluation**: Evaluate each requirement match using LLM
8. **Overall Assessment**: Generate comprehensive fit evaluation

## 🛠️ Development

### Project Structure

```
├── app.py                 # FastAPI application
├── cli.py                 # Command-line interface
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── src/                  # Source code
│   ├── __init__.py
│   ├── models/           # Data models
│   │   ├── __init__.py
│   │   └── response_models.py
│   └── services/         # Business logic
│       ├── __init__.py
│       ├── candidate_evaluator.py
│       ├── document_parser.py
│       ├── text_chunker.py
│       ├── vector_store.py
│       └── llm_service.py
└── tests/                # Test files (to be added)
```

### Adding New Features

1. **New Document Types**: Extend `DocumentParser` class
2. **New LLM Providers**: Extend `LLMService` class
3. **New Vector Stores**: Extend `VectorStore` class
4. **New Response Fields**: Update `response_models.py`

### Testing

```bash
# Run the API server
python app.py

# Test with CLI
python cli.py sample_resume.pdf sample_job.pdf

# Test API endpoint
curl -X POST "http://localhost:8000/evaluate-fit" \
  -F "resume_file=@sample_resume.pdf" \
  -F "job_description_file=@sample_job.pdf"
```

## 🔍 Health Check

```bash
# Check API health
curl http://localhost:8000/health

# Response: {"status": "healthy", "service": "AI Candidate Fit Evaluator"}
```

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're in the correct directory and virtual environment is activated
2. **File Not Found**: Check file paths and permissions
3. **Memory Issues**: Reduce chunk size in `TextChunker` for large documents
4. **API Timeouts**: Increase timeout settings for large documents

### Performance Tips

- Use smaller chunk sizes for faster processing
- Enable GPU acceleration for Sentence Transformers if available
- Consider using a more powerful LLM for better accuracy

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation at `/docs`
3. Open an issue on GitHub

---

**Built with ❤️ using FastAPI, FAISS, and Groq (Llama)** 