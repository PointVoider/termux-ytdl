import sys
from os import path as os_path, remove as os_remove, rename as os_rename
from getopt import getopt, GetoptError
from re import search as regex_search
from datetime import datetime as dt
from youtube_dl import YoutubeDL


def logHistory(log):
    date = dt.today().strftime('%Y-%m-%d | %H:%M:%S')
    with open('urlLog.txt', 'a') as f:
        f.write(f'{date}\t{log}\n')
        f.close()


def getInputNumber(min, max, prompt='Choose : '):
    i = int(input(prompt))
    while i < min or i > max:
        i = int(input(prompt))
    return i


def regexFileNameFromStr(str):
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


class GetPrinted(object):
    Output = ''
    __origStdOut__ = None
    __custom__ = None

    def Begin():
        GetPrinted.__origStdOut__ = sys.stdout
        GetPrinted.__custom__ = GetPrinted.__Custom()
        sys.stdout = GetPrinted.__Tee(sys.stdout, GetPrinted.__custom__)

    def End():
        sys.stdout = GetPrinted.__origStdOut__
        GetPrinted.Output = GetPrinted.__custom__.out
        return GetPrinted.Output

    class __Custom(object):
        def __init__(self) -> None:
            self.out = ''

        def write(self, str):
            self.out += str

        def flush(self):
            pass

    class __Tee(object):
        def __init__(self, *files):
            self.files = files

        def write(self, obj):
            for f in self.files:
                f.write(obj)

        def flush(self):
            for f in self.files:
                f.flush()


class Config:
    def __init__(self, fileName) -> None:
        self.fileName = fileName
        self.configs = [()]

    def Add(self, type, val):
        self.configs.append((type, val))

    def RemoveAll(self, type):
        for t, v in self.configs[:]:
            if t == type:
                self.configs.remove((t, v))

    def Show(self):
        for config in self.configs:
            key, val = config
            print(key, val)

    def Save(self):
        with open(self.fileName, 'w') as f:
            for config in self.configs:
                key, val = config
                f.write(key + '=' + val + '\n')

    def Load(self):
        try:
            self.configs = []
            with open(self.fileName, 'r') as f:
                lines = f.read().splitlines()
                for line in lines:
                    lineSplit = line.split('=')
                    self.Add(lineSplit[0], lineSplit[1])
            return True
        except:
            return False


cookies = {}
dlPath = ''
config = Config('conf.ini')


class YTDL:
    def __init__(self, url):
        self.url = url
        self.ydl_opts = {
            'format':
            'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio',
            'listformats': False,
            'updatetime': False,
            'quiet': True,
            'outtmpl': f'{dlPath}%(title)s.%(resolution)s.%(id)s.%(ext)s'
        }
        self.yt_urls = ['youtube.com/', 'youtu.be/']
        self.output = ''

    def getYoutubeQuality(self, formats):
        availableFormats = []
        for format in formats:
            reso = format['height']
            if reso is None:
                continue
            if reso not in availableFormats:
                availableFormats.append(reso)

        return availableFormats

    def getFormats(self):
        with YoutubeDL(self.ydl_opts) as ydl:
            meta = ydl.extract_info(self.url, False)
            return meta.get('formats', [meta])

    def DownloadYoutube(self):
        availableFormats = self.getYoutubeQuality(self.getFormats())

        i = 0
        print('0 => Audio Only(mp3)')
        for reso in availableFormats:
            i += 1
            print(i, '=>', reso)

        i = getInputNumber(0, len(availableFormats)) - 1

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
                'format'] = f'bestvideo[height={availableFormats[i]}]+bestaudio/{self.ydl_opts["format"]}'
        self.ydl_opts['quiet'] = False

        GetPrinted.Begin()
        with YoutubeDL(self.ydl_opts) as ydl:
            ydl.download([self.url])
        self.output = GetPrinted.End()

    def DownloadGeneric(self, cookie=None):
        self.ydl_opts['quiet'] = False
        if cookie is not None:
            self.ydl_opts['cookiefile'] = cookie

        GetPrinted.Begin()
        with YoutubeDL(self.ydl_opts) as ydl:
            ydl.download([self.url])
        self.output = GetPrinted.End()

    def isYoutubeVideo(self):
        isYTVid = False
        for yt_url in self.yt_urls:
            if yt_url in self.url:
                isYTVid = True
                break
            else:
                isYTVid = False

        return isYTVid


def addCookies(name, location):

    if not os_path.isfile(location):
        print(f'{location} not found or not a file')
        return

    config.Add('cookies', f'{name}|{location}')
    cookies[name] = location
    config.Save()
    print(f'{name} has been added.')


def showCookies():
    i = 0
    if len(cookies):
        print('\nSaved Cookies:')
        for name, path in cookies.items():
            i += 1
            print(i, '=>', f'{name} [{path}]')
    else:
        print("There's no saved cookies!\nsave cookies by typing this command inside termux:\npython simple-ytdl.py -a CookiesName|/Path/To/CookiesFile.txt")


def setPath(path):
    if not os_path.exists(path):
        print('Path not found!')
        return

    dlPath = path
    config.RemoveAll('dlPath')
    config.Add('dlPath', dlPath)
    config.Save()
    print('New download location has been saved.')


def download(url):
    logHistory(url)
    ytdl = YTDL(url)
    if ytdl.isYoutubeVideo():
        print('Downloading Youtube Url', url)
        print("Getting Available Resolutions...")
        ytdl.DownloadYoutube()
    else:
        print('Downloading Generic Url', url)
        print('1 => Download')
        print('2 => Download with cookies')
        i = getInputNumber(
            1,
            2,
        )
        cookie = None

        if i == 2:
            showCookies()
            if len(cookies):
                i = getInputNumber(
                    1,
                    len(cookies),
                ) - 1
                paths = list(cookies.values())
                cookie = paths[i]

        ytdl.DownloadGeneric(cookie)

    out = ytdl.output
    filename = regexFileNameFromStr(out)
    new_filename = filename.replace('#', '')
    os_rename(filename, new_filename)

    try:
        with open('out.txt', 'w') as f:
            f.write(new_filename)
            f.close()
    except:
        pass


def processArg(argv):

    try:
        opts, args = getopt(
            argv, 'hsrp:d:a:',
            ['help', 'reset', 'set-path=', 'add-cookies=', 'show-cookies'])
    except GetoptError as err:
        print(err)
        exit()

    # print(opts)
    try:
        for opt, arg in opts:
            if opt in ['-h', '--help']:
                printHelp()
            elif opt in ['-a', '--add-coookies']:
                print('Adding Cookies')
                argSplit = arg.split('|')
                addCookies(argSplit[0], argSplit[1])
            elif opt in ['-d']:
                download(arg)
                exit()
            elif opt in ['-p', '--set-path']:
                print('Setting download location')
                setPath(arg)
            elif opt in ['-s', '--show-cookies']:
                showCookies()
            elif opt in ['-r', '--reset']:
                print('deleting conf.ini...')
                try:
                    os_remove('conf.ini')
                    print('conf.ini has been deleted')
                except:
                    print(R"the file doesn't exist")
    except Exception as err:
        print(err)
        exit()


def printHelp():
    print("""\
-a, --add-cookies="<name>|<location>"   Save cookies file location to be used later.
-d <url>                                Download the video from the url.
-p, --set-path=<path>                   Set the downloaded video location.
-s, --show-cookies                      List all saved cookies.
-r, --reset                             Reset all settings\
    """)


def loadVariables():
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
            dlPath = val

    config.Save()


def main(argv):
    # argv = ['-d' 'https://web.facebook.com/1509laji/videos/503653300732911']
    # argv = ['-d', 'https://youtu.be/wGiKS4KD_38']
    # argv = ['-p', 'D:']
    if config.Load():
        loadVariables()
    processArg(argv)


if __name__ == "__main__":
    main(sys.argv[1:])
