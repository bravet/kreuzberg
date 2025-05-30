# Installation

Kreuzberg is composed of a core package and several `optional` dependencies, which users can install at their discretion.

## System Dependencies

### Pandoc

Kreuzberg relies on `pandoc`, which is a **required** system dependency. To install it, follow the instructions below:

#### Ubuntu/Debian

```shell
sudo apt-get install pandoc
```

#### macOS

```shell
brew install pandoc
```

#### Windows

```shell
choco install -y pandoc
```

## Kreuzberg Core Package

The Kreuzberg core package can be installed using pip with:

```shell
pip install kreuzberg
```

## Optional Features

### OCR

OCR is an optional feature for extracting text from images and non-searchable PDFs. Kreuzberg supports multiple OCR backends. To understand the differences between these backends, please read the [OCR Backends documentation](../user-guide/ocr-backends.md).

#### Tesseract OCR

Tesseract OCR is built into Kreuzberg and doesn't require additional Python packages. However, you must install Tesseract 5.0 or higher on your system:

##### Ubuntu/Debian

```shell
sudo apt-get install tesseract-ocr
```

##### macOS

```shell
brew install tesseract
```

##### Windows

```shell
choco install -y tesseract
```

!!! note "Language Support"

    Tesseract includes English language support by default. If you need to process documents in other languages, you must install the appropriate language data files:

    - **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr-deu` (for German)
    - **macOS**: `brew install tesseract-lang`
    - **Windows**: See the [Tesseract documentation](https://tesseract-ocr.github.io/tessdoc/Installation.html#windows)

    For more details on language installation and configuration, refer to the [Tesseract documentation](https://tesseract-ocr.github.io/tessdoc/Installation.html).

#### EasyOCR

EasyOCR is a Python-based OCR backend with wide language support and strong performance.

```shell
pip install "kreuzberg[easyocr]"
```

#### PaddleOCR

```shell
pip install "kreuzberg[paddleocr]"
```

!!! warning "Python Compatibility"

    PaddleOCR is only available on Python 3.12 and below. PaddlePaddle does not support Python 3.13 and above.

### Chunking

Chunking is an optional feature - useful for RAG applications among others. Kreuzberg uses the excellent `semantic-text-splitter` package for chunking. To install Kreuzberg with chunking support, you can use:

```shell
pip install "kreuzberg[chunking]"
```

### All Optional Dependencies

To install Kreuzberg with all optional dependencies, you can use the `all` extra group:

```shell
pip install "kreuzberg[all]"
```

This is equivalent to:

```shell
pip install "kreuzberg[chunking,easyocr,paddleocr]"
```

!!! note

    Remember that even when installing with the `all` extra group, PaddleOCR will only be available on Python 3.12 and below.
