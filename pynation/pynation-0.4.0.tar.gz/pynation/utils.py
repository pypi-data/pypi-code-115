
import click


class DefaultCommand(click.Group):

    def command(self, *args, **kwargs):
        default_command = kwargs.pop("default_command", False)
        if default_command and not args:
            kwargs["name"] = kwargs.get("name", "info")

        decorator = super(DefaultCommand, self).command(*args, **kwargs)
        if default_command:
            def new_decorator(f):
                cmd = decorator(f)
                self.default_command = cmd.name
                # cmd.hidden = True  # Hide "->" from the command line
                return cmd
            return new_decorator

        return decorator

    def resolve_command(self, ctx, args):
        try:
            return super(DefaultCommand, self).resolve_command(ctx, args)
        except click.UsageError:
            # Since "country_name" is not a command name, we want to pass "->"
            args.insert(0, self.default_command)
            return super(DefaultCommand, self).resolve_command(ctx, args)


def return_country(data_source, column):
    _country = data_source.get(column.title(), None)
    if _country is not None:
        return _country


def error_message():
    click.secho("Country does not exist. Perhaps, write the full name?", fg="red")
