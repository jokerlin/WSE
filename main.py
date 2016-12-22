import os
import diff_match_patch
import math
import json
import authorship_attribution
import re


# "Reverse engineering"
PAGE_ID = '18935488'

# PARAMETERS
C_SCALE = 13.08         # > 0
C_TEXT = 0.6            # [0, 1]
C_LEN = 0.6             # [0, 1]
C_SLACK = 2.20          # >= 1
C_PUNISH = 19.09        # >= 1
C_MAXREP = 22026        # MAX VALUE OF REPUTATION
C_TIMESTAMP = 1         # >= 1
CONTINIOUS_TOKEN = 4    # for authorship tracking

# DEBUG
max_rep_list = set()

# class of wiki
class WikiRevision(object):
    def __init__(self):
        self.timestamp = ""
        self.user = ""
        self.revid = 0
        self.parentid = 0
        self.comment = ""
        self.content = ""


# read json file to WikiRevision object
def read_json():
    wiki_list = []
    filename_list = os.listdir('./store')
    if '.DS_Store' in filename_list:
        filename_list.remove('.DS_Store')
    # read json to Wiki Structure
    for filename in filename_list:
        f = open('./store/' + filename,'r')
        json_dict = json.loads(f.readline())
        wiki_obj = WikiRevision()
        wiki_obj.timestamp = json_dict['query']['pages'][PAGE_ID]['revisions'][0]['timestamp']
        wiki_obj.user = json_dict['query']['pages'][PAGE_ID]['revisions'][0]['user']
        wiki_obj.revid = json_dict['query']['pages'][PAGE_ID]['revisions'][0]['revid']
        wiki_obj.parentid = json_dict['query']['pages'][PAGE_ID]['revisions'][0]['parentid']
        wiki_obj.comment = json_dict['query']['pages'][PAGE_ID]['revisions'][0]['comment']
        wiki_obj.content = json_dict['query']['pages'][PAGE_ID]['revisions'][0]["*"]
        wiki_list.append(wiki_obj)
    # sort wiki list
    wiki_list.sort(key=lambda x: int(x.revid))
    # insert initial blank content
    initial_obj = WikiRevision()
    wiki_list.insert(0, initial_obj)
    return wiki_list


# filtering the versions, keeping only the last of consecutive versions by the same author
def pre_processing(wiki_list):
    i = 0
    while i < len(wiki_list)-1:
        if wiki_list[i].user == wiki_list[i + 1].user:
            # print 'before:'+str(i)
            wiki_list.pop(i)
            # print 'after:'+str(i)
        else:
            i += 1
    return wiki_list


# txt(i,j): the amount of new text added by r[i] that is still present in v[j]
# Specially, txt(i,i) is the amount of new text added by r[i]
def txt(i, j):
    diff = diff_match_patch.diff_match_patch()
    diffs = diff.diff_main(i, j, True)
    diff.diff_cleanupSemantic(diffs)
    result = 0
    for edit in diffs:
        if edit[0] == diff.DIFF_INSERT:
            result += len(edit[1].split(' '))
    return result


# edit distance between v[i] and v[j], measuring how much change(word additions,deletions,replacements, displacements)
# Currently using Levenshtein Distance
def d(i, j):
    diff = diff_match_patch.diff_match_patch()
    diffs = diff.diff_main(i, j, True)
    return diff.diff_levenshtein(diffs)


def authorship_calculate(i, j, l):
    a = authorship_attribution.AuthorshipAttribution.new_attribution_processor(N=CONTINIOUS_TOKEN)
    for k in range(i - 1, j + 1):
        a.add_revision(l[k].content.split(), revision_info=l[k].user)
    result = a.get_attribution()
    return result.count(l[i].user)


# reputation update due to text survival
# r is NOT DEFINED YET
def rule_1(i, j, l, r):
    # DEBUG
    # print math.log10(1 + r)
    # print l[i].revid, l[j].revid
    # print authorship_calculate(i, j, l)
    # print txt(l[i - 1].content, l[i].content)

    if l[i].user == l[j].user or txt(l[i - 1].content, l[i].content) == 0:
        return 0
    return C_SCALE * C_TEXT * authorship_calculate(i, j, l) / txt(l[i - 1].content, l[i].content) \
        * pow(txt(l[i - 1].content, l[i].content), C_LEN) \
        * math.log10(1 + r[l[j].user])


# reputation update due to edit survival
# v is NOT DEFINED YET
def rule_2(i, j, l, r):
    if d(l[i-1].content, l[i].content) == 0 or l[i].user == l[j].user:
        return 0
    q = (C_SLACK * d(l[i - 1].content, l[j].content) - d(l[i].content, l[j].content)) / d(l[i-1].content, l[i].content)
    q = q * C_PUNISH if q < 0 else q
    q = q * C_SCALE * (1 - C_TEXT) * pow(d(l[i-1].content, l[i].content), C_LEN) * math.log10(1 + r[l[j].user])
    return q


# timestamp factor
def rule_3(i, j, l, r):
    f = 0
    return f


# If the author is anonymous
def is_ip(user):
    re_ip = re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
    if len(re_ip.findall(user)) == 0:
        return False
    return True


def compute_reputation(wiki_list, reputation_list):
    for i in range(1, len(wiki_list) - 1):
        # DEBUG
        print 'WORKING ON ' + str(wiki_list[i].revid)
        j = i + 1
        while j - i <= 10 and j < len(wiki_list):
            if not is_ip(wiki_list[i].user):
                reputation_list[wiki_list[i].user] += rule_1(i, j, wiki_list, reputation_list)
                if reputation_list[wiki_list[i].user] < 0:
                    reputation_list[wiki_list[i].user] = 0.1
                elif reputation_list[wiki_list[i].user] > C_MAXREP:
                    reputation_list[wiki_list[i].user] = C_MAXREP

                    # DEBUG
                    print str(wiki_list[i].revid) + ' - ' + wiki_list[i].user + " Maximum Alert!"
                    max_rep_list.add(wiki_list[i].revid)
                # DEBUG
                # print "[RULE1] " + wiki_list[i].revid + '-' + wiki_list[i].user \
                    # + ': ' + str(reputation_list[wiki_list[i].user])

            if j - i <= 3:
                if not is_ip(wiki_list[i].user):
                    reputation_list[wiki_list[i].user] += rule_2(i, j, wiki_list, reputation_list)
                    if reputation_list[wiki_list[i].user] < 0:
                        reputation_list[wiki_list[i].user] = 0.1
                    elif reputation_list[wiki_list[i].user] > C_MAXREP:
                        reputation_list[wiki_list[i].user] = C_MAXREP

                        # DEBUG
                        max_rep_list.add(wiki_list[i].revid)
                        print str(wiki_list[i].revid) + ' - ' + wiki_list[i].user + " Maximum Alert!"

                    # DEBUG
                    # print "[RULE2] " + wiki_list[i].revid + '-' + wiki_list[i].user \
                        # + ': ' + str(reputation_list[wiki_list[i].user])

            j += 1

    return reputation_list


def main():
    # read json from file
    wiki_list = read_json()

    # DEBUG
    print 'Before Pre-processing wiki_list LENGTH: ', str(len(wiki_list))

    # pre-processing
    wiki_list = pre_processing(wiki_list)

    # wiki author list
    wiki_authors = set()
    for obj in wiki_list:
        if not is_ip(obj.user):
            wiki_authors.add(obj.user)

    # DEBUG
    # for author in wiki_authors:
    #     print author,
    # return

    # DEBUG
    print 'After Pre-processing wiki_list LENGTH: ', str(len(wiki_list))

    # Initial reputation of All authors
    reputation_list = {}
    for wiki_obj in wiki_list:
        reputation_list[wiki_obj.user] = 0.1
    reputation_list = compute_reputation(wiki_list, reputation_list)
    reputation_list = sorted(reputation_list.iteritems(), key=lambda reputation: reputation[1], reverse=True)

    # DEBUG
    print reputation_list
    print max_rep_list

if __name__ == '__main__':
    main()