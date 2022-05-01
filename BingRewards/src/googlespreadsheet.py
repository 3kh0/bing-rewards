from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GoogleSpreadSheetReporting():
    def __init__(self, spreadsheet_id, sheet_name):
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name

    def add_row(self, current_time, user, points_earned_today, streak_count, days_till_bonus_count, available_points):
        # If modifying these scopes, delete the file token.json.
        #SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

        # The ID and name of a the spreadsheet.
        SPREADSHEET_ID = f'{self.spreadsheet_id}'
        SHEET_NAME = f'{self.sheet_name}'

        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        try:
            service = build('sheets', 'v4', credentials=creds)

            # Call the Sheets API
            sheet = service.spreadsheets()

            # append new row on empty row from Row 2 onwards
            range_notation = f"'{SHEET_NAME}'!A2"
            body = {
                'values': [
                    [f'{current_time}',f'{user}',f'{points_earned_today}',f'{streak_count}',f'{days_till_bonus_count}',f'{available_points}']
                ]
            }

            result = sheet.values().append(spreadsheetId=SPREADSHEET_ID,
                                        range=range_notation,
                                        body=body,
                                        valueInputOption="USER_ENTERED",
                                        insertDataOption="INSERT_ROWS").execute()
            print(f"newRows={result['updates']['updatedRows']}")
            return result

        except HttpError as err:
            print(err)