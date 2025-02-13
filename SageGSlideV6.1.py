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
from tkinter import messagebox, Listbox, Button, Label

# Constants
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']
SLIDESHOW_INTERVAL = 30  # seconds
FONT_SIZE = 24  # Font size for the album name
LARGE_FONT_SIZE = 40  # Larger font size for the date and time
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
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('photoslibrary', 'v1', credentials=creds, static_discovery=False)

# Fetch list of albums
def fetch_albums(service):
    albums = []
    next_page_token = None
    while True:
        results = service.albums().list(pageSize=50, pageToken=next_page_token).execute()
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

        # Add text (current time, date, and album name)
        draw = ImageDraw.Draw(background)
        try:
            font = ImageFont.truetype("arial.ttf", FONT_SIZE)  # Font for album name
            large_font = ImageFont.truetype("arial.ttf", LARGE_FONT_SIZE)  # Font for date and time
        except IOError:
            font = ImageFont.load_default()  # Fallback font
            large_font = ImageFont.load_default()  # Fallback font

        current_time = datetime.datetime.now().strftime('%H:%M:%S')
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')

        # Draw album name (unchanged font size)
        draw.text((12, screen_height - 40), album_name, font=font, fill=WHITE)

        # Calculate the width of the date and time text
        date_time_text = f"{current_date} {current_time}"
        text_width = draw.textlength(date_time_text, font=large_font)

        # Position the date and time text dynamically to avoid cutoff
        text_x = screen_width - text_width - 20  # 20 pixels padding from the right edge
        text_y = screen_height - 60  # Same vertical position as before

        # Draw date and time with larger font size
        draw.text((text_x, text_y), date_time_text, font=large_font, fill=WHITE)

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

# GUI for selecting an album
def select_album_gui(service):
    def on_select():
        selected_index = album_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("No Selection", "Please select an album.")
            return
        selected_album = albums[selected_index[0]]
        debug_print(f"Selected album: {selected_album['title']}")
        root.destroy()
        start_slideshow(service, selected_album)

    # Fetch albums
    debug_print("Fetching albums...")
    albums = fetch_albums(service)

    # Create GUI
    root = tk.Tk()
    root.title("Select an Album")
    root.geometry("400x800")

    Label(root, text="Select an album:").pack(pady=10)
    album_listbox = Listbox(root, selectmode=tk.SINGLE)
    for album in albums:
        album_listbox.insert(tk.END, album['title'])
    album_listbox.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

    Button(root, text="Select", command=on_select).pack(pady=10)

    root.mainloop()

# Start the slideshow
def start_slideshow(service, selected_album):
    debug_print("Fetching photos from the selected album...")
    photos = fetch_photos(service, selected_album['id'])
    debug_print(f"Found {len(photos)} photos in the album.")

    debug_print("Starting slideshow...")
    slideshow(service, photos, selected_album['title'])

# Main function
def main():
    debug_print("Authenticating with Google Photos API...")
    service = authenticate_google_photos()

    # Launch the album selection GUI
    select_album_gui(service)

if __name__ == '__main__':
    main()