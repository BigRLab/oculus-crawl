# oculus-crawl
OculusCrawl project aimed to perform automatic crawl on search engines based on some criteria. It is scalable and service-based. Currently, it is supported Google Images, Yahoo Images, Bing Images, Flickr and Microsoft HowOld as search engines, on top of HTTP transport protocol.

![alt text][logo]

[logo]: https://github.com/ipazc/oculus-crawl/blob/master/oculus-crawl.jpeg "Oculus Crawl tool."

# Requirements
It is required Ubuntu >= 14.04 or Debian >= 8 Jessie with Selenium framework, Firefox and its selenium drivers.


# Installation
The following pip packages must be installed: pyvirtualdisplay selenium beautifulsoup4:
```bash
sudo pip3 install pyvirtualdisplay selenium beautifulsoup4
```

# Usage
## Launch the factory in a well-known publicly-available machine that has port TCP 24005 exposed to the internet.
```bash
python3 -m factory
```

## Launch as many crawlers as you want in any computer, even behnid NATs.
```bash
python3 -m crawler
```

## [In-progress] Modify the extcli in order to change the terms used to generate the dataset. 
Note that this project was used to generate a complete aging dataset --including minors--, that state-of-the-art aging datasets lack of, and that is the reason for the example terms used in the search.
Change them accordingly to your problem.
Launch it to create a dataset request and wait until the process finishes:
```bash
python3 -m extcli
```

The resultant dataset is going to appear zipped in the machine that launched the factory.
