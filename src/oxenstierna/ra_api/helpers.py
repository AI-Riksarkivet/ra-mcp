from enum import Enum


class Region:
    """Represents a region parameter for IIIF Image API 3.0."""

    @staticmethod
    def full() -> str:
        """Get the full image."""
        return "full"

    @staticmethod
    def square() -> str:
        """Get a centered square crop of the image."""
        return "square"

    @staticmethod
    def pixels(x: int, y: int, width: int, height: int) -> str:
        """Get a region by pixel coordinates."""
        if x < 0 or y < 0 or width <= 0 or height <= 0:
            raise ValueError(
                "Region coordinates must be non-negative and dimensions must be positive"
            )
        return f"{x},{y},{width},{height}"

    @staticmethod
    def percentage(x: float, y: float, width: float, height: float) -> str:
        """Get a region by percentage coordinates."""
        if not all(0 <= coord <= 100 for coord in [x, y, width, height]):
            raise ValueError("Percentage coordinates must be between 0 and 100")
        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be positive")
        return f"pct:{x},{y},{width},{height}"


class Size:
    """Represents a size parameter for IIIF Image API 3.0."""

    @staticmethod
    def max() -> str:
        """Get the maximum size (full dimensions)."""
        return "max"

    @staticmethod
    def width(width: int) -> str:
        """Set the width while maintaining the aspect ratio."""
        if width <= 0:
            raise ValueError("Width must be positive")
        return f"{width},"

    @staticmethod
    def height(height: int) -> str:
        """Set the height while maintaining the aspect ratio."""
        if height <= 0:
            raise ValueError("Height must be positive")
        return f",{height}"

    @staticmethod
    def exact(width: int, height: int) -> str:
        """Set exact dimensions (may distort image)."""
        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be positive")
        return f"{width},{height}"


class Rotation:
    """Represents a rotation parameter for IIIF Image API 3.0."""

    VALID_DEGREES = [0, 90, 180, 270]

    @staticmethod
    def none() -> str:
        """No rotation."""
        return "0"

    @staticmethod
    def degrees(degrees: int) -> str:
        """Rotate the image by the specified number of degrees."""
        if degrees not in Rotation.VALID_DEGREES:
            raise ValueError(
                f"Riksarkivet only supports rotation by 90-degree intervals: {Rotation.VALID_DEGREES}"
            )
        return str(degrees)

    @staticmethod
    def mirrored(degrees: int = 0) -> str:
        """Mirror the image horizontally and then rotate by the specified degrees."""
        if degrees not in Rotation.VALID_DEGREES:
            raise ValueError(
                f"Riksarkivet only supports rotation by 90-degree intervals: {Rotation.VALID_DEGREES}"
            )
        return f"!{degrees}"


class Quality(str, Enum):
    """Available quality parameters for IIIF Image API 3.0."""

    DEFAULT = "default"


class Format(str, Enum):
    """Available format parameters for IIIF Image API 3.0."""

    JPG = "jpg"
