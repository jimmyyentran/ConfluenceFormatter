import re
import sys;

from PythonConfluenceAPI import ConfluenceAPI
from bs4 import BeautifulSoup
from diff_match_patch import diff_match_patch

reload(sys);
sys.setdefaultencoding("utf8")


class ConfluenceFormatter(ConfluenceAPI):
    CQL_TEXT = "text~"
    LINK1 = '<ac:link><ri:page ri:content-title="'
    LINK2 = '"/><ac:plain-text-link-body><![CDATA['
    LINK3 = ']]></ac:plain-text-link-body></ac:link>'

    # Url formats
    VIEW_URL = "viewpage.action?"
    PAGE_URL = "pages/"
    PAGE_ID = "pageId="

    def __init__(self, username, password, uri_base):
        ConfluenceAPI.__init__(self, username, password, uri_base)
        self.uri_base = uri_base if uri_base.endswith('/') else uri_base + "/"
        self.search_words = []
        self.lim = 100
        self.expands = []
        self.response = None
        self.to_be_updated = []
        self.responses = []

    def search(self, word):
        """
        Append search word to list
        :param word: A string of the searched word
        :return: this instance for builder pattern
        """
        self.search_words.append(word)
        return self

    def limit(self, lim):
        """
        Update limit
        :param lim: An integer of returned responses
        :return: this instance for builder pattern
        """
        self.lim = lim
        return self

    def content(self, bool=True):
        """
        Get Page contents. Append "body.storage,version" to CQL expansion query
        :param bool: A boolean to fetch body.view of JSON return
        :return: this instance for builder pattern
        """
        if bool:
            self.expands.append("body.storage,version")
        return self

    def _get_search_words(self):
        """
        Add search words into a single string and format it into CQL format
        :return: A string that is properly formatted
        """
        formatted = ' '.join('{0}'.format(w) for w in self.search_words)
        quote_formatted = self.CQL_TEXT + '"{0}"'.format(formatted)
        return quote_formatted

    # TODO Do preliminary work before returning string
    def _get_expands(self):
        formatted = self.expands[0]
        return formatted

    def _get_limit(self):
        return self.lim

    def execute(self):
        """
        Run the query and save it as an instance field
        :return: json object
        """
        self.response = self.search_content(self._get_search_words(),
                                            expand=self._get_expands(),
                                            limit=self._get_limit())
        return self.response

    def link_modifier(self, search_string, page_location):
        """
        Find a word and link it to the page location. Add to
        list of updated items
        :param search_string: string to be linked
        :param page_location: string of the name of linked page
        :return:
        """
        for response in self.response['results']:
            # copy the response
            response_copy = {'id': response['id'], 'type': response['type'],
                             'title': response['title'], 'version': {}, 'body': {}}
            response_copy['body']['storage'] = {}
            response_copy['body']['storage']['representation'] = response['body']['storage'][
                'representation']
            response_copy['body']['storage']['value'] = response['body']['storage']['value']
            response_copy['version']['number'] = response['version']['number'] + 1
            response_body = response_copy['body']['storage']['value']

            bs = BeautifulSoup(response_body, "html.parser")
            matches = bs.findAll(text=re.compile(r'\b' + search_string + r'\b'))

            if not matches:
                return

            for match in matches:
                # check if part of a link
                if match.parent.parent.name == "ac:link":
                    match.parent.previous_sibling['ri:content-title'] = page_location
                else:
                    substituted = re.sub(r'\b' + search_string + r'\b',
                                         self.LINK1 + page_location + self.LINK2 +
                                         search_string + self.LINK3, match)
                    match.replaceWith(BeautifulSoup(substituted, "html.parser"))

            # do replacement
            response_copy['body']['storage']['value'] = bs.encode('utf-8')
            self.to_be_updated.append(response_copy)
            self.responses.append(response)

    def get_updated(self):
        return self.to_be_updated

    def update(self, step):
        """
        Loop through updated items and POST to server
        :return:
        """
        for page in self.to_be_updated:
            if step:
                html = self.uri_base + self.PAGE_URL + self.VIEW_URL + self.PAGE_ID + page['id']
                choice = raw_input("Updating: {}\n{}\nUpdate changes? 'y' for yes".
                                   format(page['title'], html)).lower()
                if choice != 'y':
                    continue
            self.update_content_by_id(page, page['id'])

    def link(self, word, pageLoc, verify=False, step=True):
        """
        Links word to page
        :type word: string
        :param word:
        :param verify:
        :param pageLoc: (string) name of the page
        :return:
        """
        self.search(word).content(True)
        self.execute()
        self.link_modifier(word, pageLoc)
        if verify:
            dmp = diff_match_patch()
            html = """<!DOCTYPE html>
                    <html lang="en">
                    <head>
                    <meta charset="UTF-8">
                    <title>Title</title>
                    </head>
                    <body>"""
            for i in range(len(self.to_be_updated)):
                html += "<h1>" + "Title: {}".format(self.to_be_updated[i]['title']) + "</h1>"
                diffs = dmp.diff_main(self.responses[i]['body']['storage']['value'].decode(
                    'utf-8'), self.to_be_updated[i]['body']['storage']['value'].decode(
                    'utf-8'))
                dmp.diff_cleanupSemantic(diffs)
                html_snippet = dmp.diff_prettyHtml(diffs)
                html += html_snippet

            html += "</body></html>"
            import datetime
            with open("link_" + word + "_to_" + pageLoc + str(datetime.datetime.now()) +
                              ".html", 'w') as file:
                file.write(html)
        else:
            self.update(step)
