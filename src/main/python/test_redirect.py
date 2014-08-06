import urllib2
import urlparse

url = 'http://dx.doi.org/10.1080%2F14736480490443085'
urlinfo = urlparse.urlparse(url)

#request = urllib2.Request(url, headers=headers)
request = urllib2.Request(url)
opener1 = urllib2.HTTPRedirectHandler()
opener2 = urllib2.HTTPCookieProcessor()
opener3 = urllib2.build_opener(opener2, opener1)
opener3.addheaders = [
    ('User-agent' , 'Mozilla/5.0'),
    ('Host' , urlinfo.netloc)
]
response = opener3.open(request, timeout=20.0)
print response.read()