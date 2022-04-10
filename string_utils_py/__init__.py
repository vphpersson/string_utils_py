from typing import Any, Pattern, Optional, AnyStr
from re import compile as re_compile, sub as re_sub, escape as re_escape, Pattern as RePattern, DOTALL as RE_DOTALL

_CAMEL_CASED_LETTER_PATTERN = re_compile(pattern=r'(?<=.)((?<=[a-z])[A-Z]|[A-Z](?=[a-z]))')

_SNAKE_KEBAB_CASED_LETTER_PATTERN = re_compile(pattern=r'[-_]([A-Za-z])')


def uppercase_first_character(string: str) -> str:
    """
    Uppercase the first character of a string.

    :param string: A string whose first character to uppercase.
    :return: The input string with its first character uppercased.
    """

    return re_sub(pattern=r'^.', repl=lambda match: match.group(0).capitalize(), string=string)


def lowercase_first_character(string: str) -> str:
    """
    Lowercase the first character of a string.

    :param string: A string whose first character to lowercase.
    :return: The input string with its first character lowercased.
    """

    return re_sub(pattern=r'^.', repl=lambda match: match.group(0).lower(), string=string)


def to_snake_case(string: str) -> str:
    """
    Convert a string into a snake-cased representation.

    :param string: A camel-, Pascal-, or kebab-cased string.
    :return: A snake-cased representation of the provided string.
    """

    return _CAMEL_CASED_LETTER_PATTERN.sub(repl=lambda match: f'_{match.group(0)}', string=string.replace('-', '')) \
        .replace('-', '_') \
        .lower()


def to_pascal_case(string: str) -> str:
    """
    Convert a string into a Pascal-cased representation.

    :param string: A camel-, snake-, or kebab-cased string.
    :return: A Pascal-cased representation of the provided string.
    """

    return uppercase_first_character(
        string=_SNAKE_KEBAB_CASED_LETTER_PATTERN.sub(repl=lambda match: match.group(1).upper(), string=string)
    )


def to_camel_case(string: str) -> str:
    """
    Convert a string into a camel-cased representation.

    :param string: A Pascal-, kebab-, or snake-cased string.
    :return: A camel-cased representation of the provided string.
    """

    return lowercase_first_character(
        string=_SNAKE_KEBAB_CASED_LETTER_PATTERN.sub(repl=lambda match: match.group(1).upper(), string=string)
    )


def underline(string: str, underline_character: str = '=') -> str:
    """
    Underline a string with a sequence of character equal to the string's length.

    :param string: A string to be underlined.
    :param underline_character: The character which will compose the underline.
    :return: The input string underlined with the specified charater.
    """

    return f'{string}\n{len(string) * underline_character}'


def text_align_delimiter(text: str, delimiter: str = ': ', put_non_match_after_delimiter: bool = True) -> str:
    """
    Align multi-line text around a delimiter.

    :param text: The text to be aligned.
    :param delimiter: The delimiter to align around.
    :param put_non_match_after_delimiter: Whether lines in the text not having the delimiter should be put after the
        alignment position.
    :return: The input text aligned around the specified delimiter.
    """

    max_delimiter_pos: int = max(line.find(delimiter) for line in text.splitlines())

    return '\n'.join(
        (
            (line[:delimiter_pos].rjust(max_delimiter_pos) + line[delimiter_pos:])
            if (delimiter_pos := line.find(delimiter)) != -1 else (
                (' ' * (max_delimiter_pos + len(delimiter)) + line) if (line and put_non_match_after_delimiter) else line
            )
        )
        for line in text.splitlines()
    )


def expand_var(
    string: str,
    expand_map: dict[str, Any],
    var_char: str = '%',
    end_var_char: Optional[str] = '',
    case_sensitive: bool = True,
    exception_on_unexpanded: bool = False
) -> str:
    """
    Expand variables in a string.

    If an encountered variable name is not in provided map, the function can either ignore it -- leaving the variable
    reference in-place -- or raise an exception.

    If `end_var_char` is not specified (i.e. is an empty string), `var_char` is used in its place. If `end_var_char` is
    set to `None`, no surrounding character to the right is used.

    :param string: The string to be expanded.
    :param expand_map: A name-to-value map of variable names and their corresponding values.
    :param var_char: A character that surrounds the variable names if `end_var_char` is not specified, otherwise that
        is immediately to the left of the variable name.
    :param end_var_char: A character that is immediately to the right of the variable name, unless set to `None`, in
        which case no character is used.
    :param case_sensitive: Whether the variable names in the string are case-sensitive. If not, they are lower-cased
        prior to the map lookup.
    :param exception_on_unexpanded: Raise an exception if a variable name in the string is not in the map.
    :return: The variable-expanded string.
    """

    escaped_var_char: str = re_escape(var_char)

    if end_var_char is None:
        var_pattern: Pattern = re_compile(f'{escaped_var_char}(?P<variable_name>.+?)\\b')
    else:
        # NOTE: `end_var_char` should not be escaped within the bracket expression ("[]"), as characters within such
        # expressions are parsed literally.
        var_pattern: Pattern = re_compile(
            f'{escaped_var_char}(?P<variable_name>[^{end_var_char or var_char}]+){re_escape(end_var_char or var_char)}'
        )

    search_start_offset = 0
    while match := var_pattern.search(string=string, pos=search_start_offset):
        var_pos_start, var_pos_end = match.span(0)

        variable_name: str = match.groupdict()['variable_name']
        if not case_sensitive:
            variable_name = variable_name.lower()

        if variable_name in expand_map:
            expanded_head: str = string[:var_pos_start] + str(expand_map[variable_name])
            string: str = expanded_head + string[var_pos_end:]
            search_start_offset: int = len(expanded_head)
        elif exception_on_unexpanded:
            raise KeyError(f'The variable name {variable_name} is not in the expand map.')
        else:
            search_start_offset: int = var_pos_end

    return string


def extract_ngrams(text: AnyStr, ngram_len: int) -> tuple[AnyStr, ...]:
    """
    Extract n-grams from a text.

    The n-grams are extracted using a regular expression pattern. Note that
    the `DOTALL` flag is used, allowing newlines to be included in the n-grams;
    this is especially expected when providing a byte-string text.

    :param text: A text from which to extract n-grams.
    :param ngram_len: The length of the n-grams to be extracted from the text.
    :return: N-grams of the specified length extracted from the text.
    """

    pattern: AnyStr = ngram_len * '.'
    if isinstance(text, bytes):
        pattern = pattern.encode()

    re_pattern: RePattern = re_compile(pattern=pattern, flags=RE_DOTALL)

    return tuple(
        re_match
        for text_offset in range(ngram_len)
        for re_match in re_pattern.findall(text[text_offset:])
    )
