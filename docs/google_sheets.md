## Google Sheets API Instructions (Optional)
Before proceeding, please note:
- that the process is somewhat involved, it should take around 30 minutes to get everything set-up
- Each week, you will be forced to **manually** reauthenticate in order to generate a new token.

If you would still like to proceed, here are the steps:

1. Go to the `Google Sheets API` [page](https://console.cloud.google.com/apis/library/sheets.googleapis.com?authuser=2).
	- Click `Enable`. After a few moments, you will be taken to a project page
	- On the left hand side are some tabs, click `Credentials`.
	- Click `+ Create Credentials` -> `OAuth Client Id`
2. You will first need to configure consent screen, here
	-  Click `CONFIGURE CONSENT SCREEN`
		- Choose `External`
		- Fill out the required fields
	- Scopes screen: just click `Save and Continue`
	- Test users screen: 
		- add test user email, use the same email as your google account
		- click `Save and Continue`
3. Go back to `Credentials` tab 
	1. Click `+ Create Credentials` -> `OAuth Client Id`
	1. For `Application type` select `Web application`
	1. For `Name` make up a name.
	1. (Optional): Under section `Authorized redirect URIs`, click `Add URI`. Add the following 2 URI's: `https://localhost/` and `http://localhost/`
	1. Click `CREATE`
	1. A popup will say `OAuth client created` with your credentials, at the bottom click `DOWNLOAD JSON`
4. Update json filename and path
	- move the json file to this path: `bing-rewards-master/BingRewards/config`
	- rename the file to: `google_sheets_credentials.json`. 
	- For the two steps above, via cmd line, it would look something like this:
```sh
cd bing-rewards-master/BingRewards/config/
#move downloaded file to correct dir and rename file
mv ~/Downloads/client_secret_xxx.json ./google_sheets_credentials.json
```
5. Lastly, this program needs access to the `sheet_id` and `tab_name` 
	- Get the `sheet_id` by following these [instructions](https://stackoverflow.com/a/36062068).
	- The `tab_name` is simply the name of the tab, i.e `Sheet1`
	- Re-run setup.py to update the config file:
```py
python setup.py --google_sheets_sheet_id <your_sheet_id> --google_sheets_tab_name <your_tab_name>
```
6. To summarize, the end result of the above is the following:
	- In the `config/` directory, there is a `google_sheets_credentials.json` which was downloaded from google credentials page.
	- `config/config.json` was updated via `setup.py` and now contains the following:
		- sheet_id
		- tab_name
