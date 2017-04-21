import boto3
import json
import logging
import os
import paramiko

logger = logging.getLogger('flask_ask')

class CasaSSHService(object):
    LOCAL_SERVER_ROUTE = 'http://localhost'
    SERVICE_ROUTE = 'CasaTunes/CasaService.svc'
    CASA_HEADERS = {'Content-Type': 'application/json'}

    def start(self):
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
        return self

    def close(self):
        self.client.close()

    def __enter__(self):
        return self.start()

    def __exit__(self, typ, val, traceback):
        self.close()

    @staticmethod
    def casa_route(endpoint):
        return '/'.join((
            CasaSSHService.LOCAL_SERVER_ROUTE, CasaSSHService.SERVICE_ROUTE, endpoint
        ))

    def casa_command(self, endpoint, data=None):

        data = data if data else {'ZoneID': 0}
        if 'ZoneId' in data.keys():
            data['ZoneId'] = str(data['ZoneId'])

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
