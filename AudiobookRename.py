# coding:utf-8
import os, sys, subprocess, json, re, requests
import codecs
import argparse

def validateTitle(title):
    new_title = title
    new_title = new_title.replace('/', '／')
    new_title = new_title.replace(':', '：')
    new_title = new_title.replace('?', '？')
    rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, "", new_title)  # 替换为下划线
    return new_title

def get_library(tsv):
    data = codecs.open(tsv, 'r', encoding='utf-8').readlines()
    data[1:]
    lib = {}
    for line in data:
        item = line.split('\t')
        #print("%s【%s】【%s】【%s】【%s】" % (item[0], item[1], item[4],item[6], item[8]))
        title = item[1]
        author = item[4]
        series = item[6]
        catalogs = item[8].split(', ')
        lib[item[0]] = [title, author, series, catalogs]
    return lib

def get_catalog_from_web(bookcode):
    cat = ['404primaryCategory', '404subCategory1']
    series = ''
    #从网页上获取【分类名（主类别、次类别）】和【系列名】
    url = 'https://www.audible.co.jp/pd/' + bookcode

    r = requests.get(url)
    lines = r.text.split('\n')
    for line in lines:
        if 'primaryCategory = "' in line:
            s = line.find('"')
            e = line.find(';')        
            c = line[s+1:e-1]
            if c:    
                c = c.encode().decode("unicode_escape") 
                cat[0] = c
        #次类别可能会为“none”      
        if 'subCategory1 = "' in line:
            s = line.find('"')
            e = line.find(';')        
            c = line[s+1:e-1]
            if c:  
                c = c.encode().decode("unicode_escape") 
                cat[1] = c
                
        if 'href="/series' in line:
            s = line.find('>')
            e = line.find('<')        
            series = line[s+1:e].strip()
            series = validateTitle(series)    
    return series, cat

def get_metadata_from_m4b(book):
    mediainfo = "MediaInfo.exe"
    cmd = '"%s" "%s" --output=JSON' %(mediainfo, book)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    r = p.stdout.read().decode('utf-8')
    j = json.loads(r)
    title = validateTitle(j["media"]["track"][0]["Title"])
    artist = validateTitle(j["media"]["track"][0]["Performer"])
    bookcode = j["media"]["track"][0]["extra"]["CDEK"]
    return (bookcode, [title, artist])
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="AudiobookRename",
        description="Audiobook Rename and Sort by Catalog.",
        )
    
    parser.add_argument("-o", "--output", help="output folder")
    parser.add_argument("--tsv", help="get book info from tsv")          
    parser.add_argument("m4b", help="audiobook to be renamed")
    args = parser.parse_args()    

    book = args.m4b
    bookcode, bookmeta = get_metadata_from_m4b(book)
    
    #第3个参数为目录名，结尾是斜杠符\，传进来会把后面的双引号"转义。因此在bat的双引号前加一个空格避免这种情况。
    #因此需要处理一下output的值，清除末尾的空格和斜杠符
    outputdir = args.output
    outputdir = outputdir.strip()
    if outputdir.endswith('\\'):
        outputdir = outputdir[:-1]

    if args.tsv:
        #虽然本地更快，但不推荐使用tsv          
        #tsv的分类由“分类”和“tag”组成，tag比较杂乱，不适合用来进行分类。
        lib = get_library(args.tsv)
        libmeta = lib.get(bookcode)
        if not libmeta is None:
            bookmeta = libmeta
            
    if len(bookmeta) == 2:
        #not found in tsv, get catalog from web
        series, catalogs = get_catalog_from_web(bookcode)
        bookmeta.append(series)
        bookmeta.append(catalogs)

    title = validateTitle(bookmeta[0])
    artist = validateTitle(bookmeta[1])
    cat = bookmeta[3]
    cat.append(bookmeta[2])
    cat.insert(0, outputdir)
    catdir = '\\'.join(cat)
    if not os.path.exists(catdir):
        os.makedirs(catdir)
    renamebook = "[%s] %s _%s.m4b" % (artist, title, bookcode)
    # print(catdir, renamebook)
    os.rename(book, os.path.join(catdir, renamebook))