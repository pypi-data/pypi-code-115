"""Console script for syllable_reading."""
import sys
from syllable_reading.syllable_reading import run


def main(args=None):
    args = sys.argv[1:]
    args_str = " ".join(args)
    bolded_text = run(args_str)
    print(bolded_text)


if __name__ == "__main__":
    main()
