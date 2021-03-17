import click
import os

from lib.shell import interactive_shell
from .main import main

@main.command()
@click.pass_obj
def shell(client):
    rows, columns = os.popen('stty size', 'r').read().split()
    channel = client._ssh.invoke_shell(width=int(columns), height=int(rows))
    click.secho("*** Abrindo o MATRIX ***", fg='blue')
    interactive_shell(channel)

    click.echo('Finalizando sessão com UNIO Server remoto...')
    client.close()