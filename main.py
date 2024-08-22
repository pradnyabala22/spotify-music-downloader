import tkinter as tk
from tkinter import filedialog, messagebox
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import yt_dlp
from googleapiclient.discovery import build
import threading

from config import SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, YOUTUBE_API_KEY

#tkinter window
root = tk.Tk()
root.title("Spotify Playlist Downloader")
root.geometry("800x800")
root.config(bg="#e6f2ff")

#font_name = "Futura"
font_name = "Gotu"
font_size = 25

titleLabel = tk.Label(root, text="Spotify Playlist Downloader", font=(font_name, '40', 'bold', 'underline'), bg="#e6f2ff", fg="#003366")
titleLabel.pack(pady=10)

urlInputLabel = tk.Label(root, text="Spotify Playlist URL/ID:", font=(font_name, font_size, 'bold'), bg="#e6f2ff", fg="#003366")
urlInputLabel.pack(pady=10)
url_entry = tk.Entry(root, width=50, font=(font_name, font_size))
url_entry.pack(pady=10)

#selecting directory
def browse_directory():
    directory = filedialog.askdirectory()
    if directory:
        directory_entry.delete(0, tk.END)
        directory_entry.insert(0, directory)

saveDirectoryLabel = tk.Label(root, text="Save Directory:", font=(font_name, font_size, 'bold'), bg="#e6f2ff", fg="#003366")
saveDirectoryLabel.pack(pady=10)
directory_entry = tk.Entry(root, width=50, font=(font_name, font_size))
directory_entry.pack(pady=10)

browse_button = tk.Button(root, text="Browse", command=browse_directory, font=(font_name, font_size, 'bold'), bg="#003366", fg="#003366")
browse_button.pack(pady=5)

subdirectoryLabel = tk.Label(root, text="Name of Subdirectory (Optional):", font=(font_name, font_size, 'bold'), bg="#e6f2ff", fg="#003366")
subdirectoryLabel.pack(pady=10)
subdir_entry = tk.Entry(root, width=50, font=(font_name, font_size))
subdir_entry.pack(pady=10)

download_button = tk.Button(root, text="Start Download", command=lambda: start_download_thread(url_entry.get(), directory_entry.get(), subdir_entry.get()), font=(font_name, font_size, 'bold'), bg="#ff6600", fg="#003366")
download_button.pack(pady=20)

downloading_label = tk.Label(root, text="", font=(font_name, font_size, 'bold'), bg="#e6f2ff", fg="#003366")
downloading_label.pack(pady=10)

progress_label = tk.Label(root, text="", font=(font_name, font_size, 'bold'), bg="#e6f2ff", fg="#003366")
progress_label.pack(pady=10)

reset_button = tk.Button(root, text="Download Another Playlist", command=lambda: clear_inputs_and_hide(), font=(font_name, int(font_size * 0.8)), bg="#ff6600", fg="#003366", padx=10, pady=5)

def clear_inputs_and_hide():
    clear_inputs()
    reset_button.pack_forget()
    progress_label.config(text="")
    downloading_label.config(text="")

def clear_inputs():
    url_entry.delete(0, tk.END)
    directory_entry.delete(0, tk.END)
    subdir_entry.delete(0, tk.END)

# downloading in separate thread
def start_download_thread(playlist_url_or_id, save_directory, subdirectory_name):

    downloading_label.config(text="Downloading...")
    root.update_idletasks() 
    
    download_thread = threading.Thread(target=start_download, args=(playlist_url_or_id, save_directory, subdirectory_name))
    download_thread.start()

def start_download(playlist_url_or_id, save_directory, subdirectory_name):
    if not playlist_url_or_id or not save_directory:
        messagebox.showerror("Error", "Please enter Spotify playlist URL/ID and the save directory to start downloading!")
        downloading_label.config(text="")
        return

    output_dir = os.path.join(save_directory, "Downloaded_MP3s")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if subdirectory_name:
        output_dir = os.path.join(output_dir, subdirectory_name)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    if "spotify.com" in playlist_url_or_id:
        playlist_id = playlist_url_or_id.split("/")[-1].split("?")[0]
    else:
        playlist_id = playlist_url_or_id

    #spotify authentication
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                                   client_secret=SPOTIPY_CLIENT_SECRET,
                                                   redirect_uri=SPOTIPY_REDIRECT_URI,
                                                   scope='playlist-read-private user-library-read'))

    tracks = get_playlist_tracks(sp, playlist_id)
    total_tracks = len(tracks)

    #downloading the tracks 
    for index, track in enumerate(tracks):
        youtube_url = search_youtube(track)
        download_mp3(youtube_url, track, output_dir)
        directory_text = f"{save_directory}/Downloaded_MP3s"
        if subdirectory_name:
            directory_text += f"/{subdirectory_name}"
        progress_label.config(text=f"{index + 1} song(s) downloaded to {directory_text}")
        root.update_idletasks()

    downloading_label.config(text="")
    messagebox.showinfo("Success", "Download Complete!")
    reset_button.pack(pady=10)

def get_playlist_tracks(sp, playlist_id):
    results = sp.playlist_tracks(playlist_id)
    tracks = []
    for item in results['items']:
        track = item['track']
        track_name = track['name']
        artist_name = track['artists'][0]['name']
        tracks.append(f"{track_name} {artist_name}")
    return tracks

def search_youtube(track_name):
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(
        q=track_name,
        part='snippet',
        maxResults=1
    )
    response = request.execute()
    video_id = response['items'][0]['id']['videoId']
    return f"https://www.youtube.com/watch?v={video_id}"

def download_mp3(youtube_url, track_name, output_dir):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(output_dir, f'{track_name}.mp3'),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])

root.mainloop()
