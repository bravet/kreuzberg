from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Final, Literal

from PIL import Image

from kreuzberg._mime_types import PLAIN_TEXT_MIME_TYPE
from kreuzberg._ocr._base import OCRBackend
from kreuzberg._types import ExtractionResult, Metadata
from kreuzberg._utils._string import normalize_spaces
from kreuzberg._utils._sync import run_sync
from kreuzberg.exceptions import MissingDependencyError, OCRError, ValidationError

if TYPE_CHECKING:
    from pathlib import Path

try:  # pragma: no cover
    from typing import Unpack  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover
    from typing_extensions import Unpack


EASYOCR_SUPPORTED_LANGUAGE_CODES: Final[set[str]] = {
    "abq",
    "ady",
    "af",
    "ang",
    "ar",
    "as",
    "ava",
    "az",
    "be",
    "bg",
    "bh",
    "bho",
    "bn",
    "bs",
    "ch_sim",
    "ch_tra",
    "che",
    "cs",
    "cy",
    "da",
    "dar",
    "de",
    "en",
    "es",
    "et",
    "fa",
    "fr",
    "ga",
    "gom",
    "hi",
    "hr",
    "hu",
    "id",
    "inh",  # codespell:ignore
    "is",
    "it",
    "ja",
    "kbd",
    "kn",
    "ko",
    "ku",
    "la",
    "lbe",
    "lez",
    "lt",
    "lv",
    "mah",
    "mai",
    "mi",
    "mn",
    "mr",
    "ms",
    "mt",
    "ne",
    "new",
    "nl",
    "no",
    "oc",
    "pi",
    "pl",
    "pt",
    "ro",
    "ru",
    "rs_cyrillic",
    "rs_latin",
    "sck",
    "sk",
    "sl",
    "sq",
    "sv",
    "sw",
    "ta",
    "tab",
    "te",  # codespell:ignore
    "th",
    "tjk",
    "tl",
    "tr",
    "ug",
    "uk",
    "ur",
    "uz",
    "vi",
}


@dataclass(unsafe_hash=True, frozen=True)
class EasyOCRConfig:
    """Configuration options for EasyOCR."""

    add_margin: float = 0.1
    """Extend bounding boxes in all directions."""
    adjust_contrast: float = 0.5
    """Target contrast level for low contrast text."""
    beam_width: int = 5
    """Beam width for beam search in recognition."""
    canvas_size: int = 2560
    """Maximum image dimension for detection."""
    contrast_ths: float = 0.1
    """Contrast threshold for preprocessing."""
    decoder: Literal["greedy", "beamsearch", "wordbeamsearch"] = "greedy"
    """Decoder method. Options: 'greedy', 'beamsearch', 'wordbeamsearch'."""
    height_ths: float = 0.5
    """Maximum difference in box height for merging."""
    language: str | list[str] = "en"
    """Language or languages to use for OCR."""
    link_threshold: float = 0.4
    """Link confidence threshold."""
    low_text: float = 0.4
    """Text low-bound score."""
    mag_ratio: float = 1.0
    """Image magnification ratio."""
    min_size: int = 10
    """Minimum text box size in pixels."""
    rotation_info: list[int] | None = None
    """List of angles to try for detection."""
    slope_ths: float = 0.1
    """Maximum slope for merging text boxes."""
    text_threshold: float = 0.7
    """Text confidence threshold."""
    use_gpu: bool = False
    """Whether to use GPU for inference."""
    width_ths: float = 0.5
    """Maximum horizontal distance for merging boxes."""
    x_ths: float = 1.0
    """Maximum horizontal distance for paragraph merging."""
    y_ths: float = 0.5
    """Maximum vertical distance for paragraph merging."""
    ycenter_ths: float = 0.5
    """Maximum shift in y direction for merging."""


class EasyOCRBackend(OCRBackend[EasyOCRConfig]):
    _reader: ClassVar[Any] = None

    async def process_image(self, image: Image.Image, **kwargs: Unpack[EasyOCRConfig]) -> ExtractionResult:
        """Asynchronously process an image and extract its text and metadata using EasyOCR.

        Args:
            image: An instance of PIL.Image representing the input image.
            **kwargs: Configuration parameters for EasyOCR including language, detection thresholds, etc.

        Returns:
            ExtractionResult: The extraction result containing text content, mime type, and metadata.

        Raises:
            OCRError: If OCR processing fails.
        """
        await self._init_easyocr(**kwargs)

        beam_width = kwargs.pop("beam_width")
        try:
            result = await run_sync(
                self._reader.readtext,
                image.tobytes(),
                beamWidth=beam_width,
                **kwargs,
            )

            return self._process_easyocr_result(result, image)
        except Exception as e:
            raise OCRError(f"Failed to OCR using EasyOCR: {e}") from e

    async def process_file(self, path: Path, **kwargs: Unpack[EasyOCRConfig]) -> ExtractionResult:
        """Asynchronously process a file and extract its text and metadata using EasyOCR.

        Args:
            path: A Path object representing the file to be processed.
            **kwargs: Configuration parameters for EasyOCR including language, detection thresholds, etc.

        Returns:
            ExtractionResult: The extraction result containing text content, mime type, and metadata.

        Raises:
            OCRError: If file loading or OCR processing fails.
        """
        await self._init_easyocr(**kwargs)
        try:
            image = await run_sync(Image.open, path)
            return await self.process_image(image, **kwargs)
        except Exception as e:
            raise OCRError(f"Failed to load or process image using EasyOCR: {e}") from e

    @staticmethod
    def _process_easyocr_result(result: list[Any], image: Image.Image) -> ExtractionResult:
        """Process EasyOCR result into an ExtractionResult with metadata.

        Args:
            result: The raw result from EasyOCR.
            image: The original PIL image.

        Returns:
            ExtractionResult: The extraction result containing text content, mime type, and metadata.
        """
        if not result:
            return ExtractionResult(
                content="",
                mime_type=PLAIN_TEXT_MIME_TYPE,
                metadata=Metadata(width=image.width, height=image.height),
                chunks=[],
            )

        expected_tuple_length = 2

        if all(len(item) == expected_tuple_length for item in result):
            text_content = ""
            confidence_sum = 0
            confidence_count = 0

            for text, confidence in result:
                if text:
                    text_content += text + "\n"
                    confidence_sum += confidence
                    confidence_count += 1

            metadata = Metadata(
                width=image.width,
                height=image.height,
            )

            return ExtractionResult(
                content=normalize_spaces(text_content), mime_type=PLAIN_TEXT_MIME_TYPE, metadata=metadata, chunks=[]
            )

        sorted_results = sorted(result, key=lambda x: x[0][0][1] + x[0][2][1])
        line_groups: list[list[Any]] = []
        current_line: list[Any] = []
        prev_y_center: float | None = None
        line_height_threshold = 20

        for item in sorted_results:
            box, text, confidence = item
            y_center = sum(point[1] for point in box) / 4

            if prev_y_center is None or abs(y_center - prev_y_center) > line_height_threshold:
                if current_line:
                    line_groups.append(current_line)
                current_line = [item]
            else:
                current_line.append(item)

            prev_y_center = y_center

        if current_line:
            line_groups.append(current_line)

        text_content = ""
        confidence_sum = 0
        confidence_count = 0

        for line in line_groups:
            line_sorted = sorted(line, key=lambda x: x[0][0][0])

            for item in line_sorted:
                _, text, confidence = item
                if text:
                    text_content += text + " "
                    confidence_sum += confidence
                    confidence_count += 1

            text_content += "\n"

        metadata = Metadata(
            width=image.width,
            height=image.height,
        )

        return ExtractionResult(
            content=normalize_spaces(text_content), mime_type=PLAIN_TEXT_MIME_TYPE, metadata=metadata, chunks=[]
        )

    @classmethod
    def _is_gpu_available(cls) -> bool:
        """Check if GPU is available for EasyOCR.

        Returns:
            bool: True if GPU support is available.
        """
        try:
            import torch

            return torch.cuda.is_available()
        except ImportError:
            return False

    @classmethod
    async def _init_easyocr(cls, **kwargs: Unpack[EasyOCRConfig]) -> None:
        """Initialize EasyOCR with the provided configuration.

        Args:
            **kwargs: Configuration parameters for EasyOCR including language, etc.

        Raises:
            MissingDependencyError: If EasyOCR is not installed.
            OCRError: If initialization fails.
        """
        if cls._reader is not None:
            return

        try:
            import easyocr
        except ImportError as e:
            raise MissingDependencyError.create_for_package(
                dependency_group="easyocr", functionality="EasyOCR as an OCR backend", package_name="easyocr"
            ) from e

        languages = cls._validate_language_code(kwargs.pop("language", "en"))
        has_gpu = cls._is_gpu_available()
        kwargs.setdefault("gpu", has_gpu)
        kwargs.setdefault("detector", True)
        kwargs.setdefault("recognizer", True)
        kwargs.setdefault("download_enabled", True)
        kwargs.setdefault("recog_network", "standard")

        try:
            cls._reader = await run_sync(
                easyocr.Reader,
                languages,
                gpu=kwargs.get("use_gpu"),
                verbose=False,
            )
        except Exception as e:
            raise OCRError(f"Failed to initialize EasyOCR: {e}") from e

    @staticmethod
    def _validate_language_code(language_codes: str | list[str]) -> list[str]:
        """Validate and normalize a provided language code.

        Args:
            language_codes: The language code string.

        Raises:
            ValidationError: If the language is not supported by EasyOCR

        Returns:
            A list with the normalized language code.
        """
        if not isinstance(language_codes, list):
            languages = [language_codes.lower()]
        else:
            languages = [lang.lower() for lang in language_codes]

        if all(lang in EASYOCR_SUPPORTED_LANGUAGE_CODES for lang in languages):
            return languages

        raise ValidationError(
            "The provided language codes are not supported by EasyOCR",
            context={
                "language_code": ",".join([lang for lang in languages if lang not in EASYOCR_SUPPORTED_LANGUAGE_CODES]),
                "supported_languages": ",".join(sorted(EASYOCR_SUPPORTED_LANGUAGE_CODES)),
            },
        )
