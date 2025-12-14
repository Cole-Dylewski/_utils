def color_print(styles):
    """
    Concatenate strings with specified text and background colors and print them in one line.

    :param styles: List of dictionaries containing:
                   - 'string': Text to print (required)
                   - 'text': Text color key from text_colors (optional)
                   - 'background': Background color key from background_colors (optional)
                   - 'reset': Boolean, whether to reset styles after the string (default True)
    """
    # Expanded color dictionaries
    text_colors = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "bright_black": "\033[90m",
        "bright_red": "\033[91m",
        "bright_green": "\033[92m",
        "bright_yellow": "\033[93m",
        "bright_blue": "\033[94m",
        "bright_magenta": "\033[95m",
        "bright_cyan": "\033[96m",
        "bright_white": "\033[97m",
        "orange": "\033[38;5;202m",
        "pink": "\033[38;5;205m",
        "lime": "\033[38;5;154m",
        "teal": "\033[38;5;44m",
        "purple": "\033[38;5;93m",
        "brown": "\033[38;5;94m",
        "gold": "\033[38;5;220m",
        "silver": "\033[38;5;250m",
        "coral": "\033[38;5;210m",
        "navy": "\033[38;5;17m",
        "peach": "\033[38;5;216m",
        "ivory": "\033[38;5;230m",
        "turquoise": "\033[38;5;49m",
        "emerald": "\033[38;5;40m",
        "charcoal": "\033[38;5;240m",
        "sky_blue": "\033[38;5;117m",
        "rose": "\033[38;5;213m",
        "mint": "\033[38;5;122m",
        "khaki": "\033[38;5;187m",
        "violet": "\033[38;5;177m",
        "beige": "\033[38;5;230m",
        "crimson": "\033[38;5;197m",
        "aqua": "\033[38;5;123m",
        "salmon": "\033[38;5;209m",
    }
    background_colors = {
        "black": "\033[40m",
        "red": "\033[41m",
        "green": "\033[42m",
        "yellow": "\033[43m",
        "blue": "\033[44m",
        "magenta": "\033[45m",
        "cyan": "\033[46m",
        "white": "\033[47m",
        "bright_black": "\033[100m",
        "bright_red": "\033[101m",
        "bright_green": "\033[102m",
        "bright_yellow": "\033[103m",
        "bright_blue": "\033[104m",
        "bright_magenta": "\033[105m",
        "bright_cyan": "\033[106m",
        "bright_white": "\033[107m",
        "orange": "\033[48;5;202m",
        "pink": "\033[48;5;205m",
        "lime": "\033[48;5;154m",
        "teal": "\033[48;5;44m",
        "purple": "\033[48;5;93m",
        "brown": "\033[48;5;94m",
        "gold": "\033[48;5;220m",
        "silver": "\033[48;5;250m",
        "coral": "\033[48;5;210m",
        "navy": "\033[48;5;17m",
        "peach": "\033[48;5;216m",
        "ivory": "\033[48;5;230m",
        "turquoise": "\033[48;5;49m",
        "emerald": "\033[48;5;40m",
        "charcoal": "\033[48;5;240m",
        "sky_blue": "\033[48;5;117m",
        "rose": "\033[48;5;213m",
        "mint": "\033[48;5;122m",
        "khaki": "\033[48;5;187m",
        "violet": "\033[48;5;177m",
        "beige": "\033[48;5;230m",
        "crimson": "\033[48;5;197m",
        "aqua": "\033[48;5;123m",
        "salmon": "\033[48;5;209m",
    }
    reset_code = "\033[0m"

    result = ""
    for style in styles:
        string = style.get("string", "")
        text_color = text_colors.get(style.get("text", ""), "")
        background_color = background_colors.get(style.get("background", ""), "")
        reset = style.get("reset", True)

        # Build the styled string
        styled_string = f"{text_color}{background_color}{string}"
        if reset:
            styled_string += reset_code
        result += styled_string

    # Print the concatenated result
    print(result)


# Example Usage
styles = [
    {"string": "Hello", "text": "red", "background": "yellow", "reset": True},
    {"string": " ", "reset": False},  # Space
    {"string": "World!", "text": "lime", "background": "navy", "reset": True},
    {"string": " Python is colorful.", "text": "violet", "background": "beige", "reset": True},
]

color_print(styles)
