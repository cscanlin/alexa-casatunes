### alexa-casatunes

Control CasaTunes with Alexa

### virtualenv

    /usr/local/bin/python /Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/virtualenv.py -p /usr/local/bin/python alexa-casa

    source alexa-casa/bin/activate

    pip install -r requirements.txt

### Deploying

    docker build -t zappa .

    sh deploy_zappa.sh
