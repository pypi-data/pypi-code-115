<<<<<<< Updated upstream
import os
import pathlib

=======
import pathlib                            
>>>>>>> Stashed changes
import mistletoe
from jinja2 import Template
base = os.path.dirname(os.path.abspath(__file__))

<<<<<<< Updated upstream
CSS_DIR = os.path.normpath(os.path.join(base, '../css/'))
=======
from sys import exit

CSS_DIR = pathlib.Path("./markdrip/css/")
>>>>>>> Stashed changes
CUSTOM_CSS_DIR = pathlib.Path().home() / pathlib.Path(".markdrip")
BASE_DIR = os.path.normpath(os.path.join(base, '../templete/'))

def markup(filepath):
    filepath = pathlib.Path(filepath)
    filename = filepath.stem
    with open(filepath) as f:
        text = f.read()

    mkup = mistletoe.markdown(text)
    return (mkup, filename)


def load_css(css_name):
<<<<<<< Updated upstream
=======
    print("theme name ==> " + css_name)
>>>>>>> Stashed changes

    load_path = CSS_DIR / pathlib.Path(css_name).with_suffix(".css")
    print(f"Debug: {load_path.resolve()} Is exists? {load_path.resolve().exists()}")
    if load_path.exists() == True:
<<<<<<< Updated upstream
        print("load_path(CSS) ==> " + str(load_path))
        with open(load_path) as css_file:
            css = css_file.read()
        return css

    load_path = (CUSTOM_CSS_DIR / pathlib.Path(css_name).with_suffix(".css"))
    if load_path.exists() == True:
        print("load_path ==> " + str(load_path.resolve()))
        with open(load_path) as css_file:
            css = css_file.read()
        return css
    print("EROOR")
    print("Not Found Theme")
    print("Theme Name ==> " + css_name + "(.css)")
    return "\\[ERROR]/"
=======
        print("load_path ==> " + str(load_path))
        try:
            with open(load_path.resolve()) as css_file:
                css = css_file.read()
        except FileNotFoundError:
            print ("Error: The built-in theme cannot be found. Please file an Isssue as it may be a bug.")
            # print("Error emoji is 🌲")
            exit(1)

        return css

    load_path = (CUSTOM_CSS_DIR / pathlib.Path(css_name).with_suffix(".css"))

    print("load_path ==> " + str(load_path.resolve()))

    try:
        with open(load_path.resolve()) as css_file:
            css = css_file.read()

    except FileNotFoundError:
        print ("Error: Custom CSS file not found. Did you install your custom CSS file? Or have you specified it correctly?")
        exit(1)

    return css
>>>>>>> Stashed changes



def rendor(html, css, filename=None, basename="base.html"):
<<<<<<< Updated upstream
    #print(filename)
    if (BASE_DIR / pathlib.Path(basename)).exists() == True:
        print("Base Template ==> " + str(BASE_DIR / pathlib.Path(basename)))
        with open(BASE_DIR / pathlib.Path(basename)) as tmpl:
            templete = tmpl.read()

        templete = Template(templete)
        data = {"content": html, "style": css, "filename": filename}
        result = templete.render(data)

        path = pathlib.Path(filename).resolve()

        with open(path, "w") as f:
            print("write ==> " + str(path))
            f.write(result)
    else:
        print("EROOR")
        print("Not Found Templete")
        print("Theme Templete ==> " + basename + "(.html)")
=======
    print(filename)
    print("Base Template" + str(BASE_DIR / pathlib.Path(basename)))
    try:
        with open(BASE_DIR / pathlib.Path(basename)) as tmpl:
            templete = tmpl.read()
    except FileNotFoundError:
        print("Error: Base Template is Not Found.")
        # print("Error Emoji is 🍅")


    templete = Template(templete)
    data = {"content": html, "style": css, "filename": filename}
    result = templete.render(data)

    # Swap extensions
    path = pathlib.Path(filename).resolve()
    path = path.stem + ".html"

    print(str(path))

    with open(path, "w") as f:
        print("write ==> " + str(path))
        f.write(result)
>>>>>>> Stashed changes
