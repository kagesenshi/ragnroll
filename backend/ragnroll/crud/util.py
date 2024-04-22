from langchain_core.utils.input import get_colored_text, print_text, get_bolded_text

def format_text(text, *, color=None, bold=False):
    if color:
        text = get_colored_text(text, color)
    if bold:
        text = get_bolded_text(text)
    return text