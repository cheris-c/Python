#获取上交所和深交所所有股票的名称和交易信息

import requests
from bs4 import BeautifulSoup
import traceback
import re

def getHTMLText(url):
      try:
            r = requests.get(url, timeout = 30)
            r.raise_for_status()
            r.encoding = r.apparent_encoding

            return r.text
      except:
            return ""
            
def getStockList(lst, stockURL):
      html = getHTMLText(stockURL)
      soup = BeautifulSoup(html, "html.parser")
      a = soup.find_all('a')
      for i in a:
            try:
                  href = i.attrs['href']
                  lst.append(re.findall(r"[s][zh]\d{6}", href)[0])
            except:
                  continue


def getStockInfo(lst, stockURL, fpath):
      for stock in lst:
            url = stockURL + stock + ".html"
            html = getHTMLText(url)
            try:
                  if html=="":
                        continue
                  infoDict = {}
                  soup = BeautifulSoup(html, 'html.parser')
                  stockInfo = soup.find('div', attrs={'class': 'stock-bets'})

                  name = stockInfo.find_all(attrs={'class': 'bets-name'})[0]
                  print(name)
                  infoDict.update({'股票名称': name.text.split()[0]})

                  keyList = stockInfo.find_all('dt')
                  valueList = stockInfo.find_all('dd')

                  for i in range(len(keyList)):
                        key = keyList[i].text
                        val = valueList[i].text
                        infoDict[key] = val

                  with open(fpath, 'a', encoding='utf-8') as f:
                        f.write(str(infoDict) + '\n')

            except:
                  traceback.print_exc()
                  continue
                  

def main():
      stock_list_url = 'http://quote.eastmoney.com/stocklist.html'
      stock_info_url = 'https://gupiao.baidu.com/stock/'
      output_file = 'D://BaiduStockInfo.txt'
      slist = []
      getStockList(slist, stock_list_url)
      getStockInfo(slist, stock_info_url, output_file)
      print('ok')

main()

