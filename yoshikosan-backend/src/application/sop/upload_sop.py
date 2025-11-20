"""SOP Upload Use Case."""

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from src.domain.sop.entities import SOP
from src.domain.sop.repositories import SOPRepository


@dataclass
class UploadSOPRequest:
    """Request to upload a new SOP."""

    title: str
    created_by: UUID
    image_paths: list[Path]
    text_content: str | None = None


@dataclass
class UploadSOPResponse:
    """Response from uploading an SOP."""

    sop_id: UUID
    title: str
    image_paths: list[Path]
    text_content: str | None


class UploadSOPUseCase:
    """Use case for uploading a new SOP.

    This creates an initial SOP entity and saves uploaded files
    to the storage directory for later processing by the structuring use case.
    """

    # File validation constants
    MAX_FILE_SIZE_MB = 10
    ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
    ALLOWED_TEXT_EXTENSIONS = {".txt"}

    def __init__(
        self, sop_repository: SOPRepository, storage_base_path: Path | str = "storage"
    ):
        """Initialize the use case.

        Args:
            sop_repository: Repository for SOP persistence
            storage_base_path: Base path for file storage (default: "storage")
        """
        self.sop_repository = sop_repository
        self.storage_base_path = Path(storage_base_path)

    def _validate_file(self, file_path: Path) -> None:
        """Validate a file for upload.

        Args:
            file_path: Path to file to validate

        Raises:
            ValueError: If file is invalid (doesn't exist, wrong format, too large)
        """
        if not file_path.exists():
            raise ValueError(f"File does not exist: {file_path}")

        # Check file extension
        ext = file_path.suffix.lower()
        allowed_exts = self.ALLOWED_IMAGE_EXTENSIONS | self.ALLOWED_TEXT_EXTENSIONS
        if ext not in allowed_exts:
            raise ValueError(
                f"Invalid file extension: {ext}. Allowed: {', '.join(allowed_exts)}"
            )

        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            raise ValueError(
                f"File too large: {file_size_mb:.2f}MB. Maximum: {self.MAX_FILE_SIZE_MB}MB"
            )

    def _save_files_to_storage(
        self, sop_id: UUID, file_paths: list[Path]
    ) -> list[Path]:
        """Save uploaded files to SOP storage directory.

        Args:
            sop_id: SOP ID for directory naming
            file_paths: List of file paths to save

        Returns:
            List of new file paths in storage directory
        """
        # Create SOP storage directory
        sop_storage_dir = self.storage_base_path / "sops" / str(sop_id)
        sop_storage_dir.mkdir(parents=True, exist_ok=True)

        saved_paths: list[Path] = []
        for file_path in file_paths:
            # Copy file to storage directory
            dest_path = sop_storage_dir / file_path.name
            dest_path.write_bytes(file_path.read_bytes())
            saved_paths.append(dest_path)

        return saved_paths

    async def execute(self, request: UploadSOPRequest) -> UploadSOPResponse:
        """Execute the SOP upload use case.

        Args:
            request: Upload request with title, optional images, and/or text

        Returns:
            UploadSOPResponse with SOP ID and file paths

        Raises:
            ValueError: If validation fails (invalid files, empty title, no content, etc.)
        """
        # Validate request
        if not request.title.strip():
            raise ValueError("SOP title is required")

        # Ensure at least one of images or text_content is provided
        if not request.image_paths and not request.text_content:
            raise ValueError("At least one of image files or text content is required")

        # Validate all files (if provided)
        for file_path in request.image_paths:
            self._validate_file(file_path)

        # Create SOP entity
        sop = SOP(title=request.title, created_by=request.created_by)

        # Save SOP to database (this generates the ID)
        saved_sop = await self.sop_repository.save(sop)

        # Save files to storage (if images provided)
        saved_image_paths = []
        if request.image_paths:
            saved_image_paths = self._save_files_to_storage(
                saved_sop.id, request.image_paths
            )

        return UploadSOPResponse(
            sop_id=saved_sop.id,
            title=saved_sop.title,
            image_paths=saved_image_paths,
            text_content=request.text_content,
        )
