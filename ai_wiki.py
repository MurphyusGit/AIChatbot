from ai import searchword  # import searchword to concatenate url
from ai_database import ignored_descrwords  # import required dict for get_description()
# 3rd party code for accessing webpages (https://www.crummy.com/software/BeautifulSoup/)
import requests
from bs4 import BeautifulSoup
import re


url = 'https://de.wikipedia.org/wiki/' + searchword
res = requests.get(url)
html_page = res.content
soup = BeautifulSoup(html_page, 'html.parser')
text = soup.find_all(text=True)

output = ''
blacklist = [
    '[document]',
    'noscript',
    'header',
    'html',
    'meta',
    'head',
    'input',
    'script',
    # there may be more elements you don't want, such as "style", etc.
]

for t in text:
    if t.parent.name not in blacklist:
        output += '{} '.format(t)

output = "".join([s for s in output.strip().splitlines(True) if s.strip("\r\n").strip()])
# end of 3rd party code

def get_age():
    bio = get_sentence()
    birthday = re.search("\d+\. .+ \d+", bio).group()  # search for date pattern
    birthday = re.sub(" \w+ ",  # replace written month with number
                      [x[1] for x in monthnumbers if x[0] in birthday][0] + ".", birthday)
    t = time.localtime()
    current_date = str(time.strftime("%d.%m.%Y", t))  # get current date as dd.mm.YYYY
    if current_date[3] == "0":
        current_date = current_date[:3] + current_date[4:]  # remove leading 0 for month
    if current_date[0] == "0":
        current_date = current_date[1:]  # remove leading 0 for day
    age = (int(re.search("\d{4}", current_date).group())
           - int(re.search("\d{4}", birthday).group()))  # calculate age as diff of years
    if (int(re.search(".\d{1,2}.", birthday).group().replace(".", "")) >
            int(re.search(".\d{1,2}.", current_date).group().replace(".", ""))):
        age -= 1  # birth month later than current month -> birthday not yet happened
    if (int(re.search(".\d{1,2}.", birthday).group().replace(".", "")) ==  # birth month = current month
            int(re.search(".\d{1,2}.", current_date).group().replace(".", ""))):
        if (int(re.search("\A\d{1,2}.", birthday).group().replace(".", "")) >
                int(re.search("\A\d{1,2}.", current_date).group().replace(".", ""))):
            age -= 1  # birth day later than current day -> birthday not yet happened
    return age

def get_sentence():
    """get first sentence of get_paragraph() return"""
    paragraph = get_paragraph(1)
    sentence = ""
    notinbrackets = True
    for char in paragraph:
        sentence += char
        if char == "(":
            notinbrackets = False
        if char == ")":
            notinbrackets = True
        if char == "." and notinbrackets:  # ignore punctuation in brackets
            break
    return sentence


def get_paragraph(n: int):
    """get n number of paragraphs from output var"""
    lines = output.splitlines()
    paragraph = ""
    for e, line in enumerate(lines):
        if n == 1:
            if len(line) > 100 and not any([True if x in line else False for x in ignored_descrwords]):
                paragraph = line  # pull first paragraph
                break
        elif n == 2:
            if len(line) > 100 and not any([True if x in line else False for x in ignored_descrwords]):
                paragraph = line + lines[e + 1]  # pull first two paragraphs
                break
    if paragraph[0] == " ":
        paragraph = paragraph[1:]  # remove leading whitespace
    paragraph_nopro = ""
    pro_start = 0
    pro_end = -1
    is_pro = False
    for i in range(len(paragraph)):
        if paragraph[i] == "(":
            for j in range(i + 1, len(paragraph)):
                if paragraph[j] == "[" and not paragraph[j + 1].isnumeric():
                    # square brackets with text inside -> pronunciation
                    is_pro = True
                    pro_start = i  # memorize start of round brackets containing pronunciation brackets
                    break
            continue
        elif paragraph[i] == ")" and is_pro:
            pro_end = i  # memorize end of round brackets containing pronunciation brackets
            break
    # cut out pronunciation bracket
    paragraph_nopro = paragraph[:pro_start] + paragraph[pro_end + 1:]
    if "[" in paragraph_nopro:
        paragraph_nopro = re.sub("\[.*?\]", "", paragraph_nopro)  # rm [1] etc
    if " " in paragraph_nopro:
        paragraph_nopro = paragraph_nopro.replace(' ', '')  # rm pronounc code
    paragraph_clean = " "
    for j in range(len(paragraph_nopro) - 1):
        if paragraph_nopro[j] == " " and (paragraph_clean[-1] == " "
                                          or paragraph_clean[-1] == "("):
            continue  # ignore whitespace after whitespace or after opening bracket
        elif paragraph_nopro[j] == " " and paragraph_nopro[j + 1] == ")":
            continue  # ignore whitespace leading closing bracket
        elif paragraph_nopro[j] == " " and (paragraph_nopro[j + 1] == ","
                                            or paragraph_nopro[j + 1] == "."):
            continue  # ignore whitespaces leading punctuation
        else:
            paragraph_clean += paragraph_nopro[j]
    paragraph_broken = paragraph_clean[0]
    k = 0
    # insert line breaks after 80 chars
    while k < len(paragraph_clean) - 1:
        k += 1
        if k % 80 == 0 and paragraph_clean[k] == " ":  # len(prev line) = 80 and not in a word
            paragraph_broken += "\n"  # insert line break
        elif k % 80 == 0 and paragraph_clean[k] != " ":  # len(prev line) = 80 and in a word
            paragraph_broken += paragraph_clean[k]  # add next char
            l = k
            # insert line break at next whitespace
            while l < len(paragraph_clean) - 1:
                l += 1
                k += 1
                if paragraph_clean[l] == " ":
                    paragraph_broken += "\n"
                    break
                else:
                    paragraph_broken += paragraph_clean[l]
        else:
            paragraph_broken += paragraph_clean[k]  # add char for char
    if paragraph_broken[-1].isalpha():
        paragraph_broken += "."  # add punctuation at end if not already there
    return paragraph_broken


def get_description():
    """get fact sheet from output var"""
    lines = output.splitlines()
    description = "\n"
    active = False
    for line in lines:
        if line == " Zur Suche springen ":  # line leading fact sheet in raw text
            active = True
            continue
        elif active and len(line) < 150 and line[-1] != ":":  # short line not ending with colon
            description += line + "\n"  # concatenate to description with line break
        elif active and len(line) < 150 and line[-1] == ":":  # short line ending with colon
            description += line  # concatenate left text of fact to description without line break
        elif len(line) >= 150:  # stop when paragraph starts
            break
    description_clean = linecleaner(description)
    description_final = ""
    splittable = True
    if description_clean.count(":") > 3:  # assuming not split table
        splittable = False
        for e, line in enumerate(description_clean.split("\n")):
            # non split table has colon in every fact: "Höhe: 3 m" (fact paired up in l.139)
            if (":" not in "".join(description_clean.split("\n")[e + 1:])
                    and ":" not in "".join(description_clean.split("\n")[e + 2:])):
                # two following lines w/o colon -> end of fact sheet
                description_final += line
                break
            else:
                description_final += line + "\n"
    else:  # split table
        description_final = description_clean
    if " " in description_final:
        description_final = description_final.replace(' ', ' ')  # rm pronounc code
    if "[" in description_final:
        description_final = re.sub("\[.*?\]", " ", description_final)  # rm [1] etc
    # if split table design facts have to be paired up: "Höhe", "3 m" -> "Höhe: 3 m"
    if splittable:
        # take first line (assuming title) and pair up
        description_inter = description_final.split("\n")[0] + "\n"  # title
        leftstrings = []
        rightstrings = []
        x = 1
        while x < len(description_final.split("\n")):
            if (x - 1) % 2 == 0:  # even line number -> left text of fact
                leftstrings += [description_final.split("\n")[x]]
            elif (x - 1) % 2 != 0:  # uneven line number -> right text of fact
                rightstrings += [description_final.split("\n")[x]]
            x += 1
        for e, pair in enumerate(list(zip(leftstrings, rightstrings))):
            if e == len(list(zip(leftstrings, rightstrings))) - 1:  # last fact
                description_inter += pair[0] + ":" + " " + pair[1]
                break
            else:
                description_inter += pair[0] + ":" + " " + pair[1] + "\n"  # concatenate facts with line breaks
        description_final = linecleaner(description_inter)
    else:
        description_final = linecleaner(description_final)
    return description_final


def linecleaner(descr):
    """remove unwanted chars or words in fact sheet"""
    descr_clean = ""
    for e, line in enumerate(descr.split("\n")):
        if not line or any([True if x in line else False
                            for x in ignored_descrwords]):
            continue  # skip empty lines and unwanted lines
        if line[0] != " ":
            descr_clean += line[0]  # concatenate first char if not whitespace
        # concatenate remaining chars if valid except last char
        for n in range(1, len(line) - 1):
            if line[n] == " " and (descr_clean[-1] == " " or
                                   descr_clean[-1] == "("):
                continue  # ignore whitespace after whitespace or opening bracket
            elif line[n] == " " and line[n + 1] == ")":
                continue  # ignore whitespace leading closing bracket
            elif line[n] == " " and (line[n + 1] == "," or line[n + 1] == "." or
                                     line[n + 1] == ":"):
                continue  # ignore whitespaces leading punctuation
            else:
                descr_clean += line[n]
        descr_clean += line[-1] + "\n"  # concatenate last char with line break
    # remove last line which is always empty
    descr_clean = "\n".join(descr_clean.split("\n")[:len(descr_clean.split("\n")) - 1])
    return descr_clean
