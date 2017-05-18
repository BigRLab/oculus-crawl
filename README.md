# oculus-crawl
OculusCrawl project aimed to perform automatic crawl of resources (like images) on search engines based on some criteria. It is scalable and service-based. Even though it is expected to support many resources, currently (May-2017) it only supports images under the search engines Google Images, Yahoo Images, Bing Images[experimental], Flickr[experimental] and Microsoft HowOld[experimental], on top of HTTP transport protocol.

It is entirely built in python3, with support for python3.4+. 

![alt text][logo]

[logo]: https://github.com/ipazc/oculus-crawl/blob/master/oculus-crawl.jpeg "Oculus Crawl tool."

# Architecture

It is composed by 3 elements: a factory for datasets, crawlers and an external client.

 * Factory: exports an API-Rest for creating and managing datasets.
 * Crawler: crawls on search engines for filling up a dataset. Requires connectivity with the factory.
 * Client (ocrawl): requests a dataset based on some keywords to the factory and tracks its creation progress. Requires connectivity with the factory.

Note that only the factory is needed to be in a well-known host and port in order to create a dataset.

# Usage

It is highly encouraged to install [Docker](https://www.docker.com/) prior testing this software, as there are images in the dockerhub ready with all the dependencies fixed. You can build your own images for Oculus-Crawl by using the `dockerfiles` listed under the `docker` folder.

## How to make it work

**NOTE:** If you want a direct working and easy-to-test example, go to the [examples section](#examples).

1. **On a well-known machine, run the factory.**

```bash
$ docker run -ti --rm --name o-factory -v ${LOCAL_DATASETS_FOLDER}:/datasets -p ${EXTENRAL_HOST}:${EXTERNAL_PORT}:24005 dkmivan/oculus-crawl factory 0.0.0.0 -d /datasets/
```
This will start up the factory server on the host `${EXTERNAL_HOST}` and port `${EXTERNAL_PORT}` of the well-known machine. Note that it is an HTTP server exporting an API-REST on the specified `${EXTERNAL_HOST}:${EXTERNAL_PORT}` and it must be accessible by the crawlers and the ocrawl client. 
When a dataset is successfully built, it will be hosted under the folder specified in `${LOCAL_DATASETS_FOLDER}`. 


2. **On any number of machines, run as many crawlers as needed. They can be behind NATs, but they must have connectivity with the factory.**

```bash
$ docker run -ti --rm --name o-crawler dkmivan/oculus-crawl crawler http://${EXTENRAL_HOST}:${EXTERNAL_PORT} -w ${NUM_WORKERS}
```

This will start the crawler in the machine with as many workers as `${NUM_WORKERS}`. It is encouraged to use a low number of workers or even work with only 1, as it causes a lot of overhead due to the usage of a native browser wrapped with selenium webdrivers. Replace the `http://${EXTENRAL_HOST}:${EXTERNAL_PORT}` with the URL of the API-REST that the factory is exporting.


3. **On any computer, execute the ocrawl client to request a new dataset.**

```bash
$ docker run -ti --rm --name o-crawler -v ${LOCAL_BACKUPS_FOLDER}:/backups dkmivan/oculus-crawl ocrawl http://${EXTENRAL_HOST}:${EXTERNAL_PORT} -n ${DATASET_NAME} -s '${SEARCH_KEYWORDS}:["${ADJETIVE1}", "${ADJETIVE2}", ...]' -s '${SEARCH_KEYWORDS2}:[...] -b /backups/ -t ${BACKUP_INTERVAL_IN_SECONDS} '
```

This command will execute the client, which will request the creation of a dataset of name `${DATASET_NAME}` to the factory located at `http://${EXTENRAL_HOST}:${EXTERNAL_PORT}`. The dataset will consist of the search keywords specified at `${SEARCH_KEYWORDS}` (spaces allowed) + combination of adjetives specified at `["${ADJETIVE1}", "${ADJETIVE2}", ...]`. Each `${BACKUP_INTERVAL_IN_SECONDS}` seconds the search session will be saved and dumped inside your local folder `${LOCAL_BACKUPS_FOLDER}`. Note that the search session backup is enough to build the entire dataset again by injecting it to a existing search session of any factory, without the need of any crawler; even though this functionality is not accessible, it exists in the code and will be interfaced in the future.

## Examples

The following example gives the three roles (factory, crawler and client) to a single machine with Docker; however it can be easily finetuned by changing the hosts addresses to run spread in distributed systems. 

As a clarification if you are not familiar with docker, the `docker run` command will download (only the first time) the latest image of Oculus-Crawl from my repository at https://hub.docker.com/r/dkmivan/oculus-crawl/tags/ and run each application containerized. Thus, you don't need to perform any prior set-up on your machine to make this example work, just ensure to have docker installed. You can learn more about docker [here](https://docs.docker.com/get-started/).

### Create a dataset of cats 

```bash
# Ensure that $HOME/datasets and $HOME/dataset/backups exists
DATASETS_FOLDER="${HOME}/datasets"
BACKUPS_FOLDER="${DATASETS_FOLDER}/backups"

mkdir -p "${BACKUPS_FOLDER}"

# 1. Run the factory on background and bind it to the local net interface from docker (172.17.0.1:24005).
docker run -ti -d --rm --name o-factory -v "${DATASETS_FOLDER}":/datasets -p 172.17.0.1:24005:24005 dkmivan/oculus-crawl factory 0.0.0.0 -d /datasets/

# 2. Run the crawler on background with one worker
docker run -ti -d --rm --name o-crawler dkmivan/oculus-crawl crawler http://172.17.0.1:24005 -w 1

# 3. Run the client in foreground to request the creation of the cats dataset and track its creation progress.
docker run -ti --rm --name o-crawl -v "${BACKUPS_FOLDER}":/backups dkmivan/oculus-crawl ocrawl http://172.17.0.1:24005 -n "cats_dataset_example" -s 'cat:["small", "cute"]' -b /backups/ -t 1
```

Track the process on the terminal until it is finished. The dataset will be available at your "${HOME}/datasets" folder.

![alt text][terminal result]

[terminal result]: https://github.com/ipazc/oculus-crawl/blob/master/ocrawl-client.jpeg "Oculus Crawl tool client output."

## Results

When the process finishes, a zipped dataset is released in the folder you specified. For the example of a dataset of cats with only two adjetives (small and cute) and a single crawler, it took ~5 minutes, crawled a total of 2208 pictures with an overall size of ~500 MB zipped:

![alt text][folder result1]

[folder result1]: https://github.com/ipazc/oculus-crawl/blob/master/ocrawl-result-folder1.jpeg "Oculus Crawl result."

The content of the zip file is as follows:

![alt text][folder result2]

[folder result2]: https://github.com/ipazc/oculus-crawl/blob/master/ocrawl-result-folder2.jpeg "Oculus Crawl result zip content."

An overview of the images:

![alt text][folder result3]

[folder result3]: https://github.com/ipazc/oculus-crawl/blob/master/ocrawl-result-folder3.jpeg "Oculus Crawl result zip content."

## Structure of the metadata

Oculus-crawl generates a single metadata file in JSON format describing each of the elements from the dataset. A sample of this metadata, extracted from the example of the cats dataset is:

```json
{
    "data": {
        "00320b035c4b6f99dffd436592fb7ee4": {
            "metadata": {
                "desc": "<b>Small</b> <b>Cat</b> Enclosure;",
                "extension": ".jpeg",
                "height": "480",
                "searchwords": [
                    "cat small"
                ],
                "source": [
                    "yahoo"
                ],
                "uri": [
                    "yahoo/927.jpeg"
                ],
                "url": [
                    "http://www.wendallcat.com/images/small_enclosureLg.jpg"
                ],
                "width": "640"
            }
        },
        "0067fcd6acaa3a5c97ec9af6f19d21fe": {
            "metadata": {
                "desc": "box, <b>cat, cute</b>, hahaha, kitty, maru - image #49308 on Favim.com;",
                "extension": ".jpeg",
                "height": "563",
```

Each picture is hashed by its MD5HASH, which serves as the key for its metadata content. For each picture, it is recorded a small description provided by the search engine, the extension of the element, the size (width, height), the source (it can be pointed by multiple search engines), the URI where it is stored relative to the dataset root dir, the URL(s) where it can be found and the searchwords used to retrieve it.

Note that there is also a session file along with this file, which can be used to re-fetch all the elements and recreate the dataset again without the need to crawl.


# Manual installation
TBD

# LICENSE
This project is released under the [GNU GPL v3 License](https://github.com/ipazc/oculus-crawl/blob/master/LICENSE).
