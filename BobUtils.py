from googleapiclient.discovery import build
import googleapiclient.discovery
import re
import yt_dlp

class YoutubeUtils:
    def __init__(self, ytkey):
        self.__ytkey = ytkey
        self.youtube: googleapiclient.discovery.Resource = build('youtube', 'v3', developerKey=self.__ytkey)

    @staticmethod
    def convert_time_to_seconds(time_str: str):
        """
        converts youtube formatted time into int seconds
        """
        # Define a regular expression pattern to extract minutes and seconds
        pattern = r'^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$'
        match = re.match(pattern, time_str)

        

        if not match:
            raise ValueError("Invalid time format")

        # Extract minutes and seconds from the match groups
        hours_str = match.group(1)
        minutes_str = match.group(2)
        seconds_str = match.group(3)

        # Convert minutes and seconds to integers, default to 0 if None
        hours = int(hours_str) if hours_str else 0
        minutes = int(minutes_str) if minutes_str else 0
        seconds = int(seconds_str) if seconds_str else 0

        # Convert total time to seconds
        total_seconds = hours * 3600 + minutes * 60 + seconds
        return total_seconds
    
    
    def yt_duration(self, id):
        request2 = self.youtube.videos().list(
            part='contentDetails',
            id=id
        )
        print(request2)
        response2 = request2.execute()
        print(response2)
        dur = str(response2.get('items')[0].get('contentDetails').get('duration'))
        addur: int = self.convert_time_to_seconds(dur)
        return addur

    def youtube_search(self, search: str):
        request = self.youtube.search().list(
            part='id',
            maxResults=1,
            q=search,
            type='video'
        )
        try:
            print(request.text)
        except:
            print('cring 5')
        print('eee')
        print(search)
        response = request.execute()
        print(response)
        url : str = 'https://youtube.com/watch?v=' + response.get('items')[0].get('id').get('videoId')
        print(url)
    
        return [url, self.yt_duration(response.get('items')[0].get('id').get('videoId'))]
    
    def get_audio_stream_url(video_url) -> dict:
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,  # Ensure that only a single video is downloaded
            'quiet': True  # Less verbose output
        }
        ydl = yt_dlp.YoutubeDL(ydl_opts)
        info_dict = ydl.extract_info(video_url, download=False)
        audio_url = info_dict['url']
        return audio_url
    
    def quick_search(self, search):
        """returns [yt_url, audio_url, time in seconds]
        """
        data = self.youtube_search(search)
        return {'yt': data[0], 'url': YoutubeUtils.get_audio_stream_url(data[0]), 'duration' : data[1]}


class Queue:
    def __init__(self, ytkey):
        self.queuelist = []
        self.ytkey = ytkey

    #item format: [yt url, audio stream url, length in seconds]
    def add_item(self, search: str):
        item: dict = YoutubeUtils(self.ytkey).quick_search(search)
        self.queuelist.append(item)

    def remove_finished_item(self):
        self.queuelist = self.queuelist[1:]
    
    def fancy_item_data(self, index: int):
        item = self.queuelist[index]
        return f'Song URL: {item[0]} | Duration: {item[2]}'
    
    def clear(self):
        self.queuelist = []
    
    def clean(self):
        self.queuelist = [self.queuelist[0]]
