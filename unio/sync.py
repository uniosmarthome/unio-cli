import click
import re

from .main import main

@main.command()
@click.option('-d', '--debug', is_flag=True, default=False, help='usar url através de tunel')
@click.pass_obj
def sync(client, debug=False, close=True):
    click.secho('Sincronizando Aplicação com UNIO Cloud', fg='blue')
    client.run("cd /opt/fhserver; PYTHONPATH=app:lib:. APP_SETTINGS=config.DevelopmentConfig {} python3 app/fhsync.py" \
        .format("" if not debug else 'CLOUD_URL=http://localhost:5000'), timeout=None)
    
    if close:
        click.echo('Finalizando sessão com UNIO Server remoto...')
        client.close()