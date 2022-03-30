import click

from markdrip.mods import generator as gen

@click.command()
@click.option("--output", "-o", help="Output destination file path")
@click.option("--theme", "-t", default="github", help="Applicable CSS file name. Does not include extension.")

@click.argument("target")
def main(target, theme, output):

    mkup, filename = gen.markup(target)
    css = gen.load_css(theme)
<<<<<<< Updated upstream
    if css != "\\[ERROR]/":
        if output == "./":
            output = filename + ".html"
        print(target, output, theme)
        gen.rendor(mkup, css, output)


=======
    if output == None:
        output = target

    gen.rendor(mkup, css, output)
>>>>>>> Stashed changes

if __name__ == "__main__":
    main()
