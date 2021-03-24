import click
import paramiko
import warnings
import socket
import threading
from scp import SCPClient
from time import sleep
import re
import subprocess
from io import StringIO

from lib.forward import forward_tunnel

def client_factory(host, port = None, key=None, key_password=None, user=None, password=None, open_tunnel=None, tunnel_port=None):
    return LocalClient(host) if host == 'localhost' else SSHClient(host, port, key, key_password, user, password, open_tunnel, tunnel_port)
    
class LocalClient:
    props = {}

    def __init__(self, host):
        pass

    def sudo_run(self, command):
        subprocess.call(command, shell=True)


class SSHClient:
    def __init__(self, host, port, key, key_password, user, password, open_tunnel, tunnel_port):
        self.host = host
        self.port = port
        self.tunnel_port = tunnel_port if tunnel_port > 0 else (port - 42) + 5432
        self.user = user
        self._password = password

        self._sync_cron = '* */1 * * * cd /opt/fhserver && PYTHONPATH=app:lib:. APP_SETTINGS=config.DevelopmentConfig python3 app/fhsync.py > /dev/null 2>&1'
        self._wifi_cron = '*/1 * * * * /opt/scripts/check_wifi.sh > /dev/null 2>&1'
        self.crons = []

        if key is not None:
            key = paramiko.RSAKey.from_private_key(StringIO(key), password=key_password)

        warnings.filterwarnings(action='ignore',module='.*paramiko.*')

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, port=port, password=password, look_for_keys=False, pkey=key, timeout=120, banner_timeout=120, auth_timeout=120)

        scp = SCPClient(ssh.get_transport())
        
        self._ssh = ssh
        self._scp = scp

        self.put = scp.put
        self.putfo = scp.putfo

        if open_tunnel:
            click.echo('Abrindo tunnel ssh na porta {}'.format(tunnel_port))
            self.open_tunnel(self.tunnel_port)

        click.echo('Conectando ao UNIO Server em {}:{}\n'.format(host, port))

        click.echo("Lendo configurações do UNIO Server...")
        self.props = self.read_properties()
    
    def read_properties(self):
        stdout = self.run("cat /opt/fhserver/gunicorn.conf", v=False)
        
        for line in stdout:
            if line.startswith('MQTT_BROKER_URL'):
                mqtt_broker_url = re.search('.+ *= *"(.+)"', line).group(1)

        mqtt_broker_url = None if mqtt_broker_url == '{MQTT_BROKER_URL}' or mqtt_broker_url == 'None' else mqtt_broker_url

        return {
            'MQTT_BROKER_URL': mqtt_broker_url
        }

    def save_properties(self):
        self.run("sed -Ei '0,/(MQTT_BROKER_URL ?= ?)\"(.*)\"/s/(MQTT_BROKER_URL ?= ?)\"(.*)\"/\\1\"{}\"/' /opt/fhserver/gunicorn.conf".format(self.props['MQTT_BROKER_URL']))

    @property
    def sync_cron(self):
        return self._sync_cron

    @property
    def wifi_cron(self):
        return self._wifi_cron

    def sudo_run(self, command, v=True, timeout=120):
        return self.run(command, v=v, timeout=timeout, sudo=True)

    def run(self, command, v=True, sudo=False, timeout=120):
        timeout = timeout if timeout is not None else 10000 #Infinity?

        if sudo and 'sudo' not in command:
            command = "sudo -S -p '' {}".format(command)

        try:
            stdin, stdout, stderr = self._ssh.exec_command(command, timeout=timeout, get_pty=sudo)

            self.last_output = stdout

            
            #TODO wait for prompt instead of sleep
            if sudo:
                sleep(0.1)
                stdin.write(self._password + "\n")
                stdin.flush()

            if v:
                for line in stdout:
                    click.echo('... ' + line.strip('\n'))

            for line in stderr:
                click.secho('... [ERROR] ' + line.strip('\n'), fg='red')

        except socket.timeout:
            click.secho('... [ERROR] Session closed!', fg='red')
        except Exception as error:
            click.secho('... [ERROR] ' + str(error), fg='red')

        return stdout

    def extract(self):
        for line in self.last_output:
            return line

        return ''

    def check_count(self, count=0):
        return count == len(self.extract())

    def check(self, msg):
        return msg in self.extract()

    def add_cronjob(self, name, cron, recognition_pattern, append=True, enabled=False):
        job = None
        for _job in self.crons:
            if recognition_pattern in _job['cron']:
                job = _job

        if job is None:
            job = {}
            self.crons.append(job)

        job['name'] = name
        job['pattern'] = recognition_pattern
        job['cron'] = cron
        job['enabled'] = enabled

        self.write_crontab()

    def write_crontab(self):
        crontab = 'SHELL=/bin/bash\nPATH=/bin:/usr/bin:/usr/local/bin\n\n'

        for job in self.crons:
            click.echo('Adicionando cron job: {}'.format(job['name']))
            crontab += '{}{}\n'.format('#' if not job['enabled'] else '', job['cron'])
            
        #TODO better way to set crontab
        self.run("echo '{}' > /tmp/uniocron".format(crontab), sudo=True)
        self.run('crontab -u root /tmp/uniocron -', sudo=True)
        self.run('rm /tmp/uniocron', sudo=True)

    def restart_app(self, reread=False):
        self.run("supervisorctl stop fhserver")
    
        if reread:
            self.run("supervisorctl reread fhserver")
            self.run("supervisorctl update fhserver")
        else:
            self.run("supervisorctl start fhserver")

    def get_network(self, name):
        ssid = None
        static_ip = None
        static_gateway = None
        priority = None

        stdout = self.run('nmcli con show {}'.format(name), v=False)
        for line in stdout:
            if line.startswith('802-11-wireless.ssid'):
                ssid = line.split(':')[1].strip()
            if line.startswith('ipv4.addresses'):
                static_ip = line.split(':')[1].strip().replace('/32', '')
                static_ip = static_ip.strip() if len(static_ip.strip()) > 0 else None
            if line.startswith('ipv4.gateway'):
                static_gateway = line.split(':')[1].strip()
                static_gateway = static_gateway if static_gateway != '--' else None
            if line.startswith('connection.autoconnect-priority'):
                priority = line.split(':')[1].strip()

        return {
            ssid: ssid,
            static_ip: static_ip,
            static_gateway: static_gateway,
            priority: priority
        }

    def update_hostname(self, primary=False):
        click.echo("Verificando hostname do SO")
        self.run("hostname", v=False)
        old_hostname = self.extract().strip()
        click.echo("Hostname atual: {}".format(old_hostname))

        self.run("cat /proc/cpuinfo | grep Serial | sed -E 's/Serial.*:.*0*(........+)/\\1/'", v=False)
        serial = self.extract().strip()
        click.echo("Serial: {}".format(serial))

        if primary:
            hostname = 'unio-hass-{}'.format(serial)
        else:
            hostname = 'unio-{}'.format(serial)

        if old_hostname == hostname:
            click.echo("Hostname sem alterações: {}".format(hostname))
            return

        click.echo("Atualizando hostname: {}".format(hostname))
        self.sudo_run("sh -c 'echo \"{}\" > /etc/hostname' > /dev/null 2>&1".format(hostname))
        self.sudo_run("hostname {}".format(hostname))
        self.sudo_run("sed -Ei 's/(.*)({})/\\1{}/' /etc/hosts".format(old_hostname, hostname))

    def read_hostname(self):
        click.echo("Lendo hostname do SO")
        self.run("hostname", v=False)
        hostname = self.extract().strip()
        click.echo(hostname)

    def open_tunnel(self, port):
        click.echo('Abrindo tunel SSH na porta {}'.format(port))
        def _runner():
            try:
                forward_tunnel(port, 'localhost', 5432, self._ssh.get_transport())
            except KeyboardInterrupt:
                pass

        db_forward_thread = threading.Thread(target=_runner)
        db_forward_thread.daemon = True
        db_forward_thread.start()

    def close(self):
        self._ssh.close()
        self._scp.close()