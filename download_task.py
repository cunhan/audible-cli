import os, codecs,subprocess
import time

AUDIBLE_CLI_PATH = 'e:\\PortableApp\\_KindleTools\\audible-cli\\audible.exe'
DOWNLOAD_AAXC_DIR = "download"
TSV_FILE = 'library.tsv'
DOWNLOAD_MSG_SKIP = 'Skip download.'
DOWNLOAD_MSG_NOTFOUND = 'not found in library.'
DOWNLOAD_MSG_UNAUTH = 'error: License not granted to customer'
DOWNLOAD_MSG_SUCCESS = 'new file'
MAXSIZE_ONE_DAY = 40*1024*1024*1024 #40 in 1 day

def get_library(tsv):
    data = codecs.open(tsv, 'r', encoding='utf-8').readlines()
    data = data[1:]
    lib = []
    for line in data:
        item = line.split('\t')
        lib.append(item[0].strip())
    return lib

def get_aaxc_files(aaxcdir=DOWNLOAD_AAXC_DIR):
    def sort_aaxc(e):
        return e[1]
    
    aaxc = []
    for file in os.listdir(aaxcdir):
        ext = os.path.splitext(file)
        # if not ext == 'aaxc':
        #     continue
        filepath = os.path.join(aaxcdir, file)
        size = os.path.getsize(filepath)
        modifytime = os.path.getmtime(filepath)
        aaxc.append([file, modifytime, size])
    aaxc.sort(key=sort_aaxc, reverse=True)
    return aaxc

def check_total_oneday(aaxcdir=DOWNLOAD_AAXC_DIR):    
    aaxc = get_aaxc_files(aaxcdir)
    now = time.time()
    totalsize = 0
    for aa in aaxc:
        delta = now - aa[1]
        if delta < 86400:
            totalsize += aa[2]
        else:
            break
    if totalsize > MAXSIZE_ONE_DAY:
        return False
    return True

def run_donwload(asin, cli = AUDIBLE_CLI_PATH):
    cmd = f"{cli} download -a {asin} --aaxc -f asin_ascii -o {DOWNLOAD_AAXC_DIR}"
    print(f"[Running] {cmd}")
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    r = p.stdout.read().decode('utf-8').strip()
    print(r)
    if DOWNLOAD_MSG_SKIP in r:
        #wait 5s for next book
        return 5
    elif DOWNLOAD_MSG_NOTFOUND in r:
        #wait 5s for next book
        return 5
    elif DOWNLOAD_MSG_UNAUTH in r:
        #banned downloading, cool down for 1 day.
        aaxc = get_aaxc_files()
        lastfiletime = aaxc[0][1]
        tommorrow = lastfiletime + 87400
        return int(tommorrow - time.time()) * -1
    # if DOWNLOAD_MSG_SUCCESS in r:
        #success downloading one book, wait 10min for next book.
        #100 books for one day.
    else:
        return 600

successcount = 0
lib = get_library(TSV_FILE)
for asin in lib:
    # if successcount == 10:
    #     print('Ten books is download, wait for 1.5 hour.')
    #     time.sleep(5000)
    #     successcount = 0

    if check_total_oneday():
        waitsecond = -1
        #retry if banned.
        while(waitsecond < 0):
            waitsecond = run_donwload(asin)
            print(f'Waiting {waitsecond}s')
            time.sleep(abs(waitsecond))
        # if waitsecond == 10:
        #     successcount += 1        
    else:
        print('Over 40G, wait until next day.')
        time.sleep(300)

# print(check_total_oneday())
# print(run_donwload('fake', cli='e:\\PortableApp\\_KindleTools\\audible-cli\\audible.exe'))
# print(run_donwload('B0DQXXXQQC', cli='e:\\PortableApp\\_KindleTools\\audible-cli\\audible.exe'))