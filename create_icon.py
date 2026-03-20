#!/usr/bin/env python3
"""
Generate a simple icon for Medical Research RAG application.
This creates a basic ICO file with medical/research theme.

Requirements: PIL (Pillow)
Install: pip install Pillow

Usage: python create_icon.py
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    import os
except ImportError:
    print("Error: Pillow library not found.")
    print("Install with: pip install Pillow")
    exit(1)


def create_medical_rag_icon(output_path="app_icon.ico", size=256):
    """
    Create a simple icon with medical/research theme.

    Design: Blue circle background with white medical cross and document symbol
    """

    # Create a new image with transparency
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Define colors (Medical Blue theme)
    bg_color = (37, 99, 235, 255)      # Professional blue (#2563EB)
    accent_color = (59, 130, 246, 255) # Lighter blue (#3B82F6)
    white = (255, 255, 255, 255)

    # Draw circular background with gradient effect
    center = size // 2
    radius = size // 2 - 10

    # Outer circle (darker)
    draw.ellipse([10, 10, size-10, size-10], fill=bg_color, outline=accent_color, width=4)

    # Draw medical cross symbol
    cross_width = size // 8
    cross_length = size // 2.5
    cross_center_x = center - size // 8
    cross_center_y = center

    # Vertical bar of cross
    draw.rectangle([
        cross_center_x - cross_width // 2,
        cross_center_y - cross_length // 2,
        cross_center_x + cross_width // 2,
        cross_center_y + cross_length // 2
    ], fill=white)

    # Horizontal bar of cross
    draw.rectangle([
        cross_center_x - cross_length // 2,
        cross_center_y - cross_width // 2,
        cross_center_x + cross_length // 2,
        cross_center_y + cross_width // 2
    ], fill=white)

    # Draw document/paper symbol (representing research/documents)
    doc_x = center + size // 6
    doc_y = center - size // 6
    doc_width = size // 4
    doc_height = size // 3

    # Document background
    draw.rectangle([
        doc_x,
        doc_y,
        doc_x + doc_width,
        doc_y + doc_height
    ], fill=white, outline=white, width=2)

    # Document lines (representing text)
    line_margin = doc_width // 8
    line_spacing = doc_height // 6

    for i in range(3):
        y_pos = doc_y + line_spacing * (i + 1)
        draw.line([
            doc_x + line_margin,
            y_pos,
            doc_x + doc_width - line_margin,
            y_pos
        ], fill=bg_color, width=2)

    # Add corner fold to document
    fold_size = doc_width // 3
    draw.polygon([
        (doc_x + doc_width - fold_size, doc_y),
        (doc_x + doc_width, doc_y + fold_size),
        (doc_x + doc_width, doc_y)
    ], fill=accent_color)

    # Create multiple sizes for ICO file
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    images = []

    for icon_size in sizes:
        resized = img.resize(icon_size, Image.Resampling.LANCZOS)
        images.append(resized)

    # Save as ICO with multiple resolutions
    images[0].save(
        output_path,
        format='ICO',
        sizes=[(img.width, img.height) for img in images],
        append_images=images[1:]
    )

    print(f"✓ Icon created successfully: {output_path}")
    print(f"  - Multi-resolution ICO file")
    print(f"  - Sizes: {', '.join([f'{s[0]}x{s[1]}' for s in sizes])}")
    print(f"  - Theme: Medical blue with cross and document")
    print(f"\nNext steps:")
    print(f"  1. Review the icon by double-clicking: {output_path}")
    print(f"  2. If satisfied, transfer to Windows with other project files")
    print(f"  3. Rebuild installer in Inno Setup")
    print(f"\nTo create a custom icon instead:")
    print(f"  - See CREATE_ICON_GUIDE.md for detailed instructions")
    print(f"  - Use online tools like favicon.io for easy customization")


def create_text_icon(text="MR", output_path="app_icon_text.ico", size=256):
    """
    Create a simple text-based icon.

    Args:
        text: Text to display (e.g., "MR" for Medical Research)
    """

    # Create image with transparency
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Colors
    bg_color = (37, 99, 235, 255)      # Blue
    text_color = (255, 255, 255, 255)  # White

    # Draw circular background
    draw.ellipse([10, 10, size-10, size-10], fill=bg_color, outline=(59, 130, 246, 255), width=4)

    # Try to use a nice font, fall back to default if not available
    try:
        # Try different font locations for cross-platform compatibility
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",           # macOS
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
            "C:\\Windows\\Fonts\\arial.ttf",                 # Windows
        ]

        font = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, int(size * 0.4))
                break

        if font is None:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()

    # Get text bounding box for centering
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Center text
    text_x = (size - text_width) // 2 - bbox[0]
    text_y = (size - text_height) // 2 - bbox[1]

    # Draw text
    draw.text((text_x, text_y), text, fill=text_color, font=font)

    # Create multiple sizes
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    images = [img.resize(s, Image.Resampling.LANCZOS) for s in sizes]

    # Save as ICO
    images[0].save(
        output_path,
        format='ICO',
        sizes=[(img.width, img.height) for img in images],
        append_images=images[1:]
    )

    print(f"✓ Text icon created: {output_path}")
    print(f"  - Text: '{text}'")
    print(f"  - Blue circular background")


if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("Medical Research RAG - Icon Generator")
    print("=" * 60)
    print()

    # Check if Pillow is installed
    try:
        import PIL
        print(f"✓ Pillow version: {PIL.__version__}")
    except ImportError:
        print("✗ Error: Pillow not installed")
        print("\nInstall with:")
        print("  pip install Pillow")
        print("\nor:")
        print("  pip3 install Pillow")
        sys.exit(1)

    print()

    # Offer options
    print("Choose icon type:")
    print("  1. Medical symbol icon (cross + document) - Recommended")
    print("  2. Text-based icon (\"MR\" or custom text)")
    print("  3. Both")
    print()

    try:
        choice = input("Enter choice (1-3) [default: 1]: ").strip() or "1"

        if choice == "1":
            create_medical_rag_icon("app_icon.ico")
        elif choice == "2":
            custom_text = input("Enter text for icon (default: MR): ").strip() or "MR"
            create_text_icon(custom_text, "app_icon.ico")
        elif choice == "3":
            create_medical_rag_icon("app_icon.ico")
            print()
            custom_text = input("Enter text for alternate icon (default: MR): ").strip() or "MR"
            create_text_icon(custom_text, "app_icon_text.ico")
        else:
            print("Invalid choice, creating default medical icon...")
            create_medical_rag_icon("app_icon.ico")

        print()
        print("=" * 60)
        print("✓ Icon generation complete!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nFalling back to default icon...")
        create_medical_rag_icon("app_icon.ico")
