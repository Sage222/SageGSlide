A python script that returns all Albums from your Google Photos via API. 

Select the Album you wish to view as a Slideshow. (Can take about 20 seconds to return results pending on how many Albums you have).

Slideshow is then displayed fullscreen, black border with current time on Bottom Right and Album name on buttom left.

Needs you to setup Google Photos API access for your account. (Not hard).

Exit slideshow mouseclick/screen tap. (For touchscreen devices).

Photos are stored in Memory only and removed at the end of the Slideshow.


Prerequistes & Instructions

Install Python 3.13.2 (Installed on Windows)
https://www.python.org/downloads/windows/


You can enable the Google Photos Library API by following these steps:

Step 1: Go to Google Cloud Console
Open the Google Cloud Console:
👉 https://console.cloud.google.com/

Sign in with your Google account.

Step 2: Create a New Project (If You Don’t Have One)
Click on the "Select a project" dropdown (top-left).
Click "New Project".
Enter a Project Name (e.g., Google Photos Slideshow).
Click "Create" and wait a few seconds.


Step 3: Enable Google Photos API
In the left sidebar, go to "APIs & Services" > "Library".
In the search bar, type:
Google Photos Library API
Click on Google Photos Library API from the search results.
Click the "Enable" button.


Step 4: Create API Credentials
Go to "APIs & Services" > "Credentials".
Click "Create Credentials" (top).
Select OAuth Client ID.
If it asks you to configure a consent screen:
Click "Configure Consent Screen".
Select "External", then click "Create".
Fill in basic app details (App Name, Email).
Click "Save and Continue" (you can skip scopes for now).
Click "Back to Dashboard".
Now, create OAuth credentials:
Choose Application Type:
Desktop App (for a Python script)
Web Application (for a web app)
Enter a name (e.g., Google Photos Slideshow).
Click "Create".
Download the credentials.json file.


Step 5: Use the Credentials
For Python, save the credentials.json file in the same folder as the SageGSlide.py python script.


Step 6: Authorize Access to Google Photos:
You need to request scopes to the ReadOnly GooglePhotos API.  https://console.cloud.google.com/
(www.googleapis.com/auth/photoslibrary.readonly)
This allows your app to read photos from your Google Photos library.

Step 7: Add your Google Account as a Test User
(Google only allows test users to access unverified apps.)

Go to Google Cloud Console → https://console.cloud.google.com/
Open your project.
In the left menu, go to APIs & Services > OAuth consent screen.
Scroll to Test Users section.
Click Add Users → Enter your Google email.
Click Save & Continue.

Install PIP on your PC.
Run 'cmd' as admin on your PC.
ensure python is working properly by running 
"Python --version"
Run "python -m pip install --upgrade pip"

Download the Google Photos APIs
pip install --upgrade google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

Install Pillow
Run "python -m pip install pillow"

Installer Tkinter
Run "python -m pip install tk"

Modify SageGSlide.py with your CLIENT SECRET JSON file and any other config changes you like and save.

Run "python SageGSlide.py".  It will launch a browser for your to authenticate. (This should only happen once as it will then save a local token to the same path as the py file.).

Enjoy!


Changelog 1.01 8/2/2025
Added a Confirmation on Exit.

Changelog 1.02 9/2/2025
Added some error handling to prevent images stalling.

Changelog 1.03 9/2/2025
Added some QOL messaging.

Changelog 5.2 11/2/2025
Complete re-write with Debug outputs, retries on failures and using Method: mediaItems.batchGet to avoid Google auth issues.

Changelog 6.1 13/2/2025
Moved to GUI interface for Album Selection. Minor tweaks.

Changelog 8.1 15/2/2025
Added Randomisation of photos, minimise option or exit optiopn, GUI album choice and load 50 photos at a time (and obtain the next batch in the background to avoid long load times for large albums)

Changelog 11 27/2/2025
Added multiple album selection and current and max weather temps.



