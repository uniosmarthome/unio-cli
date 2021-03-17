import click

from lib.shell import interactive_shell
from .main import main

@main.group()
def prop():
    pass

@prop.command()
@click.pass_obj
def list(client):
    click.echo('Listando propriedades configuradas:')
    props = client.props
    for prop in props:
        click.secho('  {}: {}'.format(prop, props[prop]))

@prop.command()
@click.argument('prop')
@click.pass_obj
def get(client, prop):
    if prop not in client.props:
        click.secho('NOT FOUND: {}'.format(prop), fg='red')
        return

    click.secho('  {}: {}'.format(prop, client.props[prop]))

@prop.command()
@click.argument('prop')
@click.argument('value')
@click.pass_obj
@click.pass_context
def set(ctx, client, prop, value):
    if prop not in client.props:
        click.secho('INVALID PROPERTY: {}'.format(prop), fg='red')
        return
    
    client.props[prop] = value
    client.save_properties()
    click.secho('  {}: {}'.format(prop, client.props[prop]))
