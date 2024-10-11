import os
import json
from marketdata import make_request_with_retry, get_nameid
import random

investments = []
randomTexts = ['LOL', 'OMG', 'Oh noo', 'Wow', 'Yikes', 'Aww', 'Oops', 'Ugh', 'Sigh', 'Whew',
 'Whoa', 'Ouch', 'Yay', 'Huh?', 'Eek', 'Aww man', 'Heh', 'Grr', 'Darn', 'Yesss',
 'Nooo', 'Phew', 'Oopsie', 'Ack', 'Hmm', 'Jeez', 'Hooray', 'Dang', 'What?!', 'Ha!',
 'Boo', 'Oof', 'Uh-oh', 'Womp', "D'oh", 'Ahh!', 'Whaaat?', 'Yippee', 'Whoa there', 'Meh',
 'Pfft', 'Brr', 'Oh snap!', 'Rats', 'Uh-huh', 'Oh dear', 'Ew', 'Bleh', 'Gasp', 'Awk!']

def ask_for_input():
    print("Input \"help\" to see a list of commands.")
    
    match (input()):
        case "help":
            os.system('cls' if os.name == 'nt' else 'clear')
            print()
            print("--------------------------------------------------------------------------")
            print("Input \"help\" to see this list.")
            print("Input \"check\" to check how your investments are doing.")
            print("Input \"exit\" to exit the program.")
            print("--------------------------------------------------------------------------")
            print("TO CHANGE YOUR INVESTMENTS INFO EDIT THE \"Investments_info.json\" FILE.")
            print("--------------------------------------------------------------------------")
            print()
            ask_for_input()

        case "exit":
            print("Goodbye!")
            return  # Stop execution gracefully

        case "check":
            os.system('cls' if os.name == 'nt' else 'clear')
            try:
                # Try to open the file in read mode
                with open("Investments_info.json", "r") as f:
                    file_content = f.read().strip()  # Read the file content and strip extra spaces/newlines

                    if not file_content:  # If file is empty or only contains whitespace
                        print("The file is empty.")
                        recreate_file_prompt()

                    else:
                        print("Checking your investments...")

                        currentValue = 0.01
                        invData = json.loads(file_content)  # Load the valid JSON data

                        print(f"This should take around {round((len(invData) - 2) * 5.2, 1)} seconds.")

                        for inv in invData:
                            if invData.index(inv) < len(invData) - 2:
                                print(randomTexts[random.randint(0, len(randomTexts) - 1)])
                                for key in dict(inv).keys():
                                    print(key)
                                    currentValue += get_steam_market_price(key) * inv[key] #####

                        wasValueInJSON = False
                        lastValue = 0.01

                        investments = invData
                        for d in investments:
                            if "Last Price" in d:
                                lastValue = d["Last Price"]
                                d["Last Price"] = currentValue
                                wasValueInJSON = True
                        
                        if not wasValueInJSON:
                            investments.append({"Last Price": currentValue})
                            lastValue = round(currentValue, 2)

                        wasValueInJSON = False
                        baseValue = 0.01
                        investments = invData
                        for d in investments:
                            if "Base Price" in d:
                                baseValue = d["Base Price"]
                                wasValueInJSON = True
                        
                        if not wasValueInJSON:
                            investments.append({"Base Price": currentValue})
                            baseValue = round(currentValue, 2)
                        
                        json.dump(investments, open("Investments_info.json", "w"), indent=4)

                        os.system('cls' if os.name == 'nt' else 'clear')
                        print("Finished checking your investments.")
                        print(f"In total everything is worth around {round(currentValue, 2)} PLN.")
                        print(f"Which means that it changed by {round(((currentValue / lastValue) - 1) * 100, 3)}% since last check.")
                        print(f"Or by {round(currentValue / baseValue - 1, 3) * 100}% since the beginning.")

                        input("Press enter to continue...")


            except json.JSONDecodeError:
                print("It looks like your \"Investments_info.json\" file contains invalid JSON.")
                recreate_file_prompt()

def recreate_file_prompt():
    print("Would you like to recreate the file? (y/n)")
    match (input()):
        case "y":
            print("Input \"done\" when you add all your investments.")
            fill_inv_file()
        case "n":
            print("Goodbye!")
            return  # Graceful stop


def fill_inv_file():
    print("Input a steam market link for your investment.")
    inp = input()
    if inp.startswith("https://steamcommunity.com/market/listings/"):
        link = inp
        appId = link.removeprefix("https://steamcommunity.com/market/listings/")

        while not appId.endswith("/"):
            appId = appId[:-1]
            if appId.endswith("/"):
                appId = appId[:-1]
                break
            
        hashName = link.removeprefix(f"https://steamcommunity.com/market/listings/{appId}/")

        itemName = link.removeprefix(f"https://steamcommunity.com/market/listings/{appId}/")
        while itemName.find("%20") >= 0:
            itemName = itemName.replace("%20", " ")
            if not itemName.find("%20"):
                break
            
        itemName = itemName.replace("%7C", "|")
        itemName = itemName.replace("%E2%84%A2", "™")
        itemName = itemName.replace("%26", "&")

        ask_for_quantity(itemName, hashName)
        
    elif inp == "done":
        # Ensure that even if investments are empty, an empty list is written as valid JSON
        with open("Investments_info.json", "w") as f:
            json.dump(investments, f, indent=4)  # Dump the investments list as JSON
        print("Investments saved. Goodbye!")
        return  # Graceful exit
    else:
        print("Invalid link. Try again.")
        fill_inv_file()


def ask_for_quantity(itemName, hashName):
    print(f"How many {itemName}s do you have?")
    inp = input()

    if inp != "done":
        try:
            temp_dict = {hashName: int(inp)}

            isItIn = False

            for d in investments:
                if hashName in d:
                    d[hashName] = temp_dict[hashName]
                    isItIn = True

            if not isItIn:
                investments.append(temp_dict)

            print("Noted")
            fill_inv_file()
        except ValueError:
            print("Invalid input. Please input a number.")
            ask_for_quantity(itemName, hashName)

def get_steam_market_price(hashName):
    url = f"https://steamcommunity.com/market/itemordershistogram?country=US&currency=6&language=english&two_factor=0&item_nameid={get_nameid(hashName)}"
    response = make_request_with_retry(url)
    if response and response.status_code == 200:
        order_data = response.json()
        if isinstance(order_data, dict):
            if int(order_data.get('highest_buy_order', 0)) / 100 is not None:
                return int(order_data.get('highest_buy_order', 0)) / 100
            else:
                return 0
        else:
            print("Error, no response")
    else:
        print("Error, bad response")


os.system('cls' if os.name == 'nt' else 'clear')
print(r"""
    
           ||====================================================================||
           ||//$\\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\//$\\||
           ||(100)==================| FEDERAL RESERVE NOTE |================(100)||
           ||\\$//        ~         '------========--------'                \\$//||
           ||<< /        /$\              // ____ \\                         \ >>||
           ||>>|  12    //L\\            // ///..) \\         L38036133B   12 |<<||
           ||<<|        \\ //           || <||  >\  ||                        |>>||
           ||>>|         \$/            ||  $$ --/  ||        One Hundred     |<<||
        ||====================================================================||>||
        ||//$\\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\//$\\||<||
        ||(100)==================| FEDERAL RESERVE NOTE |================(100)||>||
        ||\\$//        ~         '------========--------'                \\$//||\||
        ||<< /        /$\              // ____ \\                         \ >>||)||
        ||>>|  12    //L\\            // ///..) \\         L38036133B   12 |<<||/||
        ||<<|        \\ //           || <||  >\  ||                        |>>||=||
        ||>>|         \$/            ||  $$ --/  ||        One Hundred     |<<||
        ||<<|      L38036133B        *\\  |\_/  //* series                 |>>||
        ||>>|  12                     *\\/___\_//*   1989                  |<<||
        ||<<\      Treasurer     ______/Franklin\________     Secretary 12 />>||
        ||//$\                 ~|UNITED STATES OF AMERICA|~               /$\\||
        ||(100)===================  ONE HUNDRED DOLLARS =================(100)||
        ||\\$//\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\\$//||
        ||====================================================================||

                        """)

ask_for_input()
