import click
import select

from .main import main
from .utils import linesplit

@main.group()
@click.pass_context
def log(ctx):
    pass

@log.command()
@click.option('-n', '--lines', default=200, help='emite as últimas n linhas')
@click.pass_obj
def unio(client, lines=200):
    click.secho("Lendo arquivo de logs do UNIO Server...", fg='blue')
    return _log(client, lines, 'fhserver')

@log.command()
@click.option('-n', '--lines', default=200, help='emite as últimas n linhas')
@click.pass_obj
def hass(client, lines=200):
    click.secho("Lendo arquivo de logs do Home Assistant...", fg='blue')
    return _log(client, lines, 'hass')

@log.command()
@click.option('-n', '--lines', default=200, help='emite as últimas n linhas')
@click.pass_obj
def zigbee(client, lines=200):
    click.secho("Lendo arquivo de logs do Zigbee2Mqtt...", fg='blue')
    return _log(client, lines, 'zigbee2mqtt')
    
def _log(client, lines, filename):
    command = 'tail -f -n {} /var/log/{}.log'.format(lines, filename)

    channel = client._ssh.get_transport().open_session()
    channel.exec_command(command)

    while True:
        try:
            rl, _, _ = select.select([channel], [], [], 0.0)
            if len(rl) > 0:
                for line in linesplit(channel):
                    click.echo(line)

        except (KeyboardInterrupt, SystemExit):
            break

    click.echo('Finalizando sessão com UNIO Server remoto...')
    client.close()