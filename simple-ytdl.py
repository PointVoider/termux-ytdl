import sys
from os import path as os_path, remove as os_remove, rename as os_rename
from getopt import getopt, GetoptError
from re import search as regex_search
from datetime import datetime as dt
from youtube_dl import YoutubeDL
from colorama import init
from colorama import Fore
import math


def convert_size(size_bytes):
    #https://stackoverflow.com/a/14822210
    if size_bytes == 0 or size_bytes == None:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def convert_second(seconds):
    #https://www.geeksforgeeks.org/python-program-to-convert-seconds-into-hours-minutes-and-seconds/
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    return "%d:%02d:%02d" % (hour, minutes, seconds)


init()

foreColors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.MAGENTA, Fore.CYAN]


def log_url_history(log):
    date = dt.today().strftime('%Y-%m-%d | %H:%M:%S')
    with open('urlLog.txt', 'a') as f:
        f.write(f'{date}\t{log}\n')
        f.close()


def get_input_number(min, max, prompt='Choose : '):
    i = min - 1
    while i < min or i > max:
        try:
            i = int(input(prompt))
        except:
            i = min - 1
            print("Masukkan angka!")

    return i


def get_filename_from_output(str):
    try:
        out = str
        dest = regex_search('\[ffmpeg\] .+"(.+)"', out)
        if dest is not None:
            dest = dest.group(1)
        elif regex_search('\[ffmpeg\].+: (.+)', out) is not None:
            dest = regex_search('\[ffmpeg\].+: (.+)', out).group(1)
        elif regex_search('Destination: (.+)\n', out) is not None:
            dest = regex_search('Destination: (.+)\n', out).group(1)
        else:
            dest = regex_search('\[download] (.+) has already been downloaded',
                                out).group(1)

        return dest
    except:
        pass


class Config:
    def __init__(self, fileName) -> None:
        self.fileName = fileName
        self.configs = [()]

    def add(self, type, val):
        self.configs.append((type, val))

    def remove_all_type(self, type):
        for t, v in self.configs[:]:
            if t == type:
                self.configs.remove((t, v))

    def show(self):
        for config in self.configs:
            key, val = config
            print(key, val)

    def save(self):
        with open(self.fileName, 'w') as f:
            for config in self.configs:
                key, val = config
                f.write(key + '=' + val + '\n')

    def load(self):
        try:
            self.configs = []
            with open(self.fileName, 'r') as f:
                lines = f.read().splitlines()
                for line in lines:
                    lineSplit = line.split('=')
                    self.add(lineSplit[0], lineSplit[1])
            return True
        except:
            return False


cookies = {}
dlPath = ''
config = Config('conf.ini')

output = ''


class MyLogger(object):
    def debug(self, msg):
        global output
        output += msg + '\n'

    def warning(self, msg):
        global output
        output += msg + '\n'

    def error(self, msg):
        global output
        output += msg + '\n'
        print(msg)


def printProgressBar(i, max, postText):
    #https://stackoverflow.com/a/58602365
    n_bar = 10  #size of progress bar
    j = i / max
    sys.stdout.write('\r')
    sys.stdout.write(
        f"[{'=' * int(n_bar * j):{n_bar}s}] {int(100 * j)}%  {postText}")
    sys.stdout.flush()


def my_progress(entries):
    elapsed = entries.get('elapsed', 0)
    if entries['status'] == 'downloading':
        downloaded_size = entries.get('downloaded_bytes', 0)
        total_size = entries.get('total_bytes', 0)
        eta = entries.get('eta', 0)
        speed = entries.get('speed', 0)
        percent = math.floor(int((downloaded_size * 100) / total_size))
        printProgressBar(
            percent, 100,
            f'{convert_second(elapsed)}/{convert_second(eta)} | Speed : {convert_size(speed)}/s'
        )
    if entries['status'] == 'finished':
        printProgressBar(
            100, 100,
            f'| Finished after {convert_second(elapsed)}                        '
        )
        print()


class YTDL:
    def __init__(self, url):
        self.url = url
        self.ydl_opts = {
            'format':
            'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best',
            'listformats': False,
            'updatetime': False,
            'quiet': True,
            'outtmpl': f'{dlPath}%(title)s.%(resolution)s.%(id)s.%(ext)s',
            'progress_hooks': [my_progress],
            'logger': MyLogger()
        }
        self.yt_urls = ['youtube.com/', 'youtu.be/']
        self.output = ''
        self.videoTitle = ''
        self.videoViews = 0
        self.videoLikes = 0
        self.videoDislikes = 0
        self.videoDuration = 0
        self.videoUploader = ''

    def get_yt_quality(self, formats):
        availableFormats = {}
        audioSize = 0
        for format in formats:
            format_note = format['format_note']
            if format_note is None or 'p' not in format_note:
                size = format['filesize']
                if size > audioSize:
                    if size is not None:
                        audioSize = size
                continue
            size = format['filesize']
            fps = format['fps']
            reso = format['height']
            if size is not None:
                availableFormats[format_note] = (reso, (size + audioSize), fps)

        return availableFormats

    def get_formats_and_set_infos(self):
        with YoutubeDL(self.ydl_opts) as ydl:
            meta = ydl.extract_info(self.url, False)
            self.videoTitle = meta.get('title', None)
            self.videoViews = meta.get('view_count', None)
            self.videoLikes = meta.get('like_count', None)
            self.videoDuration = meta.get('duration', None)
            self.videoUploader = meta.get('uploader', None)
            self.videoDislikes = meta.get('dislike_count', None)
            return meta.get('formats', [meta])

    def download_youtube(self):
        availableFormats = self.get_yt_quality(
            self.get_formats_and_set_infos())

        print(Fore.BLUE + 'Video :')
        print(Fore.GREEN, 'Title   :', self.videoTitle)
        print(Fore.GREEN, 'Channel :', self.videoUploader)
        print(Fore.BLUE + 'Statistic :')
        print(Fore.GREEN, 'Duration : ', convert_second(
            self.videoDuration)) if self.videoDuration is not None else None
        print(Fore.GREEN, 'Views    : ',
              f'{self.videoViews:,}') if self.videoViews is not None else None
        print(Fore.GREEN, 'Likes    : ',
              f'{self.videoLikes:,}') if self.videoLikes is not None else None
        print(Fore.GREEN, 'Dislikes : ', f'{self.videoDislikes:,}'
              ) if self.videoDislikes is not None else None

        print(Fore.BLUE + 'All Resolutions :')
        i = 0
        print(foreColors[i], '0 => Audio Only(mp3)')
        for key, info in availableFormats.items():
            reso, size, fps = info
            i += 1
            print(foreColors[i % len(foreColors)], i, '=>', key,
                  f'\t({convert_size(size)})')
        print(Fore.RESET)
        i = get_input_number(0, len(availableFormats)) - 1
        formatList = list(availableFormats)
        key = formatList[i]
        format = availableFormats[key]
        reso = format[0]
        fps = format[2]
        if i == -1:
            self.ydl_opts = {
                'format':
                'bestaudio/best',
                'outtmpl':
                f'{dlPath}%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192'
                }],
            }
        else:
            self.ydl_opts[
                'format'] = f'bestvideo[height<={reso}][fps={fps}]+bestaudio/{self.ydl_opts["format"]}'
        self.ydl_opts['quiet'] = False

        with YoutubeDL(self.ydl_opts) as ydl:
            # meta = ydl.extract_info(self.url, False)
            ydl.download([self.url])

    def download_generic(self, cookie=None):
        self.ydl_opts['quiet'] = False
        if cookie is not None:
            self.ydl_opts['cookiefile'] = cookie

        with YoutubeDL(self.ydl_opts) as ydl:
            ydl.download([self.url])

    def is_youtube_video(self):
        isYTVid = False
        for yt_url in self.yt_urls:
            if yt_url in self.url:
                isYTVid = True
                break
            else:
                isYTVid = False

        return isYTVid


def add_cookies(name, location):

    if not os_path.isfile(location):
        print(f'{location} not found or not a file')
        return

    config.add('cookies', f'{name}|{location}')
    cookies[name] = location
    config.save()
    print(f'{name} has been added.')


def show_cookies():
    i = 0
    if len(cookies):
        print(Fore.BLUE + 'Saved Cookies:')
        for name, path in cookies.items():
            i += 1
            print(foreColors[(i) % len(foreColors)], i, '=>',
                  f'{name} [{path}]')
    else:
        print(
            "There's no saved cookies!\nsave cookies by typing this command inside termux:\npython simple-ytdl.py -a \"CookiesName|/Path/To/CookiesFile.txt\""
        )


def set_path(path):
    if not os_path.exists(path):
        print('Path not found!')
        return

    dlPath = path
    config.remove_all_type('dlPath')
    config.add('dlPath', dlPath)
    config.save()
    print('New download location has been saved.')


def download(url):
    log_url_history(url)
    ytdl = YTDL(url)
    if ytdl.is_youtube_video():
        print('Downloading Youtube Url', url)
        print("Getting Available Resolutions...")
        ytdl.download_youtube()
    else:
        print('Downloading Generic Url', url)
        print('1 => Download')
        print('2 => Download with cookies')
        i = get_input_number(
            1,
            2,
        )
        cookie = None

        if i == 2:
            show_cookies()
            if len(cookies):
                i = get_input_number(
                    1,
                    len(cookies),
                ) - 1
                paths = list(cookies.values())
                cookie = paths[i]

        ytdl.download_generic(cookie)

    filename = get_filename_from_output(output)
    print(f'Sucessfully downloaded to [{filename}]')
    try:
        with open('out.txt', 'w') as f:
            f.write(filename)
            f.close()
    except:
        pass

def setup():
    dlLocation = ''
    while(dlLocation == ''):
        dlLocation = input("Input Download Location : ")
        dlLocation = dlLocation if os_path.exists(dlLocation) else ''
        
    set_path(dlLocation)

def process_cmd_arguments(argv):

    try:
        opts, args = getopt(
            argv, 'hsrp:d:a:',
            ['help', 'reset','setup', 'set-path=', 'add-cookies=', 'show-cookies'])
    except GetoptError as err:
        print(err)
        exit()

    # print(opts)
    try:
        for opt, arg in opts:
            if opt in ['-h', '--help']:
                usage()
            elif opt in ['-a', '--add-coookies']:
                print('Adding Cookies')
                argSplit = arg.split('|')
                add_cookies(argSplit[0], argSplit[1])
            elif opt in ['-d']:
                download(arg)
                exit()
            elif opt in ['-p', '--set-path']:
                print('Setting download location')
                set_path(arg)
            elif opt in ['-s', '--show-cookies']:
                show_cookies()
            elif opt in ['-r', '--reset']:
                print('deleting conf.ini...')
                try:
                    os_remove('conf.ini')
                    print('conf.ini has been deleted')
                except:
                    print(R"the file doesn't exist")
            elif opt == '--setup':
                setup()
    except Exception as err:
        print(err)
        exit()


def usage():
    print("""\
Usage:
-a, --add-cookies="<name>|<location>"   Save cookies file location to be used later. ex: -a "CookiesName|/Path/To/CookiesFile.txt" (remember to put it inside quotes)
-p, --set-path=<path>                   Set the downloaded video location.
-d <url>                                Download the video from the url.
-s, --show-cookies                      List all saved cookies.
-r, --reset                             Reset all settings.
--setup                                 Setup.\
    """)


def set_global_variables():
    global dlPath
    for conf in config.configs[:]:
        type, val = conf
        if type == 'cookies':
            valSplit = val.split('|')
            name = valSplit[0]
            file = valSplit[1]
            if not os_path.isfile(file):
                print(f'The file {file} has been moved or deleted')
                config.configs.remove((type, val))
                continue
            cookies[name] = file
        elif type == 'dlPath':
            if not os_path.exists(val):
                print(f'{val} directory is either moved or deleted')
                config.configs.remove((type, val))
                continue
            if '/' in val:
                if val[-1] != '/':
                    val += '/'
            elif '\\' in val:
                if val[-1] != '\\':
                    val += '\\'

            dlPath = val

    config.save()


def main(argv):
    #argv = ['-d' 'https://web.facebook.com/1509laji/videos/503653300732911']
    #argv = ['-d', 'https://www.youtube.com/watch?v=L7OHcDnWw-c']
    # argv = [
    #     '-d',
    #     'https://www.instagram.com/p/CRdyJdEA7y0/?utm_source=ig_web_button_share_sheet'
    # ]
    # argv = ['-p', 'D:']
    argv = ['--setup']
    if config.load():
        set_global_variables()
    process_cmd_arguments(argv)


if __name__ == "__main__":
    main(sys.argv[1:])
