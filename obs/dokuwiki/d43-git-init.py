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
#  Requires PyGithub.

import os
import sys
import codecs
sys.path.append('/var/www/vhosts/door43.org/tools/general_tools')
try:
    from git_wrapper import *
except:
    print "Please verify that"
    print "/var/www/vhosts/door43.org/tools/general_tools exists."
    sys.exit(1)


readme = u'''
Door43 Pages: {0}
==========

*Raw DokuWiki exports from door43.org for {0}*

http://door43.org

Created by Distant Shores Media (http://distantshores.org) and the Door43 world missions community (http://door43.org).


License
==========

This work is made available under a Creative Commons Attribution-ShareAlike 4.0 International License (http://creativecommons.org/licenses/by-sa/4.0/).

You are free:

* Share — copy and redistribute the material in any medium or format
* Adapt — remix, transform, and build upon the material for any purpose, even commercially.

Under the following conditions:

* Attribution — You must attribute the work as follows: "Original work available at http://door43.org." Attribution statements in derivative works should not in any way suggest that we endorse you or your use of this work.
* ShareAlike — If you remix, transform, or build upon the material, you must distribute your contributions under the same license as the original.
'''


def writePage(outfile, contents):
    f = codecs.open(outfile, 'w', encoding='utf-8')
    f.write(contents)
    f.close()


if __name__ == '__main__':
    # Check arguments
    if len(sys.argv) > 1:
        d = sys.argv[1].strip()
        if not os.path.exists(d):
            print "Directory not found {0}".format(d)
            sys.exit(1)
    else:
        print "Please specify directory name"
        sys.exit(1)

    # Log in to Github via API
    try:
        githuborg = getGithubOrg('door43')
    except:
        print 'Could not login to Github'
        sys.exit(1)

    # Create git repo and push to Github
    lang = d.rpartition('/')[2]
    writePage(os.path.join(d, 'README.md'), readme.format(lang))
    gitCreate(d)
    name = 'dw-{0}'.format(lang)
    desc = 'Door43 DokuWiki Pages for {0}'.format(lang)
    url = 'http://door43.org/{0}/'.format(lang)
    githubCreate(d, name, desc, url, githuborg)
    gitCommit(d, 'Initial namespace creation.')
    gitPush(d)