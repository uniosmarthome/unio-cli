import click

from lib.shell import interactive_shell
from .main import main

@main.group(invoke_without_command=True)
@click.pass_obj
@click.pass_context
def wifi(ctx, client):
    pass

@wifi.command()
@click.pass_obj
def list(client):
    click.echo('Listando redes wifi configuradas:')
    client.sudo_run('nmcli con show')

@wifi.command()
@click.argument('network')
@click.pass_obj
def show(client, network):
    click.echo('Mostrando detalhes da rede {}:'.format(network))
    client.sudo_run('nmcli con show {}'.format(network))

@wifi.command()
@click.argument('network')
@click.option("-s",'--static', is_flag=True, default=False)
@click.pass_obj
def add(client, network, static):
    ssid = click.prompt('Digite o ssid da rede?')
    psk = click.prompt('Qual a senha da rede?')
    
    click.echo('Criando a rede {}: {}'.format(network, ssid))

    wifi_command = 'sudo nmcli con add type wifi con-name {} ifname wlan0 ssid \"{}\"'.format(network, ssid)
    wifi_command += '&& sudo nmcli con mod {} wifi-sec.key-mgmt wpa-psk wifi-sec.psk \"{}\"'.format(network, psk)

    if static:
        ip = click.prompt('Qual o ip estático?')
        default_router_ip = ip.split('.')
        default_router_ip[3] = '1'
        default_router_ip = '.'.join(default_router_ip)

        gateway = click.prompt('Qual o ip do roteador/gateway da rede Wifi?', default=default_router_ip)

        wifi_command += '&& sudo nmcli con mod {} ipv4.addresses {}/32'.format(network, ip)
        wifi_command += '&& sudo nmcli con mod {} ipv4.gateway {}'.format(network, gateway)
        wifi_command += '&& sudo nmcli con mod {} ipv4.dns {},8.8.8.8'.format(network, gateway)
        wifi_command += '&& sudo nmcli con mod {} ipv4.method manual'.format(network)
    else:
        wifi_command += '&& sudo nmcli con mod {} ipv4.method auto'.format(network)

    client.sudo_run(wifi_command)

@wifi.command()
@click.argument('network')
@click.option("-s",'--static', is_flag=True, default=False)
@click.pass_obj
def edit(client, network, static):
    ssid = click.prompt('Digite o novo ssid da rede?')
    psk = click.prompt('Qual a nova senha da rede?')
    
    click.echo('Editando a rede {}: {}'.format(network, ssid))

    wifi_command = 'sudo nmcli con mod {} wifi-sec.key-mgmt wpa-psk 802-11-wireless.ssid \"{}\"'.format(network, ssid)
    wifi_command += '&& sudo nmcli con mod {} wifi-sec.key-mgmt wpa-psk wifi-sec.psk \"{}\"'.format(network, psk)

    if static:
        ip = click.prompt('Qual o ip estático?')
        default_router_ip = ip.split('.')
        default_router_ip[3] = '1'
        default_router_ip = '.'.join(default_router_ip)

        gateway = click.prompt('Qual o ip do roteador/gateway da rede Wifi?', default=default_router_ip)

        wifi_command += '&& sudo nmcli con mod {} ipv4.addresses {}/32'.format(network, ip)
        wifi_command += '&& sudo nmcli con mod {} ipv4.gateway {}'.format(network, gateway)
        wifi_command += '&& sudo nmcli con mod {} ipv4.dns {},8.8.8.8'.format(network, gateway)
        wifi_command += '&& sudo nmcli con mod {} ipv4.method manual'.format(network)
    else:
        #wifi_command += '&& sudo nmcli con mod {} -ipv4.addresses'.format(network)
        #wifi_command += '&& sudo nmcli con mod {} -ipv4.gateway'.format(network)
        #wifi_command += '&& sudo nmcli con mod {} -ipv4.dns'.format(network)
        wifi_command += '&& sudo nmcli con mod {} ipv4.method auto'.format(network)

    client.sudo_run(wifi_command)

@wifi.command()
@click.argument('network')
@click.pass_obj
def delete(client, network):
    wifi_command = 'nmcli con delete {}'.format(network)
    client.sudo_run(wifi_command)

@wifi.command()
@click.argument('network')
@click.pass_obj
def up(client, network):
    wifi_command = 'nmcli con up {}'.format(network)
    client.sudo_run(wifi_command)
