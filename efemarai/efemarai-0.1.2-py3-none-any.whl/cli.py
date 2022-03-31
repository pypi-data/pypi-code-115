from datetime import datetime
from re import T
from pathlib import Path
import click
import efemarai as ef
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm


console = Console()


@click.group()
def main():
    """Efemarai CLI."""
    pass


@main.command()
@click.option("-c", "--config", help="Optional configuration file.")
def init(config):
    """Initialize Efemarai."""
    ef.Session._user_setup(config_file=config)


@main.group()
def project():
    """Manage projects."""
    pass


@project.command("create")
@click.argument("definition-file", required=True)
@click.option(
    "--exists-ok/--exists-not-ok",
    default=False,
    help="Append differences if project already exists.",
)
def project_create(definition_file, exists_ok):
    """Create a project following the specified configuration file.

    definition_file (str): YAML file containing project definition."""
    result = ef.Session().load(definition_file, exists_ok=exists_ok)
    console.print(result)


@project.command("list")
def project_list():
    """Lists the projects associated with the current user."""
    table = Table(box=None)
    [table.add_column(x) for x in ["Id", "Name", "Problem Type"]]
    for m in ef.Session().projects:
        table.add_row(m.id, m.name, str(m.problem_type))
    console.print(table)


@project.command("delete")
@click.argument("project", required=True)
@click.option("-y", "--yes", default=False, is_flag=True, help="Confirm deletion.")
def project_delete(project, yes):
    """Delete the specified project."""
    project = ef.Session().project(project)
    if not project:
        console.print(f"Project '{project}' does not exist.")
        return

    if yes or Confirm.ask(
        f"Do you want to delete project [bold]{project.name}[/bold] including all stress tests, models, datasets and domains?",
        default=False,
    ):
        project.delete()


@main.group()
def model():
    """Manage models."""
    pass


@model.command("list")
@click.option(
    "-f", "--file", help="Name of the Efemarai file (Default is 'efemarai.yaml')"
)
def model_list(file):
    """Lists the models in the current project."""
    project = _get_project(file)
    if not project:
        return

    table = Table(box=None)
    [table.add_column(x) for x in ["Id", "Name"]]
    for m in project.models:
        table.add_row(m.id, m.name)
    console.print(table)


@model.command("create")
@click.argument("definition-file", required=True)
@click.option(
    "-f", "--file", help="Name of the Efemarai file (Default is 'efemarai.yaml')"
)
@click.option("-v", "--verbose", count=True, help="Print resulting model.")
@click.option(
    "--exists-ok/--exists-not-ok",
    default=False,
    help="Specifies if a model can be overwritten.",
)
def model_create(definition_file, file, verbose, exists_ok):
    """Create a model in the current project."""

    project = _get_project(file)

    definition = ef.Session._read_config(definition_file)

    try:
        model_definition = definition["model"]
    except KeyError:
        console.print(f":poop: Key 'model' not found in {definition}", style="red")
        exit(1)

    try:
        model = project.create_model(**model_definition, exists_ok=exists_ok)
    except ValueError as e:
        console.print(e)
        exit(1)

    if verbose:
        console.print(model)

    console.print(model.id)

    return model


@model.command("delete")
@click.argument("model", required=True)
@click.option(
    "-f", "--file", help="Name of the Efemarai file (Default is 'efemarai.yaml')"
)
def model_delete(model, file):
    """Delete a model from the current project.

    MODEL - the name or ID of the model."""
    project = _get_project(file)
    if not project:
        return

    if _check_for_multiple_entities(project.models, model):
        console.print("There are multiple models with the given:\n")
        models = [t for t in project.models if t.name == test]
        _print_table(models)
        console.print(
            f"\nRun the command with a specific model id: [bold green]$ efemarai model delete {models[0].id}",
        )
        return

    model = project.model(model)
    model.delete()


@main.group()
def domain():
    """Manage domains."""
    pass


@domain.command("list")
@click.option(
    "-f", "--file", help="Name of the Efemarai file (Default is 'efemarai.yaml')"
)
def domain_list(file):
    """Lists the domains in the current project."""
    project = _get_project(file)
    if not project:
        return

    table = Table(box=None)
    [table.add_column(x) for x in ["Id", "Name"]]
    for d in project.domains:
        table.add_row(d.id, d.name)
    console.print(table)


@domain.command("create")
@click.argument("definition-file", required=True)
@click.option(
    "-f", "--file", help="Name of the Efemarai file (Default is 'efemarai.yaml')"
)
def domain_create(definition_file, file):
    """Create a domain in the current project.

    definition_file (str): YAML file containing domain definition."""
    project = _get_project(file)
    if not project:
        return
    definition = ef.Session._read_config(definition_file)
    domain = project.create_domain(**defintion["domain"])
    return domain


@domain.command("delete")
@click.argument("domain", required=True)
@click.option(
    "-f", "--file", help="Name of the Efemarai file (Default is 'efemarai.yaml')"
)
def domain_delete(domain, file):
    """Delete a domain from the current project.

    DOMAIN - the name or ID of the domain."""
    project = _get_project(file)
    if not project:
        return

    if _check_for_multiple_entities(project.domains, domain):
        console.print("There are multiple domains with the given name:\n")
        domains = [t for t in project.domains if t.name == test]
        _print_table(domains)
        console.print(
            f"\nRun the command with a specific domain id: [bold green]$ efemarai domain delete {domains[0].id}",
        )
        return

    domain = project.domain(domain)
    domain.delete()


@domain.command("download")
@click.argument("domain", required=True)
@click.option("-o", "--output", default=None, help="Optional domain output file.")
@click.option(
    "-f", "--file", help="Name of the Efemarai file (Default is 'efemarai.yaml')"
)
def domain_download(domain, output, file):
    """Download a domain.

    DOMAIN - the name of the domain."""
    project = _get_project(file)
    if not project:
        return

    domain = project.domain(domain)
    filename = domain.download(filename=output)
    console.print(
        (f":heavy_check_mark: Downloaded '{domain.name}' reports to: \n  {filename}"),
        style="green",
    )


@main.group()
def dataset():
    """Manage datasets."""
    pass


@dataset.command("list")
@click.option(
    "-f", "--file", help="Name of the Efemarai file (Default is 'efemarai.yaml')"
)
def dataset_list(file):
    """Lists the datasets in the current project."""
    project = _get_project(file)
    if not project:
        return

    table = Table(box=None)
    [table.add_column(x) for x in ["Id", "Name", "Loaded"]]
    for d in project.datasets:
        table.add_row(d.id, d.name, str(d.loaded))
    console.print(table)


@dataset.command("create")
@click.argument("definition_file", required=True)
@click.option(
    "-f", "--file", help="Name of the Efemarai file (Default is 'efemarai.yaml')"
)
def dataset_create(definition_file, file):
    """Create a dataset in the current project.

    definition_file (str): YAML file containing dataset definition."""
    project = _get_project(file)
    if not project:
        return
    definition = ef.Session._read_config(definition_file)
    dataset = project.create_dataset(**definition["dataset"])
    return dataset


@dataset.command("delete")
@click.argument("dataset", required=True)
@click.option(
    "-f", "--file", help="Name of the Efemarai file (Default is 'efemarai.yaml')"
)
def dataset_delete(dataset, file):
    """Delete a dataset from the current project.

    DATASET - the name or ID of the dataset."""
    project = _get_project(file)
    if not project:
        return

    if _check_for_multiple_entities(project.datasets, dataset):
        console.print("There are multiple datasets with the given name:\n")
        datasets = [t for t in project.datasets if t.name == test]
        _print_table(datasets)
        console.print(
            f"\nRun the command with a specific dataset id: [bold green]$ efemarai dataset delete {datasets[0].id}",
        )
        return

    dataset = project.dataset(dataset)
    dataset.delete()


@main.group()
def test():
    """Manage stress tests."""
    pass


@test.command("list")
@click.option(
    "-f", "--file", help="Name of the Efemarai file (Default is 'efemarai.yaml')"
)
def test_list(file):
    """Lists the stress tests in the current project."""
    project = _get_project(file)
    if not project:
        return

    _print_table(project.stress_tests)


@test.command("run")
@click.argument("definition-file", required=True)
@click.option(
    "-f", "--file", help="Name of the Efemarai file (Default is 'efemarai.yaml')"
)
def test_run(definition_file, file):
    """Run a stress test.

    definition_file (str): YAML file containing stress test definition."""
    project = _get_project(file)
    if not project:
        return

    definition = ef.Session._read_config(definition_file)
    test = project.create_stress_test(**definition["test"])
    cfg = ef.Session._read_config()
    console.print(f"{cfg['url']}project/{project.id}/runs/{test.id}")


@test.command("delete")
@click.argument("test", required=True)
@click.option(
    "-f", "--file", help="Name of the Efemarai file (Default is 'efemarai.yaml')"
)
def test_delete(test, file):
    """Delete a stress test from the current project.

    TEST - the name or ID of the stress test."""
    project = _get_project(file)
    if not project:
        return

    if _check_for_multiple_entities(project.stress_tests, test):
        console.print("There are multiple stress tests with the given name:\n")
        tests = [t for t in project.stress_tests if t.name == test]
        _print_table(tests)
        console.print(
            f"\nRun the command with a specific stress test id: [bold green]$ efemarai test delete {tests[0].id}",
        )
        return

    test = project.stress_test(test)
    test.delete()


@test.command("download")
@click.argument("test", required=True)
@click.option("--min_score", default=0, help="Minimum score for the samples.")
@click.option("--include_dataset", default=False, help="Include original test dataset.")
@click.option("--path", default=None, help="Path to the downloaded files.")
@click.option("--unzip", default=True, help="Whether to unzip the resulting file.")
@click.option("--ignore_cache", default=False, help="Ignore local cache.")
@click.option(
    "-f", "--file", help="Name of the Efemarai file (Default is 'efemarai.yaml')"
)
def test_download(test, min_score, include_dataset, path, unzip, ignore_cache, file):
    """Download the stress test vulnerabilities dataset.

    TEST - the name or ID of the stress test to download."""
    project = _get_project(file)
    if not project:
        return

    test = project.stress_test(test)
    test.vulnerabilities_dataset(
        min_score=min_score,
        include_dataset=include_dataset,
        path=path,
        unzip=unzip,
        ignore_cache=ignore_cache,
    )


@test.command("reports")
@click.argument("test", required=True)
@click.option("-o", "--output", default=None, help="Optional output file.")
@click.option(
    "-f", "--file", help="Name of the Efemarai file (Default is 'efemarai.yaml')"
)
def test_reports(test, output, file):
    """Export the stress test reports.

    TEST - name or ID of the stress test."""
    project = _get_project(file)
    if not project:
        return

    test = project.stress_test(test)
    filename = test.download_reports(filename=output)
    console.print(
        (f":heavy_check_mark: Downloaded '{test.name}' reports to: \n  {filename}"),
        style="green",
    )


def _print_table(tests):
    table = Table(box=None)
    [table.add_column(x) for x in ["Id", "Name", "Model", "Dataset", "Domain", "State"]]
    for t in tests:
        table.add_row(
            t.id, t.name, t.model.name, t.dataset.name, t.domain.name, str(t.state)
        )
    console.print(table)


def _check_for_multiple_entities(entities, name):
    length = len(list(filter(lambda x: x.name == name, entities)))
    return length > 1


def _get_project(file=None):
    if file is None:
        file = "efemarai.yaml"

    if not Path(file).is_file():
        console.print(
            f":poop: Cannot find 'efemarai.yaml' in the current directory.", style="red"
        )
        exit(1)

    conf = ef.Session()._load_config_file(file)
    if "project" not in conf or "name" not in conf["project"]:
        console.print(
            f":poop: '{file}' file not configured properly (does not container project and name within).",
            style="red",
        )
        exit(1)

    name = conf["project"]["name"]
    project = ef.Session().project(name)
    if not project:
        console.print(f"Project '{name}' does not exist.")
        return

    return project


if __name__ == "__main__":
    main()
