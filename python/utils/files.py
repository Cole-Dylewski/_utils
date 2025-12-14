import os
import re
import unicodedata

import pandas as pd


def to_filename_compatible_string(s: str) -> str:
    """
    Converts a string to a filesystem-compatible filename.
    - Converts to ASCII
    - Lowercases all characters
    - Replaces whitespace and underscores with hyphens
    - Removes all non-alphanumeric characters except hyphens and dots
    - Strips leading/trailing hyphens and dots
    """
    s = (
        unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    )  # Remove accents and special chars
    s = s.lower()  # Lowercase for consistency
    s = re.sub(r"[\s_]+", "-", s)  # Normalize spaces and underscores to hyphens
    s = re.sub(r"[^a-z0-9\.-]", "", s)  # Remove invalid filename characters
    return s.strip("-.")  # Remove leading/trailing delimiters


def merge_files(outputFilePath, filesGenerated, resize=False, delete=True):
    """
    Merges a list of files into a single output file.
    Supports PDF, CSV, and PNG output types.

    Parameters:
    - outputFilePath: Path to the final merged file
    - filesGenerated: List of input file paths to merge
    - resize: Not used (included for API compatibility)
    - delete: If True, deletes input files after merging
    """
    outputFileExt = os.path.splitext(outputFilePath)[1].lower()

    if outputFileExt == ".pdf":
        # Merge PDFs using PyPDF2
        import PyPDF2

        merger = PyPDF2.PdfMerger()
        for file_name in filesGenerated:
            merger.append(file_name)
        merger.write(outputFilePath)
        merger.close()

    elif outputFileExt == ".csv":
        # Concatenate CSVs into a single DataFrame, preserving string formatting
        df = pd.DataFrame()
        for file_name in filesGenerated:
            df = pd.concat(
                [df, pd.read_csv(file_name, dtype=str, low_memory=False)], ignore_index=True
            )
        df.to_csv(outputFilePath, index=False)

    elif outputFileExt == ".png":
        # Vertically stack PNG images using PIL
        from PIL import Image

        images = {}
        totalHeight = 0
        maxWidth = 0

        for file_name in filesGenerated:
            img = Image.open(file_name)
            width, height = img.size
            images[totalHeight] = img  # Use height as insertion point
            totalHeight += height
            maxWidth = max(maxWidth, width)

        # Create a new white image and paste each input image at the correct Y-offset
        finalImage = Image.new("RGB", (maxWidth, totalHeight), "white")
        for position, img in images.items():
            finalImage.paste(img, (0, position))
        finalImage.save(outputFilePath)

    else:
        # Unsupported file extension
        raise ValueError(f"Unsupported output file type: {outputFileExt}")

    if delete:
        # Optionally delete the original files
        for file_name in filesGenerated:
            os.remove(file_name)

    return outputFilePath
