import click

from .main import main
from .log import unio as log_unio, \
	hass as log_hass, \
    zigbee as log_zigbee
	

@main.group()
@click.pass_context
def restart(ctx):
    pass

@restart.command()
@click.pass_obj
@click.pass_context
def unio(ctx, client):
    click.echo("Reiniciando Aplicação")
    client.run("supervisorctl restart fhserver")

    ctx.invoke(log_unio, lines=0)

@restart.command()
@click.pass_obj
@click.pass_context
def hass(ctx, client):
    click.echo("Reiniciando Home Assistant")
    client.run("supervisorctl restart hass")

    ctx.invoke(log_hass, lines=0)

@restart.command()
@click.pass_obj
@click.pass_context
def zigbee(ctx, client):
    click.echo("Reiniciando Zigbee2Mqtt")
    client.run("supervisorctl restart zigbee2mqtt")

    ctx.invoke(log_zigbee, lines=0)

@restart.command()
@click.pass_obj
@click.pass_context
def mqtt(ctx, client):
    click.echo("Reiniciando Mosquitto MQTT Broker")
    client.sudo_run("systemctl restart mosquitto")

    #ctx.invoke(log_mosquitto, lines=0)
    click.echo('Finalizando sessão com UNIO Server remoto...')
    client.close()
    

@restart.command()
@click.pass_obj
def os(client):
    click.echo("Reiniciando Sistema!")
    
    client.sudo_run("reboot now")

    #TODO? keep trying reconnecting, then tail app log file?

    click.echo('Finalizando sessão com UNIO Server remoto...')
    client.close()