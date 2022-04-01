import instaloader
import os
import linecache as lc
import getpass

from print import *
from pathlib import Path
from features import IgpdLinuxFeaturesPrivate as IGFP
from features import IgpdLinuxFeaturesPublic as IGFPU

#loading instance var instaloader
instance = instaloader.Instaloader()


ch_dr = os.path.isdir(str(Path.home())+"/.igpd/user_data/") 
if ch_dr == False:
	os.mkdir(str(Path.home())+"/.igpd/")
	os.mkdir(str(Path.home())+"/.igpd/user_data")

# user data stored location along with the home path
main_path = os.path.join(str(Path.home())+"/.igpd/user_data/")

print("Welcome to igpd-l", SM,GREEN)

def main():
    print("\n1. Download your follower's (POST/STORY/REELS/IGTV/HIGHLIGHTS/ENTIRE_PROFILE) by typing 1",GREEN)
    print("2. Download a public account's(POST/IGTV/ENTIRE_PROFILE) by typing 2",GREEN)

    print("\n")

    c1 = int(input("Enter your choice: "))

    def login():
        counter = 0
        if c1 == 1:
            name = input("Enter username: ")       
            counter+=1
            if counter>1:
                ask_options()
        else:
            pass
        
        if c1 == 1:
            if "."+name+".txt" in os.listdir(main_path):
                print("User data exists",GREEN)
                print("type 'yes' to continue or type 'no' in case you have changed your password or previously typed in wrong password or username",RED)
                c_i = input("(yes/no): ")
                if c_i == "yes":
                    username = str(lc.getline(main_path+"."+name+".txt",1).strip("\n"))
                    password = str(lc.getline(main_path+"."+name+".txt",2).strip("\n"))
                    instance.login(user=username,passwd=password)
                    print("\nLogin successful")
                elif c_i == "no":
                    c_username = input("Enter username: ")
                    passwo = getpass.getpass("Enter password: ")
                    with open(main_path+"."+c_username+".txt","w") as l_data:
                        l_data.write(c_username+"\n")
                        l_data.write(passwo)
                
                    
                    username = str(lc.getline(main_path+"."+name+".txt",1).strip("\n"))
                    password = str(lc.getline(main_path+"."+name+".txt",2).strip("\n"))
                    instance.login(user=username,passwd=password) 
                    print("\n Login successful")
                        
                else:
                    exit()    
            else:
                passwo = getpass.getpass("Enter password: ")
                with open(main_path+"."+name+".txt","w") as l_data:
                    l_data.write(name+"\n")
                    l_data.write(passwo)
                    l_data.close()
                
                username = str(lc.getline(main_path+"."+name+".txt",1).strip("\n"))
                password = str(lc.getline(main_path+"."+name+".txt",2).strip("\n"))
                     
                print("\nLogin successful")
    login()

    def ask_options():
        div.div('-')
        if c1 == 1:
            print("a: Download a (Post/Reels/IGTV)",YELLOW)
            print("b: Dowload story",YELLOW)
            print("c: Dowload highlights",YELLOW)
            print("d: Download entire Profile",YELLOW)
            print("e: exit",YELLOW)
        elif c1 == 2:
            print("a: Download a (Post/IGTV)",YELLOW)
            print("b: Dowload story (Not avalibale)",RED)
            print("c: Dowload highlights (Not available)",RED)
            print("d: Download entire Profile",YELLOW)
            print("e: exit",YELLOW)
        else:
            exit()


        option = input("\nEnter your choice: ")

        if option == 'a' and c1 == 1:
            url = input("Enter url of(Post/Story/IGTV): ")
            url_obj = IGFP()
            url_obj.download_post(url,instance)

            a_continue = input("Do you wanna continue(yes/no): ")
            
            if a_continue == "yes":
                main()
            elif a_continue == "no":
                main()
            else:
                exit()

        elif option == 'a' and c1 == 2:
            url = input("Enter url of(Post/Story/IGTV): ")
            url_obj = IGFPU()
            url_obj.download_pri(url)

            a_continue = input("Do you wanna continue(yes/no): ")
            
            if a_continue == "yes":
                main()
            elif a_continue == "no":
                exit()
            else:
                exit()


        elif option == 'b' and c1 == 1:
            s_username = input("Enter the username of the story's owner: ")

            story_obj = IGFP()
            story_obj.download_story(s_username,instance)

            conti_2 = input("\nDo you want to continue(yes/no): ")

            if conti_2 == 'yes':
                main()
            else:
                quit() 
        elif option == 'b' and c1==2:
            print("Not available")

            conti_2 = input("\nDo you want to continue(yes/no): ")

            if conti_2 == 'yes':
                main()
            else:
                quit()

        elif option == 'c' and c1 == 1:
            h_username = input("Enter the username of the hightlight's owner: ")

            high_obj = IGFP()
            high_obj.download_highlights(h_username,instance)

            conti_3 = input("\nDo you want to continue(yes/no): ")

            if conti_3 == 'yes':
                main()
            else:
                quit() 

        elif option == 'c' and c1 == 2:
            print("Not available")

            conti_3 = input("\nDo you want to continue(yes/no): ")

            if conti_3 == 'yes':
                main()
            else:
                quit() 

        elif option == 'd' and c1 == 1:
            p_username = input("Enter the username of the profile's owner: ")

            profile_obj = IGFP()
            profile_obj.download_profile(p_username,instance)

            conti_4 = input("\nDo you want to continue(yes/no): ")

            if conti_4 == 'yes':
                main()
            else:
                quit() 
        elif option == 'd' and c1==2:
            p_username = input("Enter the username of the profile's owner: ")

            profile_obj = IGFPU()
            profile_obj.download_profile(p_username)

            conti_4 = input("\nDo you want to continue(yes/no): ")

            if conti_4 == 'yes':
                main()
            else:
                quit() 

        elif option == 'e':
            quit()
        else:
            pass

    ask_options()

main()

