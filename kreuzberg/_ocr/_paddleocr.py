from __future__ import annotations

import platform
import sys
from dataclasses import dataclass
from importlib.util import find_spec
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


PADDLEOCR_SUPPORTED_LANGUAGE_CODES: Final[set[str]] = {"ch", "en", "french", "german", "japan", "korean"}


@dataclass(unsafe_hash=True, frozen=True)
class PaddleOCRConfig:
    """Configuration options for PaddleOCR.

    This TypedDict provides type hints and documentation for all PaddleOCR parameters.
    """

    cls_image_shape: str = "3,48,192"
    """Image shape for classification algorithm in format 'channels,height,width'."""
    det_algorithm: Literal["DB", "EAST", "SAST", "PSE", "FCE", "PAN", "CT", "DB++", "Layout"] = "DB"
    """Detection algorithm."""
    det_db_box_thresh: float = 0.5
    """Score threshold for detected boxes. Boxes below this value are discarded."""
    det_db_thresh: float = 0.3
    """Binarization threshold for DB output map."""
    det_db_unclip_ratio: float = 2.0
    """Expansion ratio for detected text boxes."""
    det_east_cover_thresh: float = 0.1
    """Score threshold for EAST output boxes."""
    det_east_nms_thresh: float = 0.2
    """NMS threshold for EAST model output boxes."""
    det_east_score_thresh: float = 0.8
    """Binarization threshold for EAST output map."""
    det_max_side_len: int = 960
    """Maximum size of image long side. Images exceeding this will be proportionally resized."""
    drop_score: float = 0.5
    """Filter recognition results by confidence score. Results below this are discarded."""
    enable_mkldnn: bool = False
    """Whether to enable MKL-DNN acceleration (Intel CPU only)."""
    gpu_mem: int = 8000
    """GPU memory size (in MB) to use for initialization."""
    language: str = "en"
    """Language to use for OCR."""
    max_text_length: int = 25
    """Maximum text length that the recognition algorithm can recognize."""
    rec: bool = True
    """Enable text recognition when using the ocr() function."""
    rec_algorithm: Literal[
        "CRNN",
        "SRN",
        "NRTR",
        "SAR",
        "SEED",
        "SVTR",
        "SVTR_LCNet",
        "ViTSTR",
        "ABINet",
        "VisionLAN",
        "SPIN",
        "RobustScanner",
        "RFL",
    ] = "CRNN"
    """Recognition algorithm."""
    rec_image_shape: str = "3,32,320"
    """Image shape for recognition algorithm in format 'channels,height,width'."""
    table: bool = True
    """Whether to enable table recognition."""
    use_angle_cls: bool = True
    """Whether to use text orientation classification model."""
    use_gpu: bool = False
    """Whether to use GPU for inference. Requires installing the paddlepaddle-gpu package"""
    use_space_char: bool = True
    """Whether to recognize spaces."""
    use_zero_copy_run: bool = False
    """Whether to enable zero_copy_run for inference optimization."""


class PaddleBackend(OCRBackend[PaddleOCRConfig]):
    _paddle_ocr: ClassVar[Any] = None

    async def process_image(self, image: Image.Image, **kwargs: Unpack[PaddleOCRConfig]) -> ExtractionResult:
        """Asynchronously process an image and extract its text and metadata using PaddleOCR.

        Args:
            image: An instance of PIL.Image representing the input image.
            **kwargs: Configuration parameters for PaddleOCR including language, detection thresholds, etc.

        Returns:
            ExtractionResult: The extraction result containing text content, mime type, and metadata.

        Raises:
            OCRError: If OCR processing fails.
        """
        import numpy as np

        await self._init_paddle_ocr(**kwargs)
        image_np = np.array(image)
        try:
            result = await run_sync(self._paddle_ocr.ocr, image_np, cls=kwargs.get("use_angle_cls", True))
            return self._process_paddle_result(result, image)
        except Exception as e:
            raise OCRError(f"Failed to OCR using PaddleOCR: {e}") from e

    async def process_file(self, path: Path, **kwargs: Unpack[PaddleOCRConfig]) -> ExtractionResult:
        """Asynchronously process a file and extract its text and metadata using PaddleOCR.

        Args:
            path: A Path object representing the file to be processed.
            **kwargs: Configuration parameters for PaddleOCR including language, detection thresholds, etc.

        Returns:
            ExtractionResult: The extraction result containing text content, mime type, and metadata.

        Raises:
            OCRError: If file loading or OCR processing fails.
        """
        await self._init_paddle_ocr(**kwargs)
        try:
            image = await run_sync(Image.open, path)
            return await self.process_image(image, **kwargs)
        except Exception as e:
            raise OCRError(f"Failed to load or process image using PaddleOCR: {e}") from e

    @staticmethod
    def _process_paddle_result(result: list[Any], image: Image.Image) -> ExtractionResult:
        """Process PaddleOCR result into an ExtractionResult with metadata.

        Args:
            result: The raw result from PaddleOCR.
            image: The original PIL image.

        Returns:
            ExtractionResult: The extraction result containing text content, mime type, and metadata.
        """
        text_content = ""
        confidence_sum = 0
        confidence_count = 0

        for page_result in result:
            if not page_result:
                continue

            sorted_boxes = sorted(page_result, key=lambda x: x[0][0][1])
            line_groups: list[list[Any]] = []
            current_line: list[Any] = []
            prev_y: float | None = None

            for box in sorted_boxes:
                box_points, (_, _) = box
                current_y = sum(point[1] for point in box_points) / 4
                min_box_distance = 20

                if prev_y is None or abs(current_y - prev_y) > min_box_distance:
                    if current_line:
                        line_groups.append(current_line)
                    current_line = [box]
                else:
                    current_line.append(box)

                prev_y = current_y

            if current_line:
                line_groups.append(current_line)

            for line in line_groups:
                line_sorted = sorted(line, key=lambda x: x[0][0][0])

                for box in line_sorted:
                    _, (text, confidence) = box
                    if text:
                        text_content += text + " "
                        confidence_sum += confidence
                        confidence_count += 1

                text_content += "\n"

        width, height = image.size
        metadata = Metadata(
            width=width,
            height=height,
        )

        return ExtractionResult(
            content=normalize_spaces(text_content), mime_type=PLAIN_TEXT_MIME_TYPE, metadata=metadata, chunks=[]
        )

    @classmethod
    def _is_mkldnn_supported(cls) -> bool:
        """Check if the current architecture supports MKL-DNN optimization.

        Returns:
            True if MKL-DNN is supported on this architecture.
        """
        system = platform.system().lower()
        processor = platform.processor().lower()
        machine = platform.machine().lower()

        if system in ("linux", "windows"):
            return "intel" in processor or "x86" in machine or "amd64" in machine or "x86_64" in machine

        if system == "darwin":
            return machine == "x86_64"

        return False

    @classmethod
    async def _init_paddle_ocr(cls, **kwargs: Unpack[PaddleOCRConfig]) -> None:
        """Initialize PaddleOCR with the provided configuration.

        Args:
            **kwargs: Configuration parameters for PaddleOCR including language, detection thresholds, etc.

        Raises:
            MissingDependencyError: If PaddleOCR is not installed.
            OCRError: If initialization fails.
            ValidationError: If the python version is too high.
        """
        if cls._paddle_ocr is not None:
            return

        if sys.version_info >= (3, 13):  # pragma: no cover
            raise ValidationError(
                "PaddleOCR is only available in python 3.12 and below. Please downgrade your Python or switch to a different OCR backend.",
                context={"issue": "https://github.com/PaddlePaddle/Paddle/issues/71616"},
            )

        try:
            from paddleocr import PaddleOCR
        except ImportError as e:
            raise MissingDependencyError.create_for_package(
                dependency_group="paddleocr", functionality="PaddleOCR as an OCR backend", package_name="paddleocr"
            ) from e

        language = cls._validate_language_code(kwargs.pop("language", "en"))
        has_gpu_package = bool(find_spec("paddlepaddle_gpu"))
        kwargs.setdefault("use_angle_cls", True)
        kwargs.setdefault("use_gpu", has_gpu_package)
        kwargs.setdefault("enable_mkldnn", cls._is_mkldnn_supported() and not has_gpu_package)
        kwargs.setdefault("det_db_thresh", 0.3)
        kwargs.setdefault("det_db_box_thresh", 0.5)
        kwargs.setdefault("det_db_unclip_ratio", 1.6)

        try:
            cls._paddle_ocr = await run_sync(PaddleOCR, lang=language, show_log=False, **kwargs)
        except Exception as e:
            raise OCRError(f"Failed to initialize PaddleOCR: {e}") from e

    @staticmethod
    def _validate_language_code(lang_code: str) -> str:
        """Convert a language code to PaddleOCR format.

        Args:
            lang_code: ISO language code or language name

        Raises:
            ValidationError: If the language is not supported by PaddleOCR

        Returns:
            Language code compatible with PaddleOCR
        """
        normalized = lang_code.lower()
        if normalized in PADDLEOCR_SUPPORTED_LANGUAGE_CODES:
            return normalized

        raise ValidationError(
            "The provided language code is not supported by PaddleOCR",
            context={
                "language_code": lang_code,
                "supported_languages": ",".join(sorted(PADDLEOCR_SUPPORTED_LANGUAGE_CODES)),
            },
        )
