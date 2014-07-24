#!/usr/bin/env python
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>
#
#  Requires PyGithub for unfoldingWord export.

import os
import re
import sys
import json
import codecs
import shlex
import datetime
from subprocess import *


root = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo'
pages = os.path.join(root, 'pages')
uwadmindir = os.path.join(pages, 'en/uwadmin')
exportdir = os.path.join(root, 'media/exports')
unfoldingWorddir = '/var/www/vhosts/api.unfoldingword.org/httpdocs/obs/txt/1/'
digits = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')
rtl = ['he', 'ar', 'fa']
langnames = os.path.join('/var/www/vhosts/door43.org',
                        'httpdocs/lib/plugins/translation/lang/langnames.txt')
readme = u'''
unfoldingWord | Open Bible Stories
==================================

*an unrestricted visual mini-Bible in any language*

http://unfoldingword.org/

Created by Distant Shores Media (http://distantshores.org) and the Door43 world missions community (http://door43.org).


License
=======

This work is made available under a Creative Commons Attribution-ShareAlike 3.0 Unported License (http://creativecommons.org/licenses/by-sa/3.0).

You are free:

* to Share— to copy, distribute and transmit the work
* to Remix — to adapt the work
* to make commercial use of the work

Under the following conditions:

* Attribution — You must attribute the work as follows: "Original work available at www.openbiblestories.com." Attribution statements in derivative works should not in any way suggest that we endorse you or your use of this work.
* ShareAlike — If you alter, transform, or build upon this work, you may distribute the resulting work only under the same or similar license to this one.

Use of trademarks: unfoldingWord is a trademark of Distant Shores Media and may not be included on any derivative works created from this content.  Unaltered content from http://openbiblestories.com must include the unfoldingWord logo when distributed to others. But if you alter the content in any way, you must remove the unfoldingWord logo before distributing your work.

Attribution of artwork: All images used in these stories are © Sweet Publishing (www.sweetpublishing.com) and are made available under a Creative Commons Attribution-Share Alike License (http://creativecommons.org/licenses/by-sa/3.0).
'''
# Regexes for splitting the chapter into components
titlere = re.compile(ur'======.*', re.UNICODE)
refre = re.compile(ur'//.*//', re.UNICODE)
framere = re.compile(ur'{{[^{]*', re.DOTALL | re.UNICODE)
fridre =  re.compile(ur'[0-5][0-9]-[0-9][0-9]', re.UNICODE)


def getChapter(chapterpath, jsonchapter):
    chapter = codecs.open(chapterpath, 'r', encoding='utf-8').read()
    # Get title for chapter
    title = titlere.search(chapter)
    if title:
        jsonchapter['title'] = title.group(0).replace('=', '').strip()
    else:
        jsonchapter['title'] = u'NOT FOUND'
        print u'NOT FOUND: title in {0}'.format(chapterpath)
    # Get reference for chapter
    ref = refre.search(chapter)
    if ref:
        jsonchapter['ref'] = ref.group(0).replace('/', '').strip()
    else:
        jsonchapter['ref'] = u'NOT FOUND'
        print u'NOT FOUND: reference in {0}'.format(chapterpath)
    # Get the frames
    for fr in framere.findall(chapter):
        frlines = fr.split('\n')
        frse = fridre.search(fr)
        if frse:
            frid = frse.group(0)
        else:
            frid = u'NOT FOUND'
            print u'NOT FOUND: frame id in {0}'.format(chapterpath)
        frame = { 'id': frid,
                  'img': frlines[0].strip(),
                  'text': u''.join([x for x in frlines[1:] if u'//' not in x]
                                                                    ).strip()
                }
        jsonchapter['frames'].append(frame)
    # Sort frames
    jsonchapter['frames'].sort(key=lambda frame: frame['id'])
    return jsonchapter

def writePage(outfile, p):
    makeDir(outfile.rpartition('/')[0])
    f = codecs.open(outfile.replace('.txt', '.json'), 'w', encoding='utf-8')
    f.write(p)
    f.close()

def makeDir(d):
    if not os.path.exists(d):
        os.makedirs(d, 0755)

def getDump(j):
    return json.dumps(j, sort_keys=True, indent=2)

def loadJSON(f, t):
    if os.path.isfile(f):
        return json.load(open(f, 'r'))
    if t == 'd':
      return json.loads('{}')
    else:
      return json.loads('[]')

def loadLangStrings(path):
    langdict = {}
    if not os.path.isfile(path):
        return langdict
    for line in codecs.open(path, 'r', encoding='utf-8').readlines():
        if ( line.startswith(u'#') or line.startswith(u'\n')
                                                  or line.startswith(u'\r') ):
            continue
        code,string = line.split(None, 1)
        langdict[code.strip()] = string.strip()
    return langdict

def getJSONDict(statfile):
    status = {}
    if os.path.isfile(statfile):
        for line in open(statfile):
            if ( line.startswith('#') or line.startswith('\n')
                                                         or ':' not in line ):
                continue
            k, v = line.split(':')
            status[k.strip().lower().replace(' ', '_')] = v.strip()
    return status

def exportunfoldingWord(status, gitdir, json, lang, githuborg):
    '''
    Exports JSON data for each language into its own Github repo.
    '''
    makeDir(gitdir)
    writePage(os.path.join(gitdir, 'obs-{0}.json'.format(lang)), json)
    statjson = getDump(status)
    writePage(os.path.join(gitdir, 'status-{0}.json'.format(lang)), statjson)
    writePage(os.path.join(gitdir, 'README.md'), readme)
    gitCreate(gitdir)
    githubCreate(gitdir, lang, githuborg)
    commitmsg = str(status)
    if 'comments' in status:
        commitmsg = status['comments']
    gitCommit(gitdir, commitmsg)
    gitPush(gitdir)

def gitCreate(d):
    '''
    Creates local GIT repo and pushes to Github.
    '''
    if os.path.exists(os.path.join(d, '.git')):
        return
    os.chdir(d)
    out, ret = runCommand('git init .')
    if ret > 0:
        print 'Failed to create a GIT repo in: {0}'.format(d)
        sys.exit(1)

def githubCreate(d, lang, org):
    '''
    Creates a Github repo for lang unless it already exists.
    '''
    rname = 'obs-{0}'.format(lang)
    try:
        repo = org.get_repo(rname)
        return
    except GithubException:
        try:
            repo = org.create_repo(rname,
                            'Open Bible Stories for {0}'.format(lang),
                            'http://unfoldingword.org/{0}/'.format(lang),
                            has_issues=False,
                            has_wiki=False,
                            auto_init=False,
                            )
        except GithubException as ghe:
            print(ghe)
            return
    os.chdir(d)
    out, ret = runCommand('git remote add origin {0}'.format(repo.ssh_url))
    if ret > 0:
        print 'Failed to add Github remote to repo in: {0}'.format(d)

def gitCommit(d, msg):
    '''
    Adds all files in d and commits with message m.
    '''
    os.chdir(d)
    out, ret = runCommand('git add *')
    out1, ret1= runCommand('''git commit -am '{0}' '''.format(msg))
    if ret > 0 or ret1 > 0:
        print 'Nothing to commit, or failed commit to repo in: {0}'.format(d)
        print out1

def gitPush(d):
    '''
    Pushes local repository to github.
    '''
    os.chdir(d)
    out, ret = runCommand('git push origin master')
    if ret > 0:
        print out
        print 'Failed to push repo to Github in: {0}'.format(d)

def runCommand(c):
    command = shlex.split(c)
    com = Popen(command, shell=False, stdout=PIPE, stderr=PIPE)
    comout = ''.join(com.communicate()).strip()
    return comout, com.returncode

def getGithubOrg(orgname):
    user = raw_input('Github username: ').strip()
    pw = raw_input('Github password: ').strip()
    g = Github(user, pw)
    return g.get_organization(orgname)


if __name__ == '__main__':
    unfoldingwordexport = False
    if len(sys.argv) > 1:
        if sys.argv[1] == '--unfoldingwordexport':
            try:
                from github import Github
                from github import GithubException
            except:
                print "Please install PyGithub with pip"
                sys.exit(1)
            unfoldingwordexport = True
            try:
                githuborg = getGithubOrg('unfoldingword')
            except:
                print 'Could not login to Github'
                sys.exit(1)
        else:
            print 'Unknown argument: {0}'.format(sys.argv[1])
    today = ''.join(str(datetime.date.today()).rsplit('-')[0:3])
    langdict = loadLangStrings(langnames)
    uwcatpath = os.path.join(unfoldingWorddir, 'obs-catalog.json')
    uwcatalog = loadJSON(uwcatpath, 'l')
    uwcatlangs = [x['language'] for x in uwcatalog]
    catpath = os.path.join(exportdir, 'obs-catalog.json')
    catalog = loadJSON(catpath, 'l')
    for lang in os.listdir(pages):
        if ( os.path.isfile(os.path.join(pages, lang)) or
             'obs' not in os.listdir(os.path.join(pages, lang)) ):
            continue
        app_words = getJSONDict(os.path.join(pages, lang, 'obs/app_words.txt'))
        langdirection = 'ltr'
        if lang in rtl:
            langdirection = 'rtl'
        jsonlang = { 'language': lang,
                     'direction': langdirection,
                     'chapters': [],
                     'app_words': app_words,
                     'date_modified': today,
                   }
        for page in os.listdir(os.path.join(pages, lang, 'obs')):
            if not page.startswith(digits): continue
            jsonchapter = { 'number': page.split('-')[0],
                            'frames': [],
                          }
            chapterpath = os.path.join(pages, lang, 'obs', page)
            jsonlang['chapters'].append(getChapter(chapterpath, jsonchapter))
        jsonlang['chapters'].sort(key=lambda frame: frame['number'])
        jsonlangfilepath = os.path.join(exportdir, lang, 'obs',
                                            'obs-{0}.json'.format(lang))
        prevjsonlang = loadJSON(jsonlangfilepath, 'd')
        curjson = getDump(jsonlang)
        prevjson = getDump(prevjsonlang)
        try:
            langstr = langdict[lang]
        except KeyError:
            print "Configuration for language {0} missing in {1}.".format(lang,
                                                                     langnames)
            continue
        status = getJSONDict(os.path.join(uwadmindir, lang, 'obs/status.txt'))
        langcat =  { 'language': lang,
                     'string': langstr,
                     'direction': langdirection,
                     'date_modified': today,
                     'status': status,
                   }
        if not lang in [x['language'] for x in catalog]:
            catalog.append(langcat)
        # Maybe fix this to do a full string comparison
        if len(str(curjson)) != len(str(prevjson)):
            ( [x for x in catalog if x['language'] ==
                                            lang][0]['date_modified']) = today
            writePage(jsonlangfilepath, curjson)
        if unfoldingwordexport:
            unfoldingWordlangdir = os.path.join(unfoldingWorddir, lang)
            if status.has_key('checking_level') and status.has_key(
                                                              'publish_date'):
                if ( status['checking_level'] in ['1', '2', '3'] and 
                       status['publish_date'] == str(datetime.date.today()) ):
                    print "=========="
                    if 'NOT FOUND.' in curjson:
                        print ('==> !! Cannot export {0}, invalid JSON format'
                                                               .format(lang))
                        print "=========="
                        continue
                    print "---> Exporting to unfoldingWord: {0}".format(lang)
                    exportunfoldingWord(status, unfoldingWordlangdir, curjson,
                                                              lang, githuborg)
                    if lang in uwcatlangs:
                        uwcatalog.pop(uwcatlangs.index(lang))
                    uwcatalog.append(langcat)
                    print "=========="
    catjson = getDump(catalog)
    writePage(catpath, catjson)
    if unfoldingwordexport:
        uwcatjson = getDump(uwcatalog)
        writePage(uwcatpath, uwcatjson)