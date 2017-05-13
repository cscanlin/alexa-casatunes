# alexa-casatunes

Control CasaTunes with Alexa

### Available Commands

 - Play / Pause
 - Previous / Next Song
 - Turn Room On / Off
 - Set Volume in Room
 - Increase / Decrease Volume in Room
 - Now Playing Info
 - Search for Track / Artist / Album / Playlist

#### Planned Commands (With Conversational Support)

 - Wake Alarms / Sleep Timers
 - Better Search (source selection + conversational)
 - Playlist / Queue Management

### Deploying

In order to start you must have a CasaTunes server (obviously), and it must have Windows 10 installed on it.

This project is still in the early stages, and the deployment process is still very manual / unpolished for new users. If you get stuck or have any feedback, please open an issue!

Also, I'm working on building this out so it can be properly deployed as a real Alexa skill that can be installed by any user. [If you're interested in contributing, please leave a comment here!](https://github.com/cscanlin/alexa-casatunes/issues/1)

#### CasaTunes Server Setup

1. Install Bash on Windows by following the instructions here: https://msdn.microsoft.com/en-us/commandline/wsl/install_guide

2. Setup SSH on your CasaTunes server, following the instructions here:
https://superuser.com/a/1114162/401859

    - Note that you should not use the default port (22), use a different unused port instead (22222 recommended). Record which port you use, as it will be need later

    - You will also create a password at some point in the setup. Remember this as well.

3. Forward the port above through your router.

4. Create an ssh key called `casa_rsa` and add the public key to the server in the authorized_keys file (usually found in `C:\Users\<user>\.ssh\`)

5. Upload the `casa_rsa` private key to a directory called `keys` in your s3 bucket.

#### Alexa / Lambda Setup

1. Fork / clone this repository

2. Run `mapping_generator.py MY_LOCAL_CASA_IP`, using your local CasaTunes IP address

3. Change the `s3_bucket` name in `zappa_settings.json` to one you control.

4. Install [Docker](https://www.docker.com/) if not already installed

5. Build the docker image:

    ```docker build -t zappa .```

6. Deploy to AWS Lambda using Zappa

    ```sh deploy_zappa.sh -d  # you only need the `-d` flag for initial deploy```

    - This will take a few minutes to run; record the url generated after it finishes

7. Go to https://developer.amazon.com/alexa-skills-kit and create a new Alexa skill

8. Update configuration to use https, with the path generated in the command line from step 6

9. In the interaction model builder, navigate to code editor (top of the left side menu) and paste everything from `interaction_model.json`

10. Set environment variables on Lambda in the "Code" tab (and locally if desired) for the following:

    - `ALEXA_USER_ID` - can be found in the "Test" portion of the Alexa skill dashboard using the service simulator. Multiple user ids can be added, separated by a semicolon
    - `CASA_SERVER_IP` - Your public IP address, can be found by googling "what is my ip"
    - `CASA_SERVER_PORT` - From earlier ssh setup (22222 recommended)
    - `CASA_S3_BUCKET_NAME` - Your s3 bucket (likely same as in `zappa_settings.json`)
    - `CASA_SSH_PASSWORD` - From earlier ssh setup
