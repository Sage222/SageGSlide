import os
import tkinter as tk
import requests
from PIL import Image, ImageTk
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import io
import time

# 🔹 Google API Setup
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']
CREDENTIALS_FILE = 'REPLACE WITH YOUR JSON FILE'  # Your Google API credentials.json file
TOKEN_FILE = 'token.json'  # Your token.json file

# 🔹 Function to Authenticate & Save Token
def authenticate():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return creds

# Authenticate once & save the session
creds = authenticate()
service = build('photoslibrary', 'v1', credentials=creds, static_discovery=False)

# 🔹 Function to Fetch All Albums (Display Only Names)
def list_all_albums():
    albums = []
    next_page_token = None
    while True:
        results = service.albums().list(pageSize=50, pageToken=next_page_token).execute()
        albums.extend(results.get('albums', []))
        next_page_token = results.get('nextPageToken')
        if not next_page_token:
            break  
    
    if not albums:
        print("No albums found.")
        exit()
    
    print("\n📸 **Your Albums:**")
    for i, album in enumerate(albums):
        print(f"[{i+1}] {album['title']}")  # Display only album names
    
    return albums

# 🔹 Function to Fetch Photos from a Specific Album
def get_album_photos(album_id):
    photos = []
    next_page_token = None
    while True:
        results = service.mediaItems().search(
            body={"albumId": album_id, "pageSize": 50, "pageToken": next_page_token}
        ).execute()
        photos.extend([item['baseUrl'] for item in results.get('mediaItems', [])])
        next_page_token = results.get('nextPageToken')
        if not next_page_token:
            break
    return photos

# 🔹 List All Albums & Ask User to Select One
albums = list_all_albums()
while True:
    try:
        album_choice = int(input("\nEnter the number of the album to play as a slideshow: ").strip()) - 1
        if 0 <= album_choice < len(albums):
            album_id = albums[album_choice]['id']
            album_name = albums[album_choice]['title']
            break
        else:
            print("❌ Invalid number! Please enter a valid album number.")
    except ValueError:
        print("❌ Please enter a valid number.")

photos = get_album_photos(album_id)

if not photos:
    print("No photos found in this album.")
    exit()

# 🔹 Tkinter Fullscreen Slideshow Setup
root = tk.Tk()
root.title("Google Photos Fullscreen Slideshow")

# Make the window fullscreen
root.attributes("-fullscreen", True)
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# 🔹 Exit on Keyboard or Touchscreen Tap
root.bind("<Escape>", lambda event: root.destroy())  # Press "Esc" to exit
root.bind("<space>", lambda event: root.destroy())  # Press "Spacebar" to exit
root.bind("<Button-1>", lambda event: root.destroy())  # Tap anywhere on the screen to exit

# Create labels for the slideshow and time display
label = tk.Label(root, bg="black")  # Black background
label.pack(expand=True, fill="both")

# Date & Time Label (Bottom-right corner)
time_label = tk.Label(root, fg="white", bg="black", font=("Arial", 50), anchor="se")  # Adjust size if you like
time_label.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)  # Offset from bottom-right corner

# Album Name Label (Bottom-left corner)
album_label = tk.Label(root, fg="white", bg="black", font=("Arial", 18), anchor="sw")  # Adjust size if you like
album_label.place(relx=0.0, rely=1.0, anchor="sw", x=20, y=-20)  # Offset from bottom-left corner

# 🔹 Function to Update Date & Time in DD-MMM-YY HH:MM:SS Format
def update_time():
    current_time = time.strftime("%d-%b-%y %H:%M:%S")  # Adjust format: DD-MMM-YY HH:MM:SS
    time_label.config(text=current_time)
    root.after(1000, update_time)  # Update every second

# 🔹 Function to Display Images Without Cropping or Stretching
def update_image(index=0):
    img_url = photos[index] + "=d"  # Get full-resolution image
    response = requests.get(img_url)
    img_data = response.content

    img = Image.open(io.BytesIO(img_data))

    # Resize to fit screen while maintaining aspect ratio
    img_width, img_height = img.size
    scale_factor = min(screen_width / img_width, screen_height / img_height)
    new_width = int(img_width * scale_factor)
    new_height = int(img_height * scale_factor)

    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Create a blank black image and paste the resized image onto it (black borders effect)
    final_image = Image.new("RGB", (screen_width, screen_height), "black")
    x_offset = (screen_width - new_width) // 2
    y_offset = (screen_height - new_height) // 2
    final_image.paste(img, (x_offset, y_offset))

    img_tk = ImageTk.PhotoImage(final_image)

    label.config(image=img_tk)
    label.image = img_tk

    root.after(30000, update_image, (index + 1) % len(photos))  # Change every 30 sec

# Display the album name in the bottom-left corner
album_label.config(text=album_name)

# Start time updates and slideshow
update_time()
update_image()
root.mainloop()
