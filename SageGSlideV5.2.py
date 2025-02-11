import os
import time
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from PIL import Image, ImageDraw, ImageFont, ImageTk
import requests
from io import BytesIO
import tkinter as tk
from tkinter import messagebox

# Constants
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']
ALBUMS_PER_PAGE = 10
SLIDESHOW_INTERVAL = 30  # seconds
FONT_SIZE = 24
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
MAX_RETRIES = 3  # Max retries for fetching an image

# Debug output function
def debug_print(message):
    print(f"[DEBUG] {message}")

# Authenticate and get Google Photos API service
def authenticate_google_photos():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('YOUR CREDENTIAL JSON FILE HERE', SCOPES)  # put your Credential JSON file here!
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('photoslibrary', 'v1', credentials=creds, static_discovery=False)

# Fetch list of albums
def fetch_albums(service):
    albums = []
    next_page_token = None
    while True:
        results = service.albums().list(pageSize=ALBUMS_PER_PAGE, pageToken=next_page_token).execute()
        albums.extend(results.get('albums', []))
        next_page_token = results.get('nextPageToken')
        if not next_page_token:
            break
    return albums

# Fetch photos from a specific album
def fetch_photos(service, album_id):
    photos = []
    next_page_token = None
    while True:
        results = service.mediaItems().search(body={"albumId": album_id, "pageSize": 100, "pageToken": next_page_token}).execute()
        photos.extend(results.get('mediaItems', []))
        next_page_token = results.get('nextPageToken')
        if not next_page_token:
            break
    return photos

# Fetch a fresh baseUrl using mediaItem.id
def fetch_fresh_baseurl(service, media_item_id):
    debug_print(f"Fetching fresh baseUrl for mediaItem ID: {media_item_id}")
    media_item = service.mediaItems().get(mediaItemId=media_item_id).execute()
    return media_item.get('baseUrl')

# Display photos in a slideshow
def slideshow(service, photos, album_name):
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.configure(background='black')
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    label = tk.Label(root)
    label.pack()

    current_photo_index = 0

    def update_image():
        nonlocal current_photo_index
        photo = photos[current_photo_index]
        media_item_id = photo['id']
        base_url = photo.get('baseUrl')

        # If baseUrl is not available or expired, fetch a fresh one
        if not base_url:
            base_url = fetch_fresh_baseurl(service, media_item_id)
            photos[current_photo_index]['baseUrl'] = base_url  # Update the photo object with the new baseUrl

        base_url += '=w' + str(screen_width) + '-h' + str(screen_height)
        debug_print(f"Fetching image from URL: {base_url}")

        # Retry logic for fetching the image
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(base_url)
                if response.status_code == 403:  # baseUrl expired
                    debug_print("baseUrl expired. Fetching a fresh one...")
                    base_url = fetch_fresh_baseurl(service, media_item_id) + '=w' + str(screen_width) + '-h' + str(screen_height)
                    photos[current_photo_index]['baseUrl'] = base_url  # Update the photo object with the new baseUrl
                    response = requests.get(base_url)
                response.raise_for_status()  # Raise an error for bad status codes
                img = Image.open(BytesIO(response.content))
                break  # Exit the retry loop if successful
            except (requests.exceptions.RequestException, IOError) as e:
                debug_print(f"Attempt {attempt + 1} failed: {e}")
                if attempt == MAX_RETRIES - 1:
                    debug_print("Max retries reached. Skipping this image.")
                    current_photo_index = (current_photo_index + 1) % len(photos)
                    root.after(SLIDESHOW_INTERVAL * 1000, update_image)
                    return
                time.sleep(2)  # Wait before retrying

        # Maintain aspect ratio
        img_ratio = img.width / img.height
        screen_ratio = screen_width / screen_height
        if img_ratio > screen_ratio:
            new_width = screen_width
            new_height = int(screen_width / img_ratio)
        else:
            new_height = screen_height
            new_width = int(screen_height * img_ratio)

        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        background = Image.new('RGB', (screen_width, screen_height), BLACK)
        background.paste(img, ((screen_width - new_width) // 2, (screen_height - new_height) // 2))

        # Add text (current time and album name)
        draw = ImageDraw.Draw(background)
        try:
            font = ImageFont.truetype("arial.ttf", FONT_SIZE)
        except IOError:
            font = ImageFont.load_default()
        current_time = datetime.datetime.now().strftime('%H:%M:%S')
        draw.text((10, screen_height - 40), album_name, font=font, fill=WHITE)
        draw.text((screen_width - 150, screen_height - 40), current_time, font=font, fill=WHITE)

        # Convert to Tkinter format
        img_tk = ImageTk.PhotoImage(background)
        label.config(image=img_tk)
        label.image = img_tk

        current_photo_index = (current_photo_index + 1) % len(photos)
        root.after(SLIDESHOW_INTERVAL * 1000, update_image)

    def on_click(event):
        if messagebox.askyesno("Exit", "Do you want to exit the slideshow?"):
            root.destroy()

    def on_key(event):
        if event.keysym == 'Escape':
            if messagebox.askyesno("Exit", "Do you want to exit the slideshow?"):
                root.destroy()

    root.bind('<Button-1>', on_click)
    root.bind('<Escape>', on_key)

    update_image()
    root.mainloop()

# Main function
def main():
    debug_print("Authenticating with Google Photos API...")
    service = authenticate_google_photos()

    debug_print("Fetching albums...")
    albums = fetch_albums(service)
    for i, album in enumerate(albums):
        print(f"{i + 1}. {album['title']}")

    album_index = int(input("Enter the number of the album you want to view: ")) - 1
    selected_album = albums[album_index]
    debug_print(f"Selected album: {selected_album['title']}")

    debug_print("Fetching photos from the selected album...")
    photos = fetch_photos(service, selected_album['id'])
    debug_print(f"Found {len(photos)} photos in the album.")

    debug_print("Starting slideshow...")
    slideshow(service, photos, selected_album['title'])

if __name__ == '__main__':
    main()
