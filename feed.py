from xml.dom import minidom
from XmlElement import XmlElement as X
from db import Podcast, get_config


def get_feed(username, podcast: dict):
    config = get_config()
    cList = []
    for c in podcast.get('category'):
        cList.append(X('itunes:category', {'text': c}))

    port = ''
    if config['port_in_url']:
        port = ":" + str(config['port'])

    itemList = []
    for item in podcast.get('items'):
        itemList.append(
            X('item', s=[
                X('title', t=item['title']),
                X('description', t=item['description']),
                X('pubDate', t=item['pub_date']),
                X('media:content', {'type': 'audio/mpeg',
                                    'url': config['protocol'] + '://' + config['hostname'] + port
                                           + '/podcast/episode/' + item['enclosure']}),
                X('itunes:explicit', t=item['explicit']),
                X('itunes:image', {'href': config['protocol'] + '://' + config['hostname'] + port
                                           + '/podcast/image/' + item['image']}),
                X('itunes:keywords', t=','.join(item['keywords']))
            ])
        )

    feed = X('rss', {
        'xmlns:media': "http://search.yahoo.com/mrss/",
        'xmlns:itunes': "http://www.itunes.com/dtds/podcast-1.0.dtd",
        'xmlns:dcterms': "http://purl.org/dc/terms/",
        'xmlns:spotify': "http://www.spotify.com/ns/rss",
        'xmlns:psc': "http://podlove.org/simple-chapters/",
        'version': "2.0"
    }, s=[
        X('channel', s=[
            X('title', t=podcast['title']),
            X('description', t=podcast['description']),
            X('link', t=podcast['link']),
            X('language', t=podcast['language']),
            X('itunes:author', t=podcast['author']),
            X('itunes:image', {'href': config['protocol'] + '://' + config['hostname'] + port
                                           + '/podcast/image/' +  podcast['image']}),
            X('itunes:explicit', t=podcast['explicit']),
            X('itunes:category', s=cList),
            X('itunes:type', t=podcast['type']),
            X('items', s=itemList)
        ])
    ])

    return minidom.parseString(feed.to_string()).toprettyxml()


if __name__ == '__main__':
    pod = Podcast("Space Junkies",
                  "http://localhost:5000/",
                  "Many lines of moon sand",
                  "de",
                  "The Astronaut",
                  "09-image.png",
                  "clean",
                  ['Tech', 'Nature'])
    get_feed(pod.__dict__)
