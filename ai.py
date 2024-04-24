from ai_database import *  # import dictionaries etc
from ai_wiki import *  # import algorithms for searching wikipedia
from itertools import combinations  # for testing all possible combinations of searchwords
import random  # for randomizing responses
import time  # for giving corresponding greetings depending on time of day


repetitions = 0


def repetition_handler() -> int:
    """count repetitions of same type of request"""
    input_type = ""
    prev_type = ""
    kw = ""
    boolean = False
    # checking current input text
    for keyword in keywords:  # keywords = [hello_keywords, howgoesit_keywords, help_keywords]
        for x in keyword:
            if x in input_text.lower():
                kw = keyword  # input matches category of keyword
                boolean = True
                break
    if boolean:
        input_type = kw
        kw = ""
    boolean = False
    # checking prev input text
    for keyword in keywords:
        for x in keyword:
            if x in prev_text.lower():
                kw = keyword
                boolean = True
                break
    if boolean:
        prev_type = kw
    boolean = False
    if (input_type == prev_type  # new input same category as prev input
            and prev_text != ""):  # excluding 1st input
        return 1  # count up
    # else
    global repetitions
    repetitions = 0  # reset counter
    return 0


def bestsearchword(input: str) -> str:
    """evaluating best searchword from input"""
    valid_words = []
    for x in input.split():
        # ignore forbidden searchwords and valuewords ("hoch", "lang", etc)
        if (not any([True if x.lower() in y else False for y in ignored_searchwords])
                and not any([True if y[0] == x.lower()  # = not in valuewords (list of tuples)
                             else False for y in valuewords])):
            valid_words += [x]  # collecting valid words from input
    # create list of combinations of searchwords sorted descending by length
    combination_list = sorted([subset for l in range(len(valid_words) + 1)
                               for subset in combinations(valid_words, l)
                               if subset],
                              key=len, reverse=True)
    for combination in combination_list:
        s = combination[0]
        if len(combination) > 1:
            for word in combination[1:]:
                s += "_" + word  # "Golden", "Gate", "Bridge" -> "Golden_Gate_Bridge"
        if str(requests.get('https://de.wikipedia.org/wiki/' + s)) != "<Response [404]>":
            # searchword valid, wiki article exists
            return s  # return best found searchword
        else:
            continue
    return input  # if no searchwords found, return raw input


def line_handler(linetype, x, y):
    """determine type of response according to repetition level"""
    global repetitions, line
    if repetitions == 0:
        line = random.choice(linetype[:x])
        repetitions = repetition_handler() + repetitions
    elif repetitions == 1:
        line = random.choice(linetype[x:y])
        repetitions = repetition_handler() + repetitions
    elif repetitions > 1:
        line = random.choice(linetype[y:])
        repetitions = repetition_handler() + repetitions


print("\U0001F916", "Was kann ich für Sie tun?")
searchword = ""
line = ""
input_text = ""
prev_text = ""
while not any([True if x in input_text.lower() else False for x in goodbye_keywords]):
    try:
        # while goodbye cond not met, let user input text
        input_text = input()
        # single or multi word input set as searchword in case of purewiki
        if len(input_text.split()) == 1:
            searchword = input_text
        else:
            searchword = "_".join(input_text.split())
        exec(open('ai_wiki.py').read())  # run wiki algorithm to set res var for pure wiki cond
        # skip for empty input
        if input_text == "":
            continue
        # power lines
        if "was kannst du" in input_text.lower():
            line_handler(power_lines, 2, 4)
        # goodbye lines
        if any([True if x in input_text.lower() else False for x in goodbye_keywords]):
            line = random.choice(goodbye_lines)
        # hello lines
        elif any([True if x in input_text.lower() else False for x in hello_keywords]):
            if repetitions == 0:
                x = random.randint(0, 2)  # 33% random line, 67% greet according to time of day
                if x == 0:
                    line = random.choice(hello_lines[:2])
                else:  # x == 1 or x == 2
                    t = time.localtime()
                    current_time = int(time.strftime("%H", t))  # hour in 24h format
                    if 10 <= current_time < 17:
                        line = "Guten Tag!"
                    elif 17 < current_time < 24:
                        line = "Guten Abend!"
                    elif 0 <= current_time < 10:
                        line = "Guten Morgen!"
                repetitions = repetition_handler() + repetitions
            elif repetitions == 1:
                line = random.choice(hello_lines[2:4])
            elif repetitions > 1:
                line = random.choice(hello_lines[4:])
        # howgoesit lines
        elif any([True if x in input_text.lower() else False for x in howgoesit_keywords]):
            line_handler(howgoesit_lines, 2, 4)
        # help lines
        elif ("wie" in input_text.lower() and "alt" not in input_text.lower()
              and not any([True if x[0] in input_text.lower()
                       else False for x in valuewords])):  # not context wiki
            line_handler(help_lines, 2, 4)
        # pure wiki
        elif (str(res) != "<Response [404]>"
              and not any([True if x in input_text.lower()
                       else False for x in ignored_searchwords])):
            output_type = " "
            try:
                get_description()  # works if description exists
                while output_type.lower() not in "datenkurzlang":
                    output_type = input("Möchtest du Daten, einen kurzen \
oder einen langen Text: ")
                    if output_type.lower() not in "datenkurzlang":
                        print("\U0001F916", "Ungültige Eingabe!")
            except IndexError:  # if no description don't offer description
                while output_type.lower() not in "kurzlang":
                    output_type = input("Möchtest du einen kurzen \
oder einen langen Text: ")
                    if output_type.lower() not in "kurzlang":
                        print("\U0001F916", "Ungültige Eingabe!")
            if output_type.lower() == "daten":
                line = get_description()
            elif output_type.lower() == "kurz":
                line = get_sentence()
            elif output_type.lower() == "lang":
                if get_sentence() == get_paragraph(1):
                    line = get_paragraph(2)
                else:
                    line = get_paragraph(1)
        # context wiki paragraph
        elif "erzähl" in input_text.lower() and bestsearchword(input_text) != input_text:
            searchword = bestsearchword(input_text)
            if searchword != input_text:
                exec(open('ai_wiki.py').read())  # execute wiki algorithm to check results after
                if get_sentence() == get_paragraph(1):
                    line = get_paragraph(2)
                else:
                    line = get_paragraph(1)
        # context wiki sentence
        elif ((re.search(r'\bwer\b', input_text.lower())  # '\bwer\b' = " wer "
               or "was" in input_text.lower())
              and bestsearchword(input_text) != input_text):
            searchword = bestsearchword(input_text)
            if searchword != input_text:
                exec(open('ai_wiki.py').read())
                line = get_sentence()
        # context wiki description
        elif ("wie" in input_text.lower()
              and bestsearchword(input_text) != input_text  # corresponding wiki article exists
              and any([True if x[0] in input_text.lower()
                       else False for x in valuewords])):  # valuewords = [("hoch", "höhe"), etc]
            try:
                searchword = bestsearchword(input_text)
                valueword = [x[1] for x in valuewords  # get word to search in article description
                             if x[0] in input_text.lower()][0]  # [0] to get str type out of list
                alternateword = " "  # foreign default value preventing false positive
                if valueword == "gewicht":
                    alternateword = "masse"
                if valueword == "höhe":
                    alternateword = "größe"
                if valueword == "größe":
                    alternateword = "höhe"
                exec(open('ai_wiki.py').read())  # execute wiki algorithm to check results after
                description = get_description()
                for fact in description.split("\n"):
                    if valueword in fact.lower() or alternateword in fact.lower():
                        leftword = re.sub(": .*", "", fact)
                        line = re.sub(".*: ", "", fact)
                        if "gesamt" in fact.lower() or valueword == leftword.lower():
                            break  # assume this is wanted value
            except IndexError:
                line = "Das gibt Wikipedia leider nicht her."
        # context wiki age
        elif "wie alt" in input_text.lower() and bestsearchword(input_text) != input_text:
            searchword = bestsearchword(input_text)
            if searchword != input_text:
                exec(open('ai_wiki.py').read())
                line = get_age()
        # why lines
        elif ([word for word in input_text.split()][0].lower() == "warum"
                and "ich" in input_text.lower()):
            line_handler(why_lines, 2, 4)
        # clueless lines if input doesnt match any reactions
        else:
            line_handler(clueless_lines, 3, 6)
        prev_text = input_text
        print("\U0001F916", line)
    except:  # catch all errors
        print("\U0001F916", "FATALER FEHLER IM SYSTEM", sys.exc_info(), "\U0001F6A8")
print("\U0001F916", "Herunterfahren...")
