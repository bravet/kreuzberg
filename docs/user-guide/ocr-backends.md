# OCR Backends

Kreuzberg supports multiple OCR (Optical Character Recognition) backends, giving you flexibility to choose the best option for your specific needs. Each backend has different strengths, language support, and installation requirements.

## Supported Backends

### 1. Tesseract OCR

[Tesseract OCR](https://github.com/tesseract-ocr/tesseract) is the default OCR backend in Kreuzberg. It's a mature, open-source OCR engine with support for over 100 languages.

**Installation Requirements:**

- Requires system-level installation
- Minimum required version: Tesseract 5.0

**Installation Instructions:**

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
choco install -y tesseract
```

**Language Support:**

- For languages other than English, install additional language packs:
    - Ubuntu: `sudo apt-get install tesseract-ocr-deu` (for German)
    - macOS: `brew install tesseract-lang`

**Configuration:**

```python
from kreuzberg import extract_file, ExtractionConfig, TesseractConfig, PSMMode

result = await extract_file(
    "document.pdf",
    config=ExtractionConfig(
        ocr_backend="tesseract",  # This is the default
        ocr_config=TesseractConfig(language="eng+deu", psm=PSMMode.AUTO),  # English and German  # Page segmentation mode
    ),
)
```

### 2. EasyOCR

[EasyOCR](https://github.com/JaidedAI/EasyOCR) is a Python library that uses deep learning models for OCR. It supports over 80 languages and can be more accurate for certain scripts.

**Installation Requirements:**

- Requires the `easyocr` optional dependency
- Install with: `pip install "kreuzberg[easyocr]"`

**GPU Support:**

!!! warning "Experimental Feature"

    GPU support is not considered an official feature and might be subject to change or removal in future versions.

- EasyOCR can use GPU acceleration when PyTorch with CUDA is available
- To enable GPU, set `use_gpu=True` in the configuration
- Kreuzberg will automatically check if CUDA is available via PyTorch

**Language Support:**

- Uses different language codes than Tesseract
- Examples: `en` (English), `de` (German), `zh` (Chinese), etc.
- See the [EasyOCR documentation](https://github.com/JaidedAI/EasyOCR#supported-languages) for the full list

**Configuration:**

```python
from kreuzberg import extract_file, ExtractionConfig, EasyOCRConfig

result = await extract_file(
    "document.jpg",
    config=ExtractionConfig(
        ocr_backend="easyocr",
        ocr_config=EasyOCRConfig(
            language_list=["en", "de"], use_gpu=True  # English and German  # Enable GPU acceleration if available (experimental)
        ),
    ),
)
```

### 3. PaddleOCR

[PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) is an OCR toolkit developed by Baidu. It's particularly strong for Chinese and other Asian languages.

!!! warning "Python Compatibility"

    PaddleOCR is only available on Python 3.12 and below. PaddlePaddle does not support Python 3.13 and above.

**Installation Requirements:**

- Requires the `paddleocr` optional dependency
- Install with: `pip install "kreuzberg[paddleocr]"`

**GPU Support:**

!!! warning "Experimental Feature"

    GPU support is not considered an official feature and might be subject to change or removal in future versions.

- PaddleOCR can utilize GPU acceleration if the paddlepaddle-gpu package is installed
- Kreuzberg automatically detects if paddlepaddle-gpu is available
- To explicitly enable GPU, set `use_gpu=True` in the configuration
- For GPU usage, install: `pip install paddlepaddle-gpu` instead of the standard paddlepaddle package

**Language Support:**

- Limited language support compared to other backends
- Supported languages: `ch` (Chinese), `en` (English), `french`, `german`, `japan`, `korean`

**Configuration:**

```python
from kreuzberg import extract_file, ExtractionConfig, PaddleOCRConfig

result = await extract_file(
    "chinese_document.jpg",
    config=ExtractionConfig(
        ocr_backend="paddleocr",
        ocr_config=PaddleOCRConfig(
            language="ch",  # Chinese
            use_gpu=True,  # Enable GPU acceleration if paddlepaddle-gpu is available (experimental)
            gpu_mem=4000,  # Set GPU memory limit in MB (experimental)
        ),
    ),
)
```

### 4. No OCR

You can also disable OCR completely, which is useful for documents that already contain searchable text.

**Configuration:**

```python
from kreuzberg import extract_file, ExtractionConfig

result = await extract_file("searchable_pdf.pdf", config=ExtractionConfig(ocr_backend=None))
```

## Choosing the Right Backend

Here are some guidelines for choosing the appropriate OCR backend:

### Tesseract OCR (Default)

**Advantages:**

- Lightweight and CPU-optimized
- No model downloads required (faster startup)
- Mature and widely used
- Lower memory usage
- Good for general-purpose OCR across many languages
- Good balance of accuracy and performance

**Considerations:**

- Requires system-level installation
- May have lower accuracy for some languages or complex layouts
- More configuration may be needed for optimal results

### EasyOCR

**Advantages:**

- Good accuracy across multiple languages
- No system dependencies required (pure Python)
- Simple configuration
- Better for complex scripts and languages like Arabic, Thai, or Hindi
- Can be more accurate for handwritten text

**Considerations:**

- Larger memory footprint (requires PyTorch)
- Slower first-run due to model downloads
- Heavier resource usage
- Model files are downloaded on first use, causing initial delay

### PaddleOCR

**Advantages:**

- Excellent accuracy, especially for Asian languages
- No system dependencies required
- Modern deep learning architecture
- Fast processing once models are loaded

**Considerations:**

- Largest memory footprint of the three options (requires PaddlePaddle)
- Slower first-run due to model downloads
- More resource-intensive
- Model files are downloaded on first use, causing initial delay

### No OCR (Setting ocr_backend=None)

**Use when:**

- Processing searchable PDFs or documents with embedded text
- You want to extract embedded text only
- You want to avoid the overhead of OCR processing

**Behavior:**

- For searchable PDFs, embedded text will still be extracted
- For images and non-searchable PDFs, an empty string will be returned for content
- Fastest option as it skips OCR processing entirely

## Installation Summary

To install Kreuzberg with different OCR backends:

```bash
# Basic installation (Tesseract requires separate system installation)
pip install kreuzberg

# With EasyOCR support
pip install "kreuzberg[easyocr]"

# With PaddleOCR support (Python 3.12 and below only)
pip install "kreuzberg[paddleocr]"

# With chunking support
pip install "kreuzberg[chunking]"

# With all optional dependencies (OCR backends and chunking)
pip install "kreuzberg[all]"
```

!!! note "System Dependencies"

    Remember that Pandoc and Tesseract are system dependencies that must be installed separately from the Python package.

    For Tesseract, you must install version 5.0 or higher, and you'll need to install additional language data files for languages other than English.
