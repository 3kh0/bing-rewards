from __future__ import print_function

import os.path
from datetime import datetime

from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

TOKEN_PATH = os.path.join("config/google_sheets_token.json")
CREDENTIALS_PATH = os.path.join("config/google_sheets_credentials.json")


class GoogleSheetsReporting:
    def __init__(self, sheet_id, tab_name):
        self.sheet_id = sheet_id
        self.tab_name = tab_name

    def add_row(self, stats, email):
        # If modifying these scopes, delete the file token.json.
        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        creds = None
        # token.json stores the user's access and refresh tokens
        # created when the authorization flow completes first time
        if os.path.exists(TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except RefreshError as e:
                    print(
                        f"{e}\nError thrown when trying to refresh expired"
                        " token. You will need to manually delete the token"
                        " file: `rm"
                        " BingRewards/config/google_sheets_token.json`"
                    )
                    return
            else:
                if os.path.exists(CREDENTIALS_PATH):
                    flow = InstalledAppFlow.from_client_secrets_file(
                        CREDENTIALS_PATH, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                else:
                    print(
                        "The Google Sheets credential file"
                        f" `{CREDENTIALS_PATH}` does not exist or is not in"
                        " the proper path. Cannot write to Google Sheets."
                        " Please refer to the README section `Google Sheets"
                        " API Instructions (Optional)` for further"
                        " instruction."
                    )
                    return
            # Save the credentials for the next run
            with open(TOKEN_PATH, "w") as token:
                token.write(creds.to_json())

        try:
            service = build("sheets", "v4", credentials=creds)

            # Call the Sheets API
            sheet = service.spreadsheets()

            # Write column names to first row
            col_names = [
                [
                    "run_time",
                    "email",
                    "earned_now",
                    "earned_today",
                    "streak_count",
                    "available_points",
                    "lifetime_points",
                ]
            ]

            sheet.values().update(
                spreadsheetId=str(self.sheet_id),
                range=f"'{self.tab_name}'!A1",
                valueInputOption="USER_ENTERED",
                body={"values": col_names},
            ).execute()

            # append new row on empty row from Row 2 onwards
            range_notation = f"'{self.tab_name}'!A2"
            body = {
                "values": [
                    [
                        f"{current_time}",
                        email,
                        stats.earned_now,
                        stats.earned_today,
                        stats.streak_count,
                        stats.available_points,
                        stats.lifetime_points,
                    ]
                ]
            }

            result = (
                sheet.values()
                .append(
                    spreadsheetId=str(self.sheet_id),
                    range=range_notation,
                    body=body,
                    valueInputOption="USER_ENTERED",
                    insertDataOption="INSERT_ROWS",
                )
                .execute()
            )
            if int(f"{result['updates']['updatedRows']}") >= 1:
                print("Row added to Google SpreadSheet succesfully")

            else:
                print(
                    "Boo! Row NOT added to Google SpreadSheet, response is:"
                    f" {result}"
                )
            return result

        except HttpError as err:
            print(err)
