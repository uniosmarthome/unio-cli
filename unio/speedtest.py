import click
import select

from .main import main

@main.command()
@click.pass_obj
def speedtest(client):
    client.run('speedtest -h', v=False)
    if not client.check('usage: speedtest'):
        click.secho('Speedtest não instalado. Instalando...', fg='red')

        client.put('./lib/speedtest-cli', '/tmp/speedtest')
        client.run('mv /tmp/speedtest /usr/bin/speedtest', sudo=True)
        client.run('chmod 751 /usr/bin/speedtest', sudo=True)

    click.echo('Executando teste de velocidade...')
    client.run('speedtest')

    click.echo('Finalizando sessão com UNIO Server remoto...')
    client.close()