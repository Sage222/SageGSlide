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
CREDENTIALS_FILE = 'YOUR JSON FILE'  # Your credentials.json file
TOKEN_FILE = 'token.json'  # Your token.json file

print("Welcome to SageGSlide. Please wait a moment while we obtain the list of your albums from Google.")
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
        album_choice = int(input("\nEnter the number of the album to play as a slideshow, press enter and wait a moment: ").strip()) - 1
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

# 🔹 Create labels for the slideshow and time display
label = tk.Label(root, bg="black")  # Black background
label.pack(expand=True, fill="both")

# Date & Time Label (Bottom-right corner)
time_label = tk.Label(root, fg="white", bg="black", font=("Arial", 40), anchor="se")
time_label.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)  # Offset from bottom-right corner

# Album Name Label (Bottom-left corner)
album_label = tk.Label(root, fg="white", bg="black", font=("Arial", 18), anchor="sw")
album_label.place(relx=0.0, rely=1.0, anchor="sw", x=20, y=-20)  # Offset from bottom-left corner

# 🔹 Function to Update Date & Time in DD-MMM-YY HH:MM:SS Format
def update_time():
    current_time = time.strftime("%d-%b-%y %H:%M:%S")  # Format: DD-MMM-YY HH:MM:SS
    time_label.config(text=current_time)
    root.after(1000, update_time)  # Update every second

# 🔹 Function to Display Images Without Cropping or Stretching
def update_image(index=0, retry_attempts=0):
    try:
        img_url = photos[index] + "=d"  # Get full-resolution image
        response = requests.get(img_url, timeout=10)  # Timeout after 10 seconds
        response.raise_for_status()  # Raise an error for bad responses

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

        # Prevent garbage collection by keeping a reference
        label.config(image=img_tk)
        label.image = img_tk

        # 🔹 Schedule the next image (with safety check)
        root.after_cancel(update_image)  # Cancel any previous scheduled updates
        root.after(30000, update_image, (index + 1) % len(photos))  # Change every 30 sec

    except requests.RequestException as e:
        print(f"⚠️ Network Error: {e}. Retrying in 5 seconds...")

        if retry_attempts < 3:  # Retry up to 3 times
            root.after(5000, update_image, index, retry_attempts + 1)
        else:
            print("❌ Failed to load image after multiple attempts. Skipping...")
            root.after(30000, update_image, (index + 1) % len(photos))  # Skip to next image


# Display the album name in the bottom-left corner
album_label.config(text=album_name)

# 🔹 Function to Confirm Exit with Yes/No Buttons
def confirm_exit():
    # Create a new window for confirmation
    confirmation_window = tk.Toplevel(root)
    confirmation_window.title("Exit Confirmation")
    
    # Adjust geometry to move the window to a more centered position
    confirmation_window.geometry("300x150+{}+{}".format(int(screen_width / 2 - 150), int(screen_height / 2 - 75)))  # Centered in the screen
    
    confirmation_window.configure(bg="black")

    # Label for the confirmation message
    message_label = tk.Label(confirmation_window, text="Are you sure you want to exit?", fg="white", bg="black", font=("Arial", 18))
    message_label.pack(expand=True)

    # Function to close the app
    def exit_app():
        confirmation_window.destroy()  # Close the confirmation window
        root.quit()  # Exit the main application

    # Create a button to confirm exit
    confirm_button = tk.Button(confirmation_window, text="Yes", command=exit_app, font=("Arial", 18))
    confirm_button.pack(side="left", padx=20, pady=20)

    # Button to cancel exit
    cancel_button = tk.Button(confirmation_window, text="No", command=confirmation_window.destroy, font=("Arial", 18))
    cancel_button.pack(side="right", padx=20, pady=20)

    confirmation_window.transient(root)
    confirmation_window.grab_set()  # Keep focus on this window
    confirmation_window.wait_window()

# 🔹 Exit on Keyboard or Touchscreen Tap with Confirmation
root.bind("<Escape>", lambda event: confirm_exit())  # Press "Esc" to confirm exit
root.bind("<space>", lambda event: confirm_exit())  # Press "Spacebar" to confirm exit
root.bind("<Button-1>", lambda event: confirm_exit())  # Tap anywhere on the screen to confirm exit

# Start time updates and slideshow
update_time()
update_image()
root.mainloop()
