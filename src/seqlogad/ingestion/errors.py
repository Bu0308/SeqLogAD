"""Expected errors raised by dataset acquisition and integrity tooling."""


class DatasetError(Exception):
    """Base class for expected dataset-tooling failures."""


class DatasetConfigError(DatasetError):
    """Raised when dataset configuration is missing or malformed."""


class DatasetNotFoundError(DatasetError):
    """Raised when a required dataset or manifest path does not exist."""


class MissingRequiredFileError(DatasetError):
    """Raised when an operation requires a complete dataset."""


class ManifestValidationError(DatasetError):
    """Raised when a manifest cannot be parsed or validated."""


class MetadataExtractionError(DatasetError):
    """Raised when raw metadata cannot be extracted without ambiguity."""


class ChecksumMismatchError(DatasetError):
    """Raised when downloaded or local content fails checksum validation."""
