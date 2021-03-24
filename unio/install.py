import click
import os
import datetime
from pkg_resources import resource_stream

from .main import main
from .log import unio as log_unio
from .sync import sync

@main.command()
@click.argument('version')
@click.pass_obj
@click.pass_context
def install(ctx, client, version):
    python_packages_path = '/usr/local/lib/python3.8/site-packages/'

    click.echo('Instalando update: {}'.format(version))

    update_filename = 'unio-server-{}.zip'.format(version)
    
    click.echo("Fazendo upload do pacote de atualização: " + update_filename)
    client.putfo(resource_stream('resources', update_filename), remote_path='/tmp/{}'.format(update_filename))

    backup_filename = datetime.datetime.now().strftime("fhserver.%Y%m%d.%H%M%S.bak")
    backup_location = '/opt/{}'.format(backup_filename)
    click.echo("Fazendo backup para {}".format(backup_location))
    client.run("mv /opt/fhserver {}".format(backup_location), sudo=True)

    click.echo("Descompactando arquivo de atualizaçaão...")
    client.run("mkdir /opt/fhserver/", sudo=True)
    client.run("unzip -o /tmp/{} -d /opt/fhserver/".format(update_filename), sudo=True, v=False)

    click.echo('Copiando boards.json da instalação anterior')
    client.run("cp /opt/{}/boards.json /opt/fhserver/".format(backup_filename), sudo=True)

    click.echo("Aplicando permissões da aplicação")
    client.run("chmod -R 770 /opt/fhserver/", sudo=True)
    client.run("chown -R root:fhome /opt/fhserver/", sudo=True)

    click.echo("Aplicando permissões das configurações do supervisor.fhserver")
    client.run("chmod 770 /etc/supervisor/conf.d/fhserver.conf", sudo=True)
    client.run("chown root:fhome /etc/supervisor/conf.d/fhserver.conf", sudo=True)

    stdout = client.run("cat /home/pi/.bashrc", v=False)
    has_command1 = False
    has_command2 = False
    for line in stdout:
        if line.startswith('export LC_ALL='):
            has_command1 = True
        if line.startswith('export LANG='):
            has_command2 = True

    if not has_command1:
        click.echo("Adicionando parâmetro de configuração no .bashrc: LC_ALL")
        client.run('echo -e "export LC_ALL=pt_BR.UTF-8\\n\\n$(cat /home/pi/.bashrc)" > /home/pi/.bashrc')
    if not has_command2:
        click.echo("Adicionando parâmetro de configuração no .bashrc: LANG")
        client.run('echo -e "export LANG=pt_BR.UTF-8\\n$(cat /home/pi/.bashrc)" > /home/pi/.bashrc')

    stdout = client.run("cat /etc/supervisor/conf.d/fhserver.conf", v=False)
    has_property1 = False
    has_property2 = False
    command_changed = False
    environment_changed = False

    supervisor_command = 'command=gunicorn --config /opt/fhserver/gunicorn.conf run:app'
    supervisor_environment ='environment=PYTHONPATH=\"app:lib:.\"'

    for line in stdout:
        if line.startswith('stopasgroup='):
            has_property1 = True
        if line.startswith('stopsignal='):
            has_property2 = True
        if line.strip().startswith('command='):
            if line.strip() != supervisor_command:
                command_changed = True
        if line.strip().startswith('environment='):
            if line.strip() != supervisor_environment:
                environment_changed = True

    if not has_property1:
        click.echo("Adicionando parâmetro de configuração no supervisor.fhserver: stopasgroup")
        client.run("echo 'stopasgroup=true' | tee --append /etc/supervisor/conf.d/fhserver.conf")
    if not has_property2:
        click.echo("Adicionando parâmetro de configuração no supervisor.fhserver: stopsignal")
        client.run("echo 'stopsignal=QUIT' | tee --append /etc/supervisor/conf.d/fhserver.conf")
    if command_changed:
        click.echo("Alterando parâmetro de configuração no supervisor.fhserver: command")
        client.run("sed -Ei 's$command ?= ?(.*)${}$' /etc/supervisor/conf.d/fhserver.conf".format(supervisor_command), sudo=True)
    if environment_changed:
        click.echo("Alterando parâmetro de configuração no supervisor.fhserver: environment")
        client.run("sed -Ei 's$environment ?= ?(.*)${}$' /etc/supervisor/conf.d/fhserver.conf".format(supervisor_environment), sudo=True)

    supervisor_changed = not has_property1 or not has_property2 or command_changed or environment_changed

    click.echo("Aplicando configurações do UNIO Server")
    client.save_properties()

    click.echo('Instalando dependências...')
    client.sudo_run("pip3 install --no-index --find-links /opt/fhserver/lib/pip -r /opt/fhserver/requirements.txt", timeout=None)

    client.run("ls -la {} | grep gpiozero".format(python_packages_path), v=False)
    if not client.check('gpiozero'):
        client.run("cd /opt/fhserver/lib/python-gpiozero; sudo make install", sudo=True, timeout=None)

    click.echo('Limpando instalação antiga...')
    client.sudo_run('cd /home/pi && sudo rm -rf .local .cache .fhserver* .virtualenvs || true')

    click.echo('Aplicando permissões nas dependências')
    client.run("chown -R root:fhome {}".format(python_packages_path), sudo=True)
   
    click.echo('Processando crontab...')
    client.add_cronjob('fhsync', client.sync_cron, 'python3 app/fhsync.py', enabled=True)
    client.add_cronjob('wifisync', client.wifi_cron, '/opt/scripts/check_wifi.sh', enabled=True)

    click.echo("Reiniciando aplicação...")
    client.restart_app(reread=supervisor_changed)
    
    click.secho('Instalação do UNIO Server ({}) finalizada com SUCESSO!'.format(update_filename), fg='green')
    ctx.invoke(log_unio, lines=0)