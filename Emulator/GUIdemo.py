import os

# menus
mainMenu = [" ", "Mifare Classic", "NTAG", " "]
mifareMenu = [" ", "..", "Read", "Write current", "Save current", "Load from saved", " "]
ntagMenu = [" ", "..", "Read", "Write current", "Save current", "Load from saved", " "]

# saved data
savedUIDsMifare = []
savedUIDsNTAG = []

def driver_select(selection):
    os.system('clear')
    match selection:
        case 0: print("Present MIFARE card...")
        case 1: print("MIFARE Classic write")
        case 2: print("Save current to MIFARE list")
        case 3: print("Display saved MIFARE UIDs")
        case 4: print("NTAG read")
        case 5: print("NTAG write")
        case 6: print("Save current to NTAG list")
        case 7: print("Display saved NTAG UIDs")
        case _: pass  # no action

def printMenu(menu, index):
    os.system('clear')

    # ensure index in valid range
    if index <= 0:
        index = 1
    if index >= len(menu) - 1:
        index = len(menu) - 2

    ln1 = menu[index - 1]
    ln2 = menu[index]
    ln3 = menu[index + 1]

    print(ln1)
    print(">" + ln2)
    print(ln3)

    return index

# initialize
currentMenu = mainMenu
currentOptionIndex = 1
driverSelection = None

printMenu(currentMenu, currentOptionIndex)

while True:
    user_input = input().strip()

    if user_input == "u":  # up
        if currentOptionIndex > 1:
            currentOptionIndex -= 1
        currentOptionIndex = printMenu(currentMenu, currentOptionIndex)

    elif user_input == "d":  # down
        if currentOptionIndex < len(currentMenu) - 2:
            currentOptionIndex += 1
        currentOptionIndex = printMenu(currentMenu, currentOptionIndex)

    elif user_input == "":  # select
        if currentMenu == mainMenu:
            if currentOptionIndex == 1:  # Mifare Classic
                currentMenu = mifareMenu
                currentOptionIndex = 2
            elif currentOptionIndex == 2:  # NTAG
                currentMenu = ntagMenu
                currentOptionIndex = 2
            currentOptionIndex = printMenu(currentMenu, currentOptionIndex)

        elif currentMenu == mifareMenu:
            if currentOptionIndex == 1:  # go back
                currentMenu = mainMenu
                currentOptionIndex = 1
            elif currentOptionIndex == 2:
                driverSelection = 0
            elif currentOptionIndex == 3:
                driverSelection = 1
            elif currentOptionIndex == 4:
                driverSelection = 2
            elif currentOptionIndex == 5:
                driverSelection = 3
            if driverSelection is not None:
                driver_select(driverSelection)
                input("\nPress Enter to return...")
            currentOptionIndex = printMenu(currentMenu, currentOptionIndex)

        elif currentMenu == ntagMenu:
            if currentOptionIndex == 1:
                currentMenu = mainMenu
                currentOptionIndex = 2
            elif currentOptionIndex == 2:
                driverSelection = 4
            elif currentOptionIndex == 3:
                driverSelection = 5
            elif currentOptionIndex == 4:
                driverSelection = 6
            elif currentOptionIndex == 5:
                driverSelection = 7
            if driverSelection is not None:
                driver_select(driverSelection)
                input("\nPress Enter to return...")
            currentOptionIndex = printMenu(currentMenu, currentOptionIndex)

    else:
        # invalid key
        pass
