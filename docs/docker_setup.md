## Docker Container Set-up (Optional)

Docker makes it easy for you to run any program, including this one, regardless of your environment. You just need to [install docker](https://docs.docker.com/get-docker/) on your machine. 

Please note that not all features are supported using Docker, i.e Telegram.

Once docker is installed, follow these instructions to set-up the BingRewards container:

1. In terminal, run `docker pull killerherts/bing-rewards:latest`
2. Set-up the config with either option 1 or 2 
	 1. Option 1, run setup.py within the container: `docker run -t -d --name bing-rewards killerherts/bing-rewards:latest python setup.py -e <your_email> -p <password>`  You must include your password as there will be no user prompt with -t -d flags.
	 2. Option 2: Pass your config directly into the container: `docker run -t -d -v <absolute-path-to-config-directory>:/bing-rewards/BingRewards/config --name bing-rewards killerherts/bing-rewards:latest`. Note, this option assumes you have a set-up a local copy of this project on your machine.
3. To run BingRewards, you have a variety of options:
	1. Wait for the scheduled cron job to run (every 8 hours)
	2. Execute the python script manually: `docker exec bing-rewards python BingRewards.py -nsb`
3. If for any reason you want to enter the container then run: `docker exec -it bing-rewards /bin/bash`

#### Container Notes: 
1. You may override default environment variables, by adding the following flags in the `docker run` command:
	1. Set a preferred bot run schedule with 
	`-e SCH=<cronexpression>` Default : `0 */8 * * *`
	2. Set a preferred timezone with 
	`-e TZ=<timezone>` Default: `America/New_York`
	3. Set a preferred update schedule with 
	`-e UPDATE=<cronexpression>` Default : `0 0 /1 * *`
4. Logs can be mounted to host file system by using the following with docker run
 `-v <absolute-path-to-logs-directory>:/bing-rewards/BingRewards/logs`
5. Images will be rebuilt daily at 12:26 PM UTC this will update chromium and other image dependencies. If your having issues with the container update it with the following [instructions](https://stackoverflow.com/a/26833005)
6. If you would like to use docker compose a sample configuration can be found [here](https://github.com/jjjchens235/bing-rewards/blob/master/compose.yaml)

