# -*- coding: utf-8 -*-
import ConfigParser
import os
import tarfile
import time
import datetime
import threading
import re

CONFIG_FILE = "pack.cfg"

'''
    初始化配置
'''
def init_config(fileName):
    if os.path.exists( os.path.join(os.getcwd(),fileName) ):
        conf = ConfigParser.ConfigParser()
        conf.read(fileName)
        return conf
    
    return -1

'''
    读取公共配置项
'''
def read_common_options(conf):
    maxSerial = conf.get("COMMON", "MAX_SERIAL_NO")
    maxSerialNo = int(re.sub("\\D","", maxSerial))

    maxTarSizeExpr = conf.get("COMMON", "MAX_TARFILE_SIZE")
    maxTarFileSize = eval(maxTarSizeExpr.lstrip().rstrip()) 

    duration = conf.get("COMMON", "TIME_WAIT")
    timeWait = int(re.sub("\\D","", duration))

    return maxSerialNo, maxTarFileSize, timeWait

'''
拼接压缩包文件名
命名规范：
    详单种类(gprs;sms;gsm)_打包序号(0001~9999)_打包开始时间(YYYYMMDDHHmm).tar
'''
def get_package_name(packagePath, recordType, nCount, tmBegin ):
    pattern =  '{0:04d}'
    serialNo = pattern.format(nCount)
    strTmBegin = tmBegin.strftime("%Y%m%d%H%M")    
    packageName = packagePath + "/" + recordType + "_" + serialNo + "_" + strTmBegin + ".tar"
    
    return packageName

mutex = threading.Lock()

def run(conf, recordType):
    print("Process ", recordType, "record thread begin...")

    # 获取详单路径以及压缩包保存路径
    recordPaths = conf.get(recordType, "RECORD_PATH")
    packagePath = conf.get(recordType, "PACKAGE_PATH")

    print("RECORD_PATH: ", recordPaths)
    print("PACKAGE_PATH: ", packagePath)

    if not os.path.exists(packagePath):
        print("The package path is not exist!\n")
        return

    # 支持详单输入路径存在多个目录的情况
    recordPathList = recordPaths.split(';')
    print(recordPathList)

    maxSerialNo, maxTarFileSize, timeWait = read_common_options(conf)
    currPath = os.getcwd()

    for recordPath in recordPathList:
        if not os.path.exists(recordPath):
            print("The record path is not exist!\n")
            return

        recordPath = os.path.join(currPath, recordPath)
        packagePath = os.path.join(currPath, packagePath)
        
        nCount = 0
        nTarFileSize = 0
        # 遍历目录获取文件列表
        for _, _, fileList in os.walk(recordPath):
            tmBegin = datetime.datetime.now()
            packageName = get_package_name(packagePath, recordType, nCount, tmBegin)
            tar = tarfile.open(packageName, 'w:gz')

           
           # 加锁效率太低，所有的耗时操作在加锁的内容中
            mutex.acquire()
            os.chdir(recordPath)
            for fileName in fileList:
                print(recordPath, fileName, "   ", os.path.isfile(fileName))
               
                if os.path.isfile(fileName):
                    if nCount > maxSerialNo:
                        nCount %= maxSerialNo + 1

                    tmTmp = datetime.datetime.now() 
                    nTarFileSize += os.path.getsize(fileName)
                    
                    # 压缩包源文件总量大于最大值或者打包周期已到
                    if nTarFileSize > maxTarFileSize or (tmTmp-tmBegin).seconds >= timeWait:
                        tar.close()
                        
                        nCount += 1
                        nTarFileSize = os.path.getsize(fileName)
                        # 压缩包源文件总量大于最大值但是打包周期未结束，则等待
                        if timeWait - (tmTmp-tmBegin).seconds > 0:
                            time.sleep(timeWait - (tmTmp-tmBegin).seconds)
                        
                        tmBegin = datetime.datetime.now()
                        packageName = get_package_name(packagePath, recordType, nCount, tmBegin)
                        tar = tarfile.open(packageName, 'w:gz') 
                    tar.add(fileName)
                    os.remove(fileName)
                    
            if not tar.closed:
                tar.close()
            os.chdir(currPath)
            mutex.release()

    print("Process ", recordType, "record thread end...\n")        

def main():
    conf = init_config(CONFIG_FILE)
    if -1 == conf:
        print("The config file is not exist!")
        return

    recordTypes = conf.sections()
    print(recordTypes)

    threads = []
    for type in recordTypes: 
        if type != 'COMMON':
            thread = threading.Thread(target=run, args=(conf, type,))
            threads.append(thread)

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
    
