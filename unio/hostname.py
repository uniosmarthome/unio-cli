import click

from .main import main

@main.group(invoke_without_command=True)
@click.pass_obj
def hostname(client):
    client.read_hostname()

@hostname.command()
@click.option("-p",'--primary', is_flag=True, default=False)
@click.pass_obj
def update(client, primary):
    client.update_hostname(primary)