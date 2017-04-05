import boto3
import functools
import json
import logging
import os
import paramiko

logger = logging.getLogger('flask_ask')

class CasaSSHContext(object):
    LOCAL_SERVER_ROUTE = 'http://localhost'
    SERVICE_ROUTE = 'CasaTunes/CasaService.svc'
    CASA_HEADERS = {'Content-Type': 'application/json'}

    def __enter__(self):
        s3_client = boto3.client('s3')
        s3_client.download_file('alexa-casatunes', 'keys/casa_rsa', '/tmp/casa_rsa')

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=os.getenv('CASA_SERVER_IP'),
            username='casa',
            password=os.getenv('CASA_SSH_PASSWORD'),
            key_filename='/tmp/casa_rsa',
            port=22222,
        )
        self.client = client
        return client

    def __exit__(self, typ, val, traceback):
        self.client.close()

    def __call__(self, f):
        @functools.wraps(f)
        def decorated(*args, **kwargs):
            with self:
                return f(ssh=self, *args, **kwargs)
        return decorated

    @staticmethod
    def casa_route(endpoint):
        return '/'.join((
            CasaSSHContext.LOCAL_SERVER_ROUTE, CasaSSHContext.SERVICE_ROUTE, endpoint
        ))

    def casa_command(self, endpoint, data=None):

        data = data if data else {'ZoneID': 0}

        headers = ' '.join(['-H "{}: {}"'.format(k, v) for k, v in self.CASA_HEADERS.items()])
        command = 'curl -X POST {headers} -d \'{data}\' {route}'.format(
            headers=headers,
            data=json.dumps(data),
            route=self.casa_route(endpoint),
        )
        _, stdout, stderr = self.client.exec_command(command)
        response_data = json.loads(stdout.read())

        logger.debug(json.dumps(response_data))
        return response_data
