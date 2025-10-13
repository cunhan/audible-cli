import os, codecs,subprocess
import time

AUDIBLE_CLI_PATH = 'audible.exe'
DOWNLOAD_AAXC_DIR = "download"
DOWNLOAD_M4B_DIR = 'm4b'
TSV_FILE = 'library.tsv'
DOWNLOAD_MSG_SKIP = 'Skip download.'
DOWNLOAD_MSG_NOTFOUND = 'not found in library.'
DOWNLOAD_MSG_UNAUTH = 'error: License not granted to customer'
DOWNLOAD_MSG_SUCCESS = 'aaxc downloaded in'
DOWNLOAD_MSG_SUCCESS_1SEC = 'aaxc downloaded in 0:00:01.'
DOWNLOAD_MSG_UnPublished = 'is not published. It will be available in'
DOWNLOAD_404 = 'Not Found (404)'
DOWNLOAD_INTERVAL = 680
MAXSIZE_ONE_DAY = 40*1000*1000*1000 #40 in 1 day


# 收集已经下载并解码的有声书m4b列表。
# M4B_LIB_PATH = "e:\\airu\\audible-cli-master\\m4b"
def m4b_lib():
    asins = []
    for root, dirs, files in os.walk(DOWNLOAD_M4B_DIR):
        for file in files:
            asin = os.path.basename(file).split('_')[-1]
            asin = asin[:10]
            asins.append(asin)
    # print(f"Found {len(asins)} items in m4b library.")
    return asins
    
def get_library(tsv):
    data = codecs.open(tsv, 'r', encoding='utf-8').readlines()
    data = data[1:]
    lib = []
    m4bs = m4b_lib()
    for line in data:
        item = line.split('\t')
        runtime = 0
        if len(item) > 10:
            runtime = int(item[9])
        asin = item[0]
        # 检查本地是否已经下载
        if asin in m4bs:
            # print(asin + " exsited, omit.")
            continue
        lib.append((runtime, asin.strip()))
    # 每天下载100个
    print(f"total: {len(lib)}/{len(data)}")
    lib = lib[:100]
    #only asin list in tsv
    if len(data[1].strip()) == 10:
        return [x[1] for x in lib]
    lib.sort()
    lib2 = []
    fulllen = len(lib)
    halflen = int(fulllen/2)
    for i in range(halflen):
        asin = lib[i][1]
        lib2.append(asin)
        asin = lib[fulllen-i-1][1]
        lib2.append(asin)
    if not len(lib2) == fulllen:
        lib2.append(lib[halflen][1])
    return lib2

def get_aaxc_files(aaxcdir=DOWNLOAD_AAXC_DIR):
    def sort_aaxc(e):
        return e[1]
    
    aaxc = []
    for file in os.listdir(aaxcdir):
        ext = os.path.splitext(file)
        if not ext == 'aaxc':
            continue
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
    firstfiletime = 0
    for aa in aaxc:
        delta = now - aa[1]
        if delta < 86400:
            totalsize += aa[2]
            firstfiletime = aa[1]
        else:
            break
    if totalsize > MAXSIZE_ONE_DAY:
        return firstfiletime
    return 0

def run_donwload(asin, cli = AUDIBLE_CLI_PATH):
    cmd = f"{cli} download -a {asin} --aaxc -f asin_ascii -o {DOWNLOAD_AAXC_DIR}"
    print(f"[Running] {cmd}")
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    r = p.stdout.read().decode('utf-8').strip()
    # print(r)
    # # budang only
    # return 5
    if DOWNLOAD_MSG_SKIP in r:
        #wait 5s for next book
        return 5
    elif DOWNLOAD_MSG_NOTFOUND in r:
        #wait 5s for next book
        return 5
    elif DOWNLOAD_MSG_UNAUTH in r:
        #banned downloading, cool down for 1 day.
        aaxc = get_aaxc_files()
        if len(aaxc) == 0:
            return 87400
        lastfiletime = aaxc[0][1]
        tommorrow = lastfiletime + 87400
        return int(tommorrow - time.time()) * -1
    # elif DOWNLOAD_MSG_SUCCESS_1SEC in r:
        # #do not wait small files
        # return 1
    elif DOWNLOAD_MSG_SUCCESS in r:
        # success downloading one book, wait 10min for next book.
        # about 100 books for one day.
        return DOWNLOAD_INTERVAL
    elif DOWNLOAD_MSG_UnPublished in r:
        print(r)
        return 1
    elif DOWNLOAD_404 in r:
        print(r)
        return 2
    else:
        print(r)
        print("[Unknown result]")
        return -999


lib = get_library(TSV_FILE)

total = len(lib)
if total == 0:
    print('No new items. Sleep 6 hour.')
    time.sleep(3600*6)
print(f'{total} items will be download...')
i = 1
for asin in lib:
    while(True):
        firstfiletime = check_total_oneday()
        if firstfiletime == 0:
            break
        nextdaytime = firstfiletime + 86400
        nextdaytime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(nextdaytime))
        checkedtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print(f'\rOver 40G, wait until {nextdaytime}. Checked at {checkedtime}', end='')
        time.sleep(300)
    print('\n')    
    waitsecond = -1
    #retry if banned.
    while(waitsecond < 0):
        print(f"[{i}/{total}] {asin} is processing")
        waitsecond = run_donwload(asin)
        if waitsecond == DOWNLOAD_INTERVAL:
            # print("download success, processing...")
            cmd = "call decrypt.bat & call catalog_Rename.bat"
            # print(f"[Running] {cmd}")
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            r = p.stdout.read().decode('utf-8').strip()
            # print(r)
        if waitsecond == -999:
            break
        print(f"[{i}/{total}] {asin} is processed")
        print(f'Waiting {waitsecond}s...')
        time.sleep(abs(waitsecond))     
    i = i + 1