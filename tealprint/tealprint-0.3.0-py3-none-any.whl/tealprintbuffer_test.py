import pytest
from colored import fg

from . import TealConfig, TealLevel, TealPrintBuffer

indent = "".ljust(TealConfig.indent_by, TealConfig.indent_char)


class T:
    logger = TealPrintBuffer()

    @staticmethod
    def reset():
        TealConfig.level = TealLevel.info
        T.logger = TealPrintBuffer()


@pytest.mark.parametrize(
    "name,expected,function",
    [
        (
            "Not indented by default",
            "test\n",
            lambda: T.logger.info("test"),
        ),
        (
            "Indented when when pushed with same lever",
            f"{indent}test\n",
            lambda: (
                T.logger.push_indent(TealLevel.info),
                T.logger.info("test"),
            ),
        ),
        (
            "Indented when when pushed with higher lever",
            f"{indent}test\n",
            lambda: (
                T.logger.push_indent(TealLevel.warning),
                T.logger.info("test"),
            ),
        ),
        (
            "Not Indented when when pushed with same lever",
            "test\n",
            lambda: (
                T.logger.push_indent(TealLevel.verbose),
                T.logger.info("test"),
            ),
        ),
        (
            "Indented and unindent directly in info()",
            f"first\n{indent}test\nthird\n",
            lambda: (
                T.logger.info("first", push_indent=True),
                T.logger.info("test", pop_indent=True),
                T.logger.info("third"),
            ),
        ),
        (
            "Don't de-indent after pop if level is lower than current",
            f"{indent}test\n{indent}test\ntest\n",
            lambda: (
                T.logger.push_indent(TealLevel.info),
                T.logger.push_indent(TealLevel.verbose),
                T.logger.info("test"),
                T.logger.pop_indent(),
                T.logger.info("test"),
                T.logger.pop_indent(),
                T.logger.info("test"),
            ),
        ),
        (
            "No indent after cleaning",
            "test\n",
            lambda: (
                T.logger.push_indent(TealLevel.info),
                T.logger.clear_indent(),
                T.logger.info("test"),
            ),
        ),
        (
            "Always push indent when logging",
            "Works!\n",
            lambda: (
                T.logger.info("Works!", push_indent=True),
                T.logger.debug("Not shown", push_indent=True),
                T.logger.pop_indent(),
                T.logger.pop_indent(),
            ),
        ),
    ],
)
def test_indentation(name, expected: str, function) -> None:
    print(name)

    function()

    T.logger.buffer.seek(0)
    result = T.logger.buffer.read()
    assert expected == result

    T.reset()


def test_remove_unicode() -> None:
    TealConfig.unicode_enabled = False

    T.logger.info("🔥 Rocket 🔥", color=fg("red"))

    T.logger.buffer.seek(0)
    result = T.logger.buffer.read()
    assert " Rocket \n" == result

    TealConfig.reset()
    T.reset()


def test_remove_colors() -> None:
    TealConfig.colors_enabled = False

    T.logger.info("🔥 Rocket 🔥", color=fg("red"))

    T.logger.buffer.seek(0)
    result = T.logger.buffer.read()
    assert "🔥 Rocket 🔥\n" == result

    TealConfig.reset()
    T.reset()
