import httpx
import ipaddress
from bs4 import BeautifulSoup
from datetime import datetime

class IPv4:
    def __init__(self, start, count):
        self.address = ipaddress.IPv4Address(start)
        self.count = count

    def __repr__(self):
        return str(self.address)

    def __add__(self, other):
        return IPv4(self, self.count + other.count)

    def __lt__(self, other):
        return int(self.address) < int(other.address)

    def CIDR(self):
        first = self.address
        last = self.address + self.count - 1
        t = list(ipaddress.summarize_address_range(first, last))
        return [ net.with_prefixlen for net in t ]

class IPv6:
    def __init__(self, start, count):
        self.address = ipaddress.IPv6Address(start)
        self.network = ipaddress.IPv6Network(f'{start}/{count}')

    def __repr__(self):
        return self.network.with_prefixlen

    def __lt__(self, other):
        return int(self.address) < int(other.address)

def getHTML(url):
    r = httpx.Client(http2=True, verify=False).get(url)

    assert r.status_code == 200

    return r.content

def parseHTML(content):
    html = BeautifulSoup(content, 'html.parser')

    ips = [ 
        IPv4(ip, int(count) << 8)
        for trs in html.find_all('tr')[1:] 
        if (tds := trs.find_all('td'))
        if (ip := tds[3].text, count := int(tds[4].text))
        if (ip := ip.partition(' ')[0])
    ]

    return sorted(ips)

def parseHTMLv6(content):
    html = BeautifulSoup(content, 'html.parser')

    ips = [
        IPv6(ip, int(count))
        for trs in html.find_all('tr')[1:]
        if (tds := trs.find_all('td'))
        if (ip := tds[3].text, count := int(tds[4].text))
    ]

    return sorted(ips)

def minifyIPs(ips: list):
    idx = 0

    while (idx < len(ips) - 1):
        r1: IPv4 = ips[idx]
        r2: IPv4 = ips[idx + 1]

        if r1.address + r1.count == r2.address:
            ips.remove(r1)
            ips[idx] = r1 + r2
            continue

        idx += 1
    
    return ips

if __name__ == '__main__':

    v4 = getHTML('https://rms.twnic.tw/help_ipv4_assign.php')
    v6 = getHTML('https://rms.twnic.tw/help_ipv6_assign.php')

    ips = parseHTML(v4)
    ips = minifyIPs(ips)

    cidrs = [ cidr for ip in ips for cidr in ip.CIDR() ]
    ipv4 = '\n'.join(cidrs)

    with open('TWNIC_IPv4.txt', 'w+', encoding='utf-8') as f:
        f.write(ipv4)

    ips = parseHTMLv6(v6)

    cidrs = [ str(cidr) for cidr in ips ]
    ipv6 = '\n'.join(cidrs)

    with open('TWNIC_IPv6.txt', 'w+', encoding='utf-8') as f:
        f.write(ipv6)

    raw = 'https://raw.githubusercontent.com/sabpprook/TWNIC_CIDR/master'

    with open('README.md', 'w+', encoding='utf-8') as f:
        today = datetime.today().strftime('%Y-%m-%d')

        f.write(f'# TWNIC CIDR\n### 更新日期: {today}\n')

        f.write(f'## IPv4\n```{raw}/TWNIC_IPv4.txt```\n')
        f.write(f'## IPv6\n```{raw}/TWNIC_IPv6.txt```\n')
