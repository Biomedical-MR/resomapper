import os
import json
import traceback

import resomapper.core.utils as ut
from resomapper.core.misc import auto_innited_logger as lggr
from resomapper.core.misc import auto_processing_options

from colorama import just_fix_windows_console



def tools_menu():
    
    tool_options = {
        "t": "Create options json template for automatic resomapper processing.",
        "x": "Exit"
    }

    just_fix_windows_console()
    print(lggr.welcome)

    selected_tool = ut.ask_user_options("What tool do you want to use?", tool_options)

    if selected_tool == "t":
        print(f"{lggr.ask}Please select the directory where you want to store the file in the pop up window.")
        output_path = ut.select_directory()

        output_filename = os.path.join(output_path,"resomapper_auto_options.json")

        with open(output_filename, "w") as outfile: 
            json.dump(auto_processing_options, outfile)
        
        print(f"{lggr.success}File succesfully stored: {output_filename}")
    
    elif selected_tool == "x":
        return

#### MAIN ####


def run_tools():

    try:
        tools_menu()
    except KeyboardInterrupt:
        print(f"\n\n{lggr.error}You have exited from resomapper.")
    except Exception as err:
        print(f"\n\n{lggr.error}The following error has ocurred: {err}\n")
        print("More information:\n")
        traceback.print_exc()


if __name__ == "__main__":
    run_tools()