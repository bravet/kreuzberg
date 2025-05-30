from __future__ import annotations

import sys
from collections.abc import Awaitable
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Callable, Literal, TypedDict, Union

from kreuzberg._constants import DEFAULT_MAX_CHARACTERS, DEFAULT_MAX_OVERLAP
from kreuzberg.exceptions import ValidationError

if sys.version_info < (3, 11):  # pragma: no cover
    from typing_extensions import NotRequired
else:  # pragma: no cover
    from typing import NotRequired

if TYPE_CHECKING:
    from kreuzberg._ocr._easyocr import EasyOCRConfig
    from kreuzberg._ocr._paddleocr import PaddleOCRConfig
    from kreuzberg._ocr._tesseract import TesseractConfig

OcrBackendType = Literal["tesseract", "easyocr", "paddleocr"]


class Metadata(TypedDict, total=False):
    """Base metadata common to all document types.

    All fields will only be included if they contain non-empty values.
    Any field that would be empty or None is omitted from the dictionary.
    """

    authors: NotRequired[list[str]]
    """List of document authors."""
    categories: NotRequired[list[str]]
    """Categories or classifications."""
    citations: NotRequired[list[str]]
    """Citation identifiers."""
    comments: NotRequired[str]
    """General comments."""
    copyright: NotRequired[str]
    """Copyright information."""
    created_at: NotRequired[str]
    """Creation timestamp in ISO format."""
    created_by: NotRequired[str]
    """Document creator."""
    description: NotRequired[str]
    """Document description."""
    fonts: NotRequired[list[str]]
    """List of fonts used in the document."""
    height: NotRequired[int]
    """Height of the document page/slide/image, if applicable."""
    identifier: NotRequired[str]
    """Unique document identifier."""
    keywords: NotRequired[list[str]]
    """Keywords or tags."""
    languages: NotRequired[list[str]]
    """Document language code."""
    license: NotRequired[str]
    """License information."""
    modified_at: NotRequired[str]
    """Last modification timestamp in ISO format."""
    modified_by: NotRequired[str]
    """Username of last modifier."""
    organization: NotRequired[str | list[str]]
    """Organizational affiliation."""
    publisher: NotRequired[str]
    """Publisher or organization name."""
    references: NotRequired[list[str]]
    """Reference entries."""
    status: NotRequired[str]
    """Document status (e.g., draft, final)."""
    subject: NotRequired[str]
    """Document subject or topic."""
    subtitle: NotRequired[str]
    """Document subtitle."""
    summary: NotRequired[str]
    """Document Summary"""
    title: NotRequired[str]
    """Document title."""
    version: NotRequired[str]
    """Version identifier or revision number."""
    width: NotRequired[int]
    """Width of the document page/slide/image, if applicable."""


@dataclass
class ExtractionResult:
    """The result of a file extraction."""

    content: str
    """The extracted content."""
    chunks: list[str]
    """The extracted content chunks. This is an empty list if 'chunk_content' is not set to True in the ExtractionConfig."""
    mime_type: str
    """The mime type of the extracted content. Is either text/plain or text/markdown."""
    metadata: Metadata
    """The metadata of the content."""


PostProcessingHook = Callable[[ExtractionResult], Union[ExtractionResult, Awaitable[ExtractionResult]]]
ValidationHook = Callable[[ExtractionResult], Union[None, Awaitable[None]]]


@dataclass(unsafe_hash=True)
class ExtractionConfig:
    """Represents configuration settings for an extraction process.

    This class encapsulates the configuration options for extracting text
    from images or documents using Optical Character Recognition (OCR). It
    provides options to customize the OCR behavior, select the backend
    engine, and configure engine-specific parameters.
    """

    force_ocr: bool = False
    """Whether to force OCR."""
    chunk_content: bool = False
    """Whether to chunk the content into smaller chunks."""
    max_chars: int = DEFAULT_MAX_CHARACTERS
    """The size of each chunk in characters."""
    max_overlap: int = DEFAULT_MAX_OVERLAP
    """The overlap between chunks in characters."""
    ocr_backend: OcrBackendType | None = "tesseract"
    """The OCR backend to use."""
    ocr_config: TesseractConfig | PaddleOCRConfig | EasyOCRConfig | None = None
    """Configuration to pass to the OCR backend."""
    post_processing_hooks: list[PostProcessingHook] | None = None
    """Post processing hooks to call after processing is done and before the final result is returned."""
    validators: list[ValidationHook] | None = None
    """Validation hooks to call after processing is done and before post-processing and result return."""

    def __post_init__(self) -> None:
        from kreuzberg._ocr._easyocr import EasyOCRConfig
        from kreuzberg._ocr._paddleocr import PaddleOCRConfig
        from kreuzberg._ocr._tesseract import TesseractConfig

        if self.ocr_backend is None and self.ocr_config is not None:
            raise ValidationError("'ocr_backend' is None but 'ocr_config' is provided")

        if self.ocr_config is not None and (
            (self.ocr_backend == "tesseract" and not isinstance(self.ocr_config, TesseractConfig))
            or (self.ocr_backend == "easyocr" and not isinstance(self.ocr_config, EasyOCRConfig))
            or (self.ocr_backend == "paddleocr" and not isinstance(self.ocr_config, PaddleOCRConfig))
        ):
            raise ValidationError(
                "incompatible 'ocr_config' value provided for 'ocr_backend'",
                context={"ocr_backend": self.ocr_backend, "ocr_config": type(self.ocr_config).__name__},
            )

    def get_config_dict(self) -> dict[str, Any]:
        """Returns the OCR configuration object based on the backend specified.

        Returns:
            A dict of the OCR configuration or an empty dict if no backend is provided.
        """
        if self.ocr_backend is not None:
            if self.ocr_config is not None:
                return asdict(self.ocr_config)
            if self.ocr_backend == "tesseract":
                from kreuzberg._ocr._tesseract import TesseractConfig

                return asdict(TesseractConfig())
            if self.ocr_backend == "easyocr":
                from kreuzberg._ocr._easyocr import EasyOCRConfig

                return asdict(EasyOCRConfig())
            from kreuzberg._ocr._paddleocr import PaddleOCRConfig

            return asdict(PaddleOCRConfig())
        return {}
