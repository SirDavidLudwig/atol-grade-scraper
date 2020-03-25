#!/usr/bin/python3
import aiohttp
import argparse
import asyncio
import html
import re
import sys
from pandas import DataFrame

# The base URL to the CS lab server
BASE_URL = "http://cslabserver2.cs.mtsu.edu"

# Separators to choose from
SEPARATORS = {
    "comma": ',',
    "space": ' ',
    "tab"  : '\t'
}

async def login(session, username, password):
    response = await session.post( f"{BASE_URL}/login.php", data = {
    	"username": username,
    	"password": password,
    	"login"   : "Sign In"
    })
    return "Unable to sign in." not in await response.text()

async def scores(session, course, lab, account):
    async with session.get(f"{BASE_URL}/admin/studentScores.php", params = {
    	"course": course,
    	"lab"   : lab,
        "userID" : account
    }) as response:
        body = html.unescape(await response.text()).replace("- - - - - -", "0 / 0")
        scores = re.findall(r"(?<=\>)\d+\s\/\s\d+", body)
        return (account, scores[:-1], scores[-1])

async def get_c_accounts(session, course, section, lab):
    async with session.get(f"{BASE_URL}/admin/manage.php", params = {
        "page" : "scores",
        "course" : course,
        "section" : section,
        "lab" : lab,
        "exercise" : "1", 
        "submit" : "view"
    }) as response:
        return re.findall(r"(?<=\<td>)c[0-9]+", await response.text())

async def fetch_grades(username, password, course, section, lab):
    async with aiohttp.ClientSession() as session:
    	if await login(session, username, password):
            c_accounts = await get_c_accounts(session, course, section, lab)
            return [await scores(session, course, lab, account) for account in c_accounts]
    	else:
    		print("Failed login:", {username})
    		return None

async def main(argv):
    parser = argparse.ArgumentParser(description="Scrape AtoL grades for an assignment, and copy to clipboard")
    parser.add_argument("course", type=str, help="The course that the assignment is under")
    parser.add_argument("section", type=str, help="The section of course")
    parser.add_argument("labid", type=str,  help="The lab ID to scrape")
    parser.add_argument("-u", "--no-cnumber", action="store_true", help="Do not output c number")
    parser.add_argument("-d", "--no-denominator", action="store_true", help="Do not output denominator for individual exercise scores")
    parser.add_argument("-f", "--no-final", action="store_true", help="Do not output the cslab-calculated final score")
    parser.add_argument("-t", "--terminal-output", action="store_true", help="Print to standard out instead of copying to clipboard")
    parser.add_argument("-s", "--separator", choices=SEPARATORS.keys(), default=tuple(SEPARATORS.keys())[0], help="The separator to use for scores")
    parser.add_argument("-e", "--exercises", type=lambda x: [int(ex)-1 for ex in x.split(',')], help="Comma-separated list of exercises to include")
    args = parser.parse_args()

    user = tuple(input().split()) 

    grades = await fetch_grades(*user, args.course, args.section, args.labid)

    outlist = []
    for (cnumber, scores, final) in grades:

        entry = []

        #strip off the denominator if the user does not want it printed
        if args.no_denominator:
            scores = [score.split(' ')[0] for score in scores]
            final = final.split(' ')[0]
        #otherwise strip whitespaces
        else:
            scores = [score.replace(" ", "") for score in scores]
            final = final.replace(" ", "")

        #if user wants c number included:
        if not args.no_cnumber:
            entry.append(cnumber)
            
        #if user only wants specific exercises:
        if args.exercises:
            for ex in args.exercises:
                entry.append(scores[ex])
        else:
            entry.extend(scores)
           
        #if user wants cslabserver calculated score:
        if not args.no_final:
            entry.append(final)

        outlist.append(SEPARATORS[args.separator].join(entry))
    
    if not args.terminal_output:
        DataFrame(outlist).to_clipboard(index=False,header=False)
    else:
        for entry in outlist:
            print(entry)

    return 0

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(sys.argv))
    loop.close()


#    outlist = []
#
#    filters = sorted(set(args.filter or []), reverse=True)
#    for i, values in enumerate(grades):
#        for j in filters:
#            del values[j - 1]
#        if not args.no_username:
#            values = [users[i][0]] + values
#        outlist.append(SEPARATORS[args.separator].join(values))
#    
#    DataFrame(outlist).to_clipboard(index=False,header=False)








