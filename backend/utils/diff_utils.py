import difflib


def get_diff_html(original_text, modified_text):
    d = difflib.Differ()
    diff = list(d.compare(original_text.split(), modified_text.split()))

    result_html = []
    for word in diff:
        if word.startswith("+ "):
            result_html.append(f'<span style="background-color: #c8e6c9;">{word[2:]}</span>')
        elif word.startswith("- "):
            result_html.append(
                f'<span style="background-color: #ffcdd2;text-decoration:line-through;">{word[2:]}</span>'
            )
        else:
            result_html.append(word[2:])

    return " ".join(result_html)
