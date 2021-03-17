import click

from lib.shell import interactive_shell
from .main import main

@main.group()
def network():
    pass

@network.command()
@click.pass_obj
def scan(client):
    click.echo('Listando dispositivos conectados:')
    client.sudo_run('fing -r 1 -d true -o table,text')

@network.group()
def ap(client):
    pass

@ap.command()
@click.pass_obj
def enable(client):
    click.echo('Ativando Access Point')
    client.sudo_run('nmcli con up ap')

@ap.command()
@click.pass_obj
def disable(client):
    click.echo('Desativando Access Point')
    client.sudo_run('nmcli con up unio')

@ap.command()
@click.pass_obj
def reset(client):
    click.echo('Resetando configurações do Access Point')
    #TODO aplicar configurações só se precisar
    #client.sudo_run('fing -r 1 -d true -o table,text')
