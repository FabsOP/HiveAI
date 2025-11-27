############## IMPORTS ##############################
import Hive
import Bee
import os
import json

# test 1
def test1():
    ### Configure Hive ###
    modelA = "https://distant-guardian-starts-salaries.trycloudflare.com"   # Replace with your SSH-tunneled local port
    modelB = "https://golden-angel-tunnel.trycloudflare.com"

    h = Hive.Hive("Hive 1")
    h.set_randomize(False)

    h.add_model(modelA)
    h.add_model(modelB)

    ### Configure Queen ###
    h.attach_model_to_queen(h.getModels()[0])

    ### Configure Bees ###
    b1 = Bee.Bee("Creative", "Think outside the box")
    b2 = Bee.Bee("Pragmatic", "Think step by step")
    b3 = Bee.Bee("Analytical", "Think logically")

    #attach models
    b1.attach_model(h.getModels()[1])
    b2.attach_model(h.getModels()[1])
    b3.attach_model(h.getModels()[1])

    #define injections
    b1.addInjection("Disagree with previous speaker", 3)
    b1.addInjection("Agree with previous speaker", 3)
    b1.addInjection("Summarise what's discussed so far", 3)

    b2.addInjection("Agree with previous speaker", 3)
    b2.addInjection("Disagree with previous speaker", 5)
    b2.addInjection("Summarise what's discussed so far", 3)

    b3.addInjection("Summarise what's discussed so far", 3)
    
    ### Add bees to hive ###
    h.add_bee(b1)
    h.add_bee(b2)
    h.add_bee(b3)

    prompt = "How to survive a beer attack in a dark forest?"
    # h.query(prompt, 5)

#test 2
def test2():
    id ="1eaa8d8f-c855-11f0-ba2b-8eb6c9366e60"
    #load hive from id
    h = Hive.Hive("Temp")
    h.load(id)

    h.query("How to write better code", 3)

def test3():
    # Clear History
    id ="1eaa8d8f-c855-11f0-ba2b-8eb6c9366e60"
    h = Hive.Hive("Temp")
    h.load(id)
    h.clear_history()
    h.log_properties()


def list_hives():
    """List all available hives"""
    if not os.path.exists("hives"):
        print("No hives directory found.")
        return []
    
    hives = []
    for filename in os.listdir("hives"):
        if filename.startswith("hive_") and filename.endswith(".json"):
            hive_id = filename[5:-5]  # Remove "hive_" prefix and ".json" suffix
            try:
                with open(f"hives/{filename}", "r") as f:
                    data = json.load(f)
                    hive_name = data.get("hiveName", "Unknown")
                    hives.append({"id": hive_id, "name": hive_name})
            except (json.JSONDecodeError, KeyError):
                # Skip corrupted files
                continue
    
    return hives

def create_new_hive():
    """Create a new hive"""
    while True:
        name = input("Enter hive name: ").strip()
        if not name:
            print("Hive name cannot be empty.")
            continue
        
        # Check for duplicate names
        existing_hives = list_hives()
        if any(hive["name"] == name for hive in existing_hives):
            print(f"A hive named '{name}' already exists. Please choose a different name.")
            continue
        
        break
    
    hive = Hive.Hive(name)
    print(f"Created new hive: {name} (ID: {hive.hiveID})")
    input("\nPress Enter to continue...")
    return hive

def load_existing_hive():
    """Load an existing hive"""
    hives = list_hives()
    if not hives:
        print("No existing hives found.")
        return None
    
    print("\nAvailable hives:")
    for i, hive in enumerate(hives, 1):
        print(f"{i}. {hive['name']} (ID: {hive['id']})")
    
    try:
        choice_input = input("\nSelect hive number (or b to back): ").strip()
        
        if choice_input.lower() == 'b':
            return None
        
        choice = int(choice_input) - 1
        if choice == -1:
            print("Operation cancelled.")
            return None
        if 0 <= choice < len(hives):
            hive_id = hives[choice]['id']
            temp_hive = Hive.Hive("Temp")
            temp_hive.load(hive_id)
            print(f"Loaded hive: {temp_hive.hiveName} (ID: {hive_id})")
            return temp_hive
        else:
            print("Invalid selection.")
            return None
    except ValueError:
        print("Please enter a valid number.")

def add_model_to_hive(hive):
    """Add a new model to the hive"""
    model = input("Enter model URL: ")
    if not model:
        print("Model URL cannot be empty.")
        return
    
    hive.add_model(model)
    print(f"Added model: {model}")
    input("\nPress Enter to continue...")

def remove_model_from_hive(hive):
    """Remove a model from the hive"""
    models = hive.getModels()
    if not models:
        print("No models to remove.")
        input("\nPress Enter to continue...")
        return

    print("\nAvailable models:")
    for i, model in enumerate(models, 1):
        print(f"{i}. {model}")
    
    try:
        choice_input = input("Select model to remove (or b to back): ").strip()
        
        if choice_input.lower() == 'b':
            return

        choice = int(choice_input) - 1
        
        if 0 <= choice < len(models):
            model = models[choice]
            confirm = input(f"Are you sure you want to remove '{model}'? This will detach it from all bees using it. (Y/n): ").lower()
            if confirm == '' or confirm == 'y':
                hive.remove_model(model)
                print(f"Removed model: {model}")
                input("\nPress Enter to continue...")
            else:
                print("Operation cancelled.")
                input("\nPress Enter to continue...")
        else:
            print("Invalid selection.")
    except ValueError:
        print("Please enter a valid number.")

def manage_bees(hive):
    """Manage bees in the hive"""
    while True:
        print("\n--- Bee & Queen Management ---")
        print(f"Current bees in {hive.hiveName}:")
        
        if not hive.getBees():
            print("No bees in hive.")
        else:
            for i, bee in enumerate(hive.getBees(), 1):
                model_status = f"Model: {bee.get_model()}" if bee.get_model() else "No model attached"
                print(f"{i}. {bee.get_name()} ({bee.get_role()}) - {model_status}")
        
        # Show queen info
        queen = hive.getQueen()
        print(f"\nQueen: {queen.role} - Model: {queen.get_model() or 'No model attached'}")
        
        print("\nManagement Options:")
        print("1. Add new bee")
        print("2. Edit existing bee")
        print("3. Remove bee")
        print("4. Configure queen")
        print("5. Log all bees and queen")
        
        try:
            choice_input = input("\nEnter your choice (or b to back): ").strip()
            
            if choice_input.lower() == 'b':
                break
            
            choice = int(choice_input)
            
            if choice == 1:
                add_bee_to_hive(hive)
            elif choice == 2:
                edit_bee(hive)
            elif choice == 3:
                remove_bee_from_hive(hive)
            elif choice == 4:
                configure_queen(hive)
            elif choice == 5:
                log_all_bees(hive)
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a valid number.")

def add_bee_to_hive(hive):
    """Add a new bee to the hive"""
    name = input("Enter bee name: ").strip()
    role = input("Enter bee role: ").strip()
    
    if not name or not role:
        print("Name and role cannot be empty.")
        return
    
    bee = Bee.Bee(name, role)
    
    # Ask for model attachment
    models = hive.getModels()
    if models:
        print("\nAvailable models:")
        for i, model in enumerate(models, 1):
            print(f"{i}. {model}")
        
        try:
            model_choice = int(input("Select model (or 0 to skip): ")) - 1
            if 0 <= model_choice < len(models):
                bee.attach_model(models[model_choice])
                print(f"Attached model: {models[model_choice]}")
            elif model_choice == -1:
                print("No model attached.")
        except ValueError:
            print("No model attached.")
    
    # Ask for injections
    while True:
        add_injection = input("\nAdd injection? (Y/n): ").lower()
        if add_injection == 'n':
            break
        
        behaviour = input("Enter injection behaviour: ").strip()
        if not behaviour: 
             print("Behaviour cannot be empty.")
             continue

        try:
            interval = int(input("Enter injection interval (1-10): "))
            if 1 <= interval <= 10:
                bee.addInjection(behaviour, interval)
                print(f"Added injection: {behaviour} (interval: {interval})")
            else:
                print("Interval must be between 1 and 10.")
        except ValueError:
            print("Please enter a valid number.")

    hive.add_bee(bee)
    print(f"Added bee '{name}' to hive.")
    input("\nPress Enter to continue...")

def edit_bee(hive):
    """Edit an existing bee"""
    bees = hive.getBees()
    if not bees:
        print("No bees to edit.")
        input("\nPress Enter to continue...")
        return
    
    print("\nSelect bee to edit:")
    for i, bee in enumerate(bees, 1):
        print(f"{i}. {bee.get_name()} ({bee.get_role()})")
    
    try:
        choice_input = input("\nEnter bee number (or b to back): ").strip()
        if choice_input.lower() == 'b':
            return
            
        choice = int(choice_input) - 1
        if choice == -1:
            return
        if 0 <= choice < len(bees):
            bee = bees[choice]
            print(f"\nEditing bee: {bee.get_name()}")
            print(f"Current role: {bee.get_role()}")
            print(f"Current model: {bee.get_model()}")
            
            print("\nWhat would you like to edit?")
            print("1. Change name")
            print("2. Change role")
            print("3. Change model")
            print("4. Manage injections")
            
            choice_input = input("Enter your choice (or b to back): ").strip()
            if choice_input.lower() == 'b':
                return

            edit_choice = int(choice_input)
            
            if edit_choice == 1:
                new_name = input("Enter new name: ").strip()
                if new_name:
                    bee.set_name(new_name)
                    print(f"Bee name changed to: {new_name}")
            elif edit_choice == 2:
                new_role = input("Enter new role: ").strip()
                if new_role:
                    bee.set_role(new_role)
                    print(f"Bee role changed to: {new_role}")
            elif edit_choice == 3:
                models = hive.getModels()
                if models:
                    print("\nAvailable models:")
                    for i, model in enumerate(models, 1):
                        print(f"{i}. {model}")
                    print("0. Remove model")
                    
                    choice_input = input("Select model (or 0 to remove, b to back): ").strip()
                    
                    if choice_input.lower() != 'b':
                        try:
                            model_choice = int(choice_input) - 1
                            if model_choice == -1:
                                bee.detach_model()
                                print("Model removed from bee.")
                            elif 0 <= model_choice < len(models):
                                bee.attach_model(models[model_choice])
                                print(f"Attached model: {models[model_choice]}")
                            else:
                                print("Invalid selection.")
                        except ValueError:
                            print("Invalid selection.")
                else:
                    print("No models available. Add models to hive first.")
            elif edit_choice == 4:
                manage_injections(bee)
            
            hive.updateLastModified()
            hive.save()
        else:
            print("Invalid selection.")
    except ValueError:
        print("Please enter a valid number.")

def manage_injections(bee):
    """Manage injections for a bee"""
    while True:
        print(f"\n--- Injections for {bee.get_name()} ---")
        injections = bee.get_injections()
        
        if not injections:
            print("No injections configured.")
        else:
            for i, injection in enumerate(injections, 1):
                print(f"{i}. {injection['behaviour']} (interval: {injection['interval']})")
        
        print("\nInjection Management Options:")
        print("1. Add injection")
        print("2. Remove injection")
        
        try:
            choice_input = input("Enter your choice (or b to back): ").strip()
            if choice_input.lower() == 'b':
                break
            
            choice = int(choice_input)
            
            if choice == 1:
                behaviour = input("Enter injection behaviour: ").strip()
                if behaviour:
                    interval = int(input("Enter injection interval (1-10): "))
                    if 1 <= interval <= 10:
                        bee.addInjection(behaviour, interval)
                        print(f"Added injection: {behaviour} (interval: {interval})")
                    else:
                        print("Interval must be between 1 and 10.")
                        input("\nPress Enter to continue...")
            elif choice == 2:
                if injections:
                    inj_choice = int(input("Enter injection number to remove: ")) - 1
                    if 0 <= inj_choice < len(injections):
                        removed = injections.pop(inj_choice)
                        print(f"Removed injection: {removed['behaviour']}")
                        input("\nPress Enter to continue...")
                    else:
                        print("Invalid selection.")
                else:
                    print("No injections to remove.")
            else:
                print("Invalid choice.")
        except ValueError:
            print("Please enter a valid number.")

def remove_bee_from_hive(hive):
    """Remove a bee from the hive"""
    bees = hive.getBees()
    if not bees:
        print("No bees to remove.")
        input("\nPress Enter to continue...")
        return
    
    print("\nSelect bee to remove:")
    for i, bee in enumerate(bees, 1):
        print(f"{i}. {bee.get_name()} ({bee.get_role()})")
    
    try:
        choice_input = input("\nEnter bee number (or b to back): ").strip()
        if choice_input.lower() == 'b':
            return

        choice = int(choice_input) - 1
        if choice == -1:
            return
        if 0 <= choice < len(bees):
            bee = bees[choice]
            confirm = input(f"Are you sure you want to remove '{bee.get_name()}'? (Y/n): ").lower()
            if confirm == '' or confirm == 'y':
                hive.remove_bee(bee)
                print(f"Removed bee: {bee.get_name()}")
                input("\nPress Enter to continue...")
            else:
                print("Operation cancelled.")
            input("\nPress Enter to continue...")
        else:
            print("Invalid selection.")
    except ValueError:
        print("Please enter a valid number.")

def log_all_bees(hive):
    """Log all bees and queen details"""
    print("\n" + "="*80)
    print(f"COMPLETE BEE LOG FOR HIVE: {hive.hiveName}")
    print("="*80)
    
    # Log Queen
    queen = hive.getQueen()
    print(f"\n👑 QUEEN:")
    print(f"   Name: Queen")
    print(f"   Role: {queen.role}")
    print(f"   Model: {queen.get_model() or 'No model attached'}")
    
    # Log Bees
    bees = hive.getBees()
    if bees:
        print(f"\n🐝 BEES ({len(bees)} total):")
        for i, bee in enumerate(bees, 1):
            print(f"\n   Bee #{i}:")
            print(f"   Name: {bee.get_name()}")
            print(f"   Role: {bee.get_role()}")
            print(f"   Model: {bee.get_model() or 'No model attached'}")
            
            injections = bee.get_injections()
            if injections:
                print(f"   Injections ({len(injections)}):")
                for j, injection in enumerate(injections, 1):
                    print(f"      {j}. {injection['behaviour']} (interval: {injection['interval']})")
            else:
                print(f"   Injections: None")
    else:
        print("\n🐝 BEES: No bees in hive")
    
    print("\n" + "="*80)
    print("End of Bee Log")
    print("="*80)
    
    input("\nPress Enter to continue...")

def configure_queen(hive):
    """Configure the queen bee"""
    queen = hive.getQueen()
    print(f"\n--- Queen Configuration ---")
    print(f"Current role: {queen.role}")
    print(f"Current model: {queen.get_model()}")
    
    print("\nQueen Configuration Options:")
    print("1. Change queen role")
    print("2. Change queen model")
    
    try:
        choice_input = input("\nEnter your choice (or b to back): ").strip()
        if choice_input.lower() == 'b':
            return
        
        choice = int(choice_input)
        
        if choice == 1:
            new_role = input("Enter new queen role: ").strip()
            if new_role:
                queen.set_role(new_role)
                print(f"Queen role changed to: {new_role}")
                hive.updateLastModified()
                hive.save()
                input("\nPress Enter to continue...")
        elif choice == 2:
            models = hive.getModels()
            if models:
                print("\nAvailable models:")
                for i, model in enumerate(models, 1):
                    print(f"{i}. {model}")
                print("0. Remove model")
                
                choice_input = input("Select model (or 0 to remove, b to back): ").strip()
                
                if choice_input.lower() == 'b':
                    return  # Return to queen configuration menu
                
                try:
                    model_choice = int(choice_input) - 1
                    if model_choice == -1:
                        queen.detach_model()
                        print("Model removed from queen.")
                    elif 0 <= model_choice < len(models):
                        queen.attach_model(models[model_choice])
                        print(f"Attached model to queen: {models[model_choice]}")
                    else:
                        print("Invalid selection.")
                    hive.updateLastModified()
                    hive.save()
                    input("\nPress Enter to continue...")
                except ValueError:
                    print("Invalid selection.")
            else:
                print("No models available. Add models to hive first.")
                input("\nPress Enter to continue...")
        else:
            print("Invalid choice.")
    except ValueError:
        print("Please enter a valid number.")

def query_hive(hive):
    """Query the hive with user input"""
    # Check if queen has a model
    if not hive.getQueen().get_model():
        print("Please configure the queen model first.")
        input("\nPress Enter to continue...")
        return
    
    # Check if all bees have models
    bees_without_models = [bee for bee in hive.getBees() if not bee.get_model()]
    if bees_without_models:
        print("Cannot query: The following bees do not have models attached:")
        for bee in bees_without_models:
            print(f"  - {bee.get_name()}")
        print("Please configure models for all bees first.")
        input("\nPress Enter to continue...")
        return
    
    prompt = input("Enter your query: ")
    if not prompt:
        print("Query cannot be empty.")
        return
    
    try:
        rounds = int(input("Enter number of rounds (1-10): "))
        if not 1 <= rounds <= 10:
            print("Number of rounds must be between 1 and 10.")
            input("\nPress Enter to continue...")
            return
    except ValueError:
        print("Please enter a valid number.")
        input("\nPress Enter to continue...")
        return
    
    print("\n" + "="*80)
    response = hive.query(prompt, rounds)
    print("="*80)
    print(f"\nFinal Response: {response}")
    
    input("\nPress Enter to continue...")

def show_hive_info(hive):
    """Show hive information"""
    print(f"\nHive Information:")
    print(f"Name: {hive.hiveName}")
    print(f"ID: {hive.hiveID}")
    print(f"Models: {len(hive.getModels())}")
    print(f"Bees: {len(hive.getBees())}")
    print(f"History entries: {len(hive.history)}")
    print(f"Sequential: {hive.sequential}")
    print(f"Randomize: {hive.randomize}")
    print(f"Last modified: {hive.lastModified}")
    
    # Show queen info
    queen = hive.getQueen()
    print(f"\nQueen:")
    print(f"  Role: {queen.role}")
    print(f"  Model: {queen.get_model() or 'No model attached'}")
    
    # Show bee details
    if hive.getBees():
        print(f"\nBees:")
        for bee in hive.getBees():
            print(f"  - {bee.get_name()} ({bee.get_role()})")
            print(f"    Model: {bee.get_model() or 'No model attached'}")
            print(f"    Injections: {len(bee.get_injections())}")
    
    input("\nPress Enter to continue...")

def clear_hive_history(hive):
    """Clear hive history"""
    confirm = input("Are you sure you want to clear the history? (Y/n): ").lower()
    if confirm == '' or confirm == 'y':
        hive.clear_history()
        print("History cleared.")
        input("\nPress Enter to continue...")
    else:
        print("Operation cancelled.")
        input("\nPress Enter to continue...")

def delete_hive():
    """Delete an existing hive"""
    hives = list_hives()
    if not hives:
        print("No existing hives found.")
        input("\nPress Enter to continue...")
        return
    
    print("\nAvailable hives:")
    for i, hive in enumerate(hives, 1):
        print(f"{i}. {hive['name']} (ID: {hive['id']})")
    
    try:
        choice_input = input("\nSelect hive to delete (or b to back): ").strip()
        
        if choice_input.lower() == 'b':
            return
        
        choice = int(choice_input) - 1
        if 0 <= choice < len(hives):
            hive = hives[choice]
            confirm = input(f"Are you sure you want to delete '{hive['name']}'? This cannot be undone. (Y/n): ").lower()
            if confirm == '' or confirm == 'y':
                Hive.Hive.deleteHive(hive['id'])
                print(f"Deleted hive: {hive['name']} (ID: {hive['id']})")
                input("\nPress Enter to continue...")
            else:
                print("Operation cancelled.")
                input("\nPress Enter to continue...")
        else:
            print("Invalid selection.")
            input("\nPress Enter to continue...")
    except ValueError:
        print("Please enter a valid number.")

def show_help():
    """Display comprehensive help information about the HiveMind LLM system"""
    print("\n" + "="*80)
    print("🐝 HIVEMIND CLI MANUAL")
    print("="*80)
    
    print("\n📋 QUICK START")
    print("-" * 40)
    print("1. Create a Hive: [1] Hive Management -> [1] Create new hive")
    print("2. Add Models:    [1] Hive Management -> [4] Add model to hive")
    print("3. Config Bees:   [2] Bee & Queen Management -> [1] Add new bee")
    print("   (Assign roles like 'Critic' or 'Researcher' and attach models)")
    print("4. Config Queen:  [2] Bee & Queen Management -> [4] Configure queen")
    print("   (The Queen needs a model to synthesize results)")
    print("5. Run Query:     [3] Query & Analysis -> [1] Query hive")
    
    print("\n🏗️ ARCHITECTURE")
    print("-" * 40)
    print("• HIVE:  The container for your session. Saves history and configuration.")
    print("• BEES:  Worker agents. They debate, research, and generate content.")
    print("         Each bee has a ROLE (instruction) and a MODEL (endpoint).")
    print("• QUEEN: The coordinator. She reads history, facilitates the discussion,")
    print("         and writes the final summary.")
    
    print("\n📝 SAMPLE INTERACTION LOG")
    print("-" * 40)
    print("############################# HIVE CONFIGURATION ########################################")
    print("[Debug] Querying Hive 1 with prompt: How to survive a beer attack?")
    print("[Debug] Number of bees: 2")
    print("[Debug] Number of rounds: 3")
    print("############################ FETCH CONTEXT #########################################")
    print("[Debug] Queen is thinking...")
    print("[Debug] <Context Fetched by Queen>")
    print("############################## START OF DISCUSSION #######################################")
    print("")
    print("### Round 1 ###")
    print("[Debug] Creative bee is thinking...")
    print("[Debug] 🎲 Injection 'Disagree with previous speaker' successful for Creative Bee")
    print("[Debug] <Creative Bee Reply>")
    print("")
    print("[Debug] Pragmatic bee is thinking...")
    print("[Debug] <Pragmatic Bee Reply>")
    print("")
    print("############################# END OF DISCUSSION ########################################")
    print("[Debug] Queen is thinking...")
    print("[Debug] Queen 👑: <Aggregated Queen Response>")
    print("[Debug] Hive 1 history updated")
    print("[Debug] Hive 1 saved")
    
    print("\n" + "="*80)
    print("Tip: Use 'Injections' to force specific behaviors at random intervals!")
    print("="*80)
    
    input("\nPress Enter to continue...")

def cli():
    """Main CLI interface"""
    current_hive = None
    
    while True:
        print("\n" + "="*50)
        print("HIVE AI CLI")
        print("="*50)
        
        if current_hive:
            print(f"Current hive: {current_hive.hiveName} (ID: {current_hive.hiveID})")
        
        print("\nOptions:")
        print("1. Hive Management")
        print("2. Bee & Queen Management")
        print("3. Query & Analysis")
        print("4. Help")
        
        try:
            choice_input = input("\nEnter your choice (or q to exit): ").strip()
            
            # Handle 'q' for exit
            if choice_input.lower() == 'q':
                print("Goodbye!")
                break
            
            choice = int(choice_input)
            
            if choice == 1:
                current_hive = hive_management_menu(current_hive)
            elif choice == 2:
                if current_hive:
                    current_hive = bee_queen_management_menu(current_hive)
                else:
                    print("No hive loaded. Please create or load a hive first.")
                    input("\nPress Enter to continue...")
            elif choice == 3:
                if current_hive:
                    query_analysis_menu(current_hive)
                else:
                    print("No hive loaded. Please create or load a hive first.")
                    input("\nPress Enter to continue...")
            elif choice == 4:
                show_help()
            else:
                print("Invalid choice. Please try again.")
                
        except ValueError:
            print("Please enter a valid number.")
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

def hive_management_menu(current_hive):
    """Hive management submenu"""
    while True:
        print("\n" + "="*40)
        print("HIVE MANAGEMENT")
        print("="*40)
        
        if current_hive:
            print(f"Current: {current_hive.hiveName}")
        
        print("\nOptions:")
        print("1. Create new hive")
        print("2. Load existing hive")
        print("3. List all hives")
        print("4. Show hive info")
        print("5. Add model to hive")
        print("6. Remove model from hive")
        print("7. Delete hive")
        
        choice_input = input("\nEnter your choice (or b to back): ").strip()
        
        if choice_input.lower() == 'b':
            break
        
        try:
            choice = int(choice_input)
            
            if choice == 1:
                current_hive = create_new_hive()
            elif choice == 2:
                current_hive = load_existing_hive()
            elif choice == 3:
                hives = list_hives()
                if hives:
                    print(f"\nFound {len(hives)} hives:")
                    for hive in hives:
                        print(f"  - {hive['name']} (ID: {hive['id']})")
                    input("\nPress Enter to continue...")
                else:
                    print("No hives found.")
                    input("\nPress Enter to continue...")
            elif choice == 4:
                if current_hive:
                    show_hive_info(current_hive)
                else:
                    print("No hive loaded.")
                    input("\nPress Enter to continue...")
            elif choice == 5:
                if current_hive:
                    add_model_to_hive(current_hive)
                else:
                    print("No hive loaded.")
                    input("\nPress Enter to continue...")
            elif choice == 6:
                if current_hive:
                    remove_model_from_hive(current_hive)
                else:
                    print("No hive loaded.")
                    input("\nPress Enter to continue...")
            elif choice == 7:
                delete_hive()
                # Clear current hive if it was deleted
                if current_hive:
                    hives = list_hives()
                    if not any(hive['id'] == current_hive.hiveID for hive in hives):
                        current_hive = None
                        print("Current hive was deleted. No hive loaded.")
            else:
                print("Invalid choice.")
        except ValueError:
            print("Please enter a valid number.")
    
    return current_hive

def bee_queen_management_menu(current_hive):
    """Bee and queen management submenu"""
    manage_bees(current_hive)
    return current_hive

def query_analysis_menu(current_hive):
    """Query and analysis submenu"""
    while True:
        print("\n" + "="*40)
        print("QUERY & ANALYSIS")
        print("="*40)
        print(f"Hive: {current_hive.hiveName}")
        
        print("\nOptions:")
        print("1. Query hive")
        print("2. Clear hive history")
        
        choice_input = input("\nEnter your choice (or b to back): ").strip()
        
        if choice_input.lower() == 'b':
            break
        
        try:
            choice = int(choice_input)
            
            if choice == 1:
                query_hive(current_hive)
            elif choice == 2:
                clear_hive_history(current_hive)
            else:
                print("Invalid choice.")
        except ValueError:
            print("Please enter a valid number.")
    
    return current_hive

if __name__ == "__main__":
    cli()