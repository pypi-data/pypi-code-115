import sys

import typer
import importlib


app = typer.Typer()

def import_class(mod_str: str):
    split_import_string = mod_str.split(".")
    import_path = ".".join(split_import_string[:-1])
    import_class_string = split_import_string[-1]
    mod = importlib.import_module(import_path)
    metrics_class = getattr(mod, import_class_string)
    return metrics_class


@app.command()
def luigi(task_path: str):
    try:
        import luigi
        from sirena.luigi.sample_dag import build_task_tree
    except ImportError:
        typer.echo("Luigi not installed. Please `pip install luigi` to use `sirena luigi`")
        sys.exit(1)

    luigi_task = import_class(task_path)
    fc = build_task_tree(luigi_task())

    typer.echo(fc.render())

@app.command()
def pydantic():
    typer.echo("Not implemented")

if __name__ == "__main__":
    app()