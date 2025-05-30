# Extraction Configuration

Kreuzberg provides extensive configuration options for the extraction process through the `ExtractionConfig` class. This guide covers common configuration scenarios and examples.

## Basic Configuration

All extraction functions accept an optional `config` parameter of type `ExtractionConfig`. This object allows you to:

- Control OCR behavior with `force_ocr` and `ocr_backend`
- Provide engine-specific OCR configuration via `ocr_config`
- Add validation and post-processing hooks
- Configure custom extractors

## Examples

### Basic Usage

```python
from kreuzberg import extract_file, ExtractionConfig

# Simple extraction with default configuration
result = await extract_file("document.pdf")

# Extraction with custom configuration
result = await extract_file("document.pdf", config=ExtractionConfig(force_ocr=True))
```

### OCR Configuration

```python
from kreuzberg import extract_file, ExtractionConfig, TesseractConfig, PSMMode

# Configure Tesseract OCR with specific language and page segmentation mode
result = await extract_file(
    "document.pdf",
    config=ExtractionConfig(force_ocr=True, ocr_config=TesseractConfig(language="eng+deu", psm=PSMMode.SINGLE_BLOCK)),
)
```

The `language` parameter specifies which language model Tesseract should use. You can specify multiple languages by joining them with a plus sign (e.g., "eng+deu" for English and German).

The `psm` (Page Segmentation Mode) parameter controls how Tesseract analyzes page layout. Different modes are suitable for different types of documents:

- `PSMMode.AUTO`: Automatic page segmentation (default)
- `PSMMode.SINGLE_BLOCK`: Treat the image as a single text block
- `PSMMode.SINGLE_LINE`: Treat the image as a single text line
- `PSMMode.SINGLE_WORD`: Treat the image as a single word
- `PSMMode.SINGLE_CHAR`: Treat the image as a single character

### Alternative OCR Engines

```python
from kreuzberg import extract_file, ExtractionConfig, EasyOCRConfig, PaddleOCRConfig

# Use EasyOCR backend
result = await extract_file(
    "document.jpg", config=ExtractionConfig(ocr_backend="easyocr", ocr_config=EasyOCRConfig(language_list=["en", "de"]))
)

# Use PaddleOCR backend
result = await extract_file(
    "chinese_document.jpg", config=ExtractionConfig(ocr_backend="paddleocr", ocr_config=PaddleOCRConfig(language="ch"))
)
```

### Batch Processing

```python
from kreuzberg import batch_extract_file, ExtractionConfig

# Process multiple files with the same configuration
file_paths = ["document1.pdf", "document2.docx", "image.jpg"]
config = ExtractionConfig(force_ocr=True)
results = await batch_extract_file(file_paths, config=config)
```

### Synchronous API

```python
from kreuzberg import extract_file_sync, ExtractionConfig, TesseractConfig

# Synchronous extraction with configuration
result = extract_file_sync("document.pdf", config=ExtractionConfig(ocr_config=TesseractConfig(language="eng")))
```

## Using Custom Extractors

You can register custom extractors to handle specific file formats:

```python
from kreuzberg import ExtractorRegistry, extract_file, ExtractionConfig
from my_module import CustomExtractor

# Register a custom extractor
ExtractorRegistry.add_extractor(CustomExtractor)

# Now extraction functions will use your custom extractor for supported MIME types
result = await extract_file("custom_document.xyz")

# Later, remove the extractor if needed
ExtractorRegistry.remove_extractor(CustomExtractor)
```

See the [Custom Extractors](../advanced/custom-extractors.md) guide for more details on creating and registering custom extractors.

## OCR Best Practices

When configuring OCR for your documents, consider these best practices:

1. **Language Selection**: Choose the appropriate language model for your documents. Using the wrong language model can significantly reduce OCR accuracy.

1. **Page Segmentation Mode**: Select the appropriate PSM based on your document layout:

    - Use `PSMMode.AUTO` for general documents with mixed content
    - Use `PSMMode.SINGLE_BLOCK` for documents with a single column of text
    - Use `PSMMode.SINGLE_LINE` for receipts or single-line text
    - Use `PSMMode.SINGLE_WORD` or `PSMMode.SINGLE_CHAR` for specialized cases

1. **OCR Engine Selection**: Choose the appropriate OCR engine based on your needs:

    - Tesseract: Good general-purpose OCR with support for many languages
    - EasyOCR: Better for some non-Latin scripts and natural scene text
    - PaddleOCR: Excellent for Chinese and other Asian languages

1. **Preprocessing**: For better OCR results, consider using validation and post-processing hooks to clean up the extracted text.
