"""Generate pixel-art sloth icon for system tray and executable."""
from pathlib import Path
from PIL import Image, ImageDraw


def create_pet_icon(output_path: str = "assets/icon.ico") -> None:
    """Generate a multi-resolution .ico with 16x16 and 32x32 pixel-art sloth."""
    sizes = [(32, 32), (16, 16)]  # largest first — Pillow uses main image size as max
    images = []

    for size in sizes:
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        s = size[0] // 16  # scale factor

        # Body (brown oval)
        draw.ellipse([2*s, 3*s, 14*s, 15*s], fill=(139, 90, 43, 255))
        # Face area (lighter brown)
        draw.ellipse([4*s, 4*s, 12*s, 12*s], fill=(180, 120, 60, 255))
        # Eyes (black)
        draw.ellipse([5*s, 6*s, 7*s, 8*s], fill=(0, 0, 0, 255))
        draw.ellipse([9*s, 6*s, 11*s, 8*s], fill=(0, 0, 0, 255))
        # Eye highlights (white)
        draw.rectangle([5*s, 6*s, 6*s, 7*s], fill=(255, 255, 255, 255))
        draw.rectangle([9*s, 6*s, 10*s, 7*s], fill=(255, 255, 255, 255))
        # Nose (dark brown)
        draw.ellipse([7*s, 9*s, 9*s, 10*s], fill=(80, 50, 20, 255))
        # Mouth (small line)
        if s >= 2:
            draw.line([7*s, 11*s, 9*s, 11*s], fill=(80, 50, 20, 255), width=max(1, s//2))

        images.append(img)

    # Save as multi-resolution .ico
    # NOTE: Pillow ICO _save uses main image.size as max — largest must be first
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    images[0].save(
        output_path,
        format="ICO",
        sizes=[img.size for img in images],
        append_images=images[1:],
    )


if __name__ == "__main__":
    create_pet_icon()
    print("Icon generated: assets/icon.ico")
