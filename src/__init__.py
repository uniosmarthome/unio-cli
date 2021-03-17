import click
import sys
import re
import getpass

from .client import client_factory

__VERSION__ = '0.1.0'

stock_opts = {
    'user': 'st2',
    'key': './unio.key',
    'key_password': '7j3SgDuuZmuJt2fp',
    'user_password': '7j3SgDuuZmuJt2fp'
}

stdout = None

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
    if ctx.invoked_subcommand is None:
        if version:
            click.echo("UNIO Utils v{}".format(__VERSION__))
        elif ctx.invoked_subcommand is None:
            click.echo("Use --help para listar todos os comandos disponíveis")
        
        sys.exit()

    if use_stock_options:
        user = stock_opts['user']
        key = stock_opts['key']
        key_password = stock_opts['key_password']
        password = stock_opts['user_password']

    if password is None:
        try: 
            password = getpass.getpass() 
        except Exception as error: 
            print('ERROR', error)

    open_tunnel = tunnel > 0

    ctx.obj = client_factory(host, port, key, key_password, user, password, open_tunnel, tunnel)

def linesplit(socket):
    buffer_string = socket.recv(4048)
    done = False
    while not done:
        if b'\n' in buffer_string:
            (line, buffer_string) = buffer_string.split(b"\n", 1)
            yield line
        else:
            more = socket.recv(4048)
            if not more:
                done = True
            else:
                buffer_string = buffer_string + more
    if buffer_string:
        yield buffer_string