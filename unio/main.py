import click
import sys
import getpass
from pkg_resources import resource_string

from .client import client_factory
from . import __version__, stock_opts

@click.group(invoke_without_command=True)
@click.option('-v', '--version', is_flag=True, default=False, help='mostra a versão do utilitário')
@click.option('-h', '--host', help='o endereço do unio-server', default='localhost')
@click.option('-p', '--port', default=42, help='a porta SSH do unio-server')
@click.option('-k', '--key', help='a chave privada para acesso SSH')
@click.option('-kp', '--key-password', help='a senha de acesso à chave privada')
@click.option('-u', '--user', help='usuário para acesso SSH')
@click.option('-up', '--password', default=None, help='senha do usuário')
@click.option('-s', '--use-stock-options', is_flag=True, default=True, help='configurações padrão para conexaão a um dispositivo com configurações padrão')
@click.option('-t', '--tunnel', default=0, help='porta para tunel ssh')
@click.pass_context
def main(ctx, version, host, port, key, key_password, user, password, use_stock_options, tunnel):
    click.echo("Bem-vindo ao aplicativo de Instalação & Suporte UNIO Smart Home!\n\n")

    welcome = resource_string('resources', 'ascii_logo1.txt')
    click.echo(welcome)            

    if ctx.invoked_subcommand is None:
        if version:
            click.echo("UNIO Utils v{}".format(__version__))
        elif ctx.invoked_subcommand is None:
            click.echo("Use --help para listar todos os comandos disponíveis")
        
        sys.exit()

    if use_stock_options:
        user = stock_opts['user']
        key = resource_string('resources', 'unio.key').decode('utf-8')
        key_password = stock_opts['key_password']
        password = stock_opts['user_password']

    if password is None:
        try: 
            password = getpass.getpass() 
        except Exception as error:
            print('ERROR', error)

    open_tunnel = tunnel > 0

    ctx.obj = client_factory(host, port, key, key_password, user, password, open_tunnel, tunnel)
