import requests
import re
import sys
from terminal import eprint


def get_file_name_from_url(url: str):
    def get_filename_from_cd(cd):
        """
        Get filename from content-disposition
        """
        if not cd:
            return None

        fname = re.findall('filename=(.+)', cd)

        if len(fname) == 0:
            return None

        return fname[0]

    remotefile = requests.head(url, allow_redirects=True)
    cd = remotefile.headers.get('content-disposition')
    filename = get_filename_from_cd(cd)

    if filename is None:
        filename = url.rsplit("/")[-1]
    return filename


def download_file(url: str, chunk_size=4096):
    filename = get_file_name_from_url(url)

    with open(filename, "wb") as f:
        print("Downloading %s" % filename)
        response = requests.get(url, stream=True, allow_redirects=True)
        total_length = response.headers.get('content-length')

        if total_length is None:  # no content length header
            eprint("The header does not specify the file size.")
            dl = 0

            for data in response.iter_content(chunk_size=chunk_size):
                dl += len(data)
                f.write(data)

                sys.stdout.write("\r%s" % file_size_string(dl))
                sys.stdout.flush()

        else:
            dl = 0
            total_length = int(total_length)

            for data in response.iter_content(chunk_size=chunk_size):
                dl += len(data)
                f.write(data)
                done = int(50 * dl / total_length)
                p = dl / total_length * 100
                p = p if p <= 100 else 100
                sys.stdout.write("\r[%s%s] %.2f" %
                                 ('#' * done, ' ' * (50-done), p))
                sys.stdout.flush()


def file_size_string(bytes: int):
    if bytes > 1_000_000_000:
        s = "{:.2f}GB".format(bytes / 1_000_000_000)
    elif bytes > 1_000_000:
        s = "{:.2f}MB".format(bytes / 1_000_000)
    elif bytes > 1_000:
        s = "{:.2f}KB".format(bytes / 1_000)
    else:
        s = "{}B".format(bytes)

    if len(s) < 9:
        s = (" " * (9 - len(s))) + s

    return s
