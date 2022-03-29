import numpy as np
import urllib.request
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.colors as mcolors
import os 

class Person(object):
    def __init__(self):
        pass
    
class Attributes(Person):
    '''class that creates a person'''
    
    def __init__(self, name, relation):
        """
        Function to initialize the class
        """
        # let's initalize it's parent class (empty for now because it is a blank class)
        super().__init__()
        self.name = name # name of the person
        self.relation = relation # relation: friend/sister/cousin/etc...
        self.fav_food = 0 
        self.fav_animal = 0 
        self.fav_activity = 0


    def Fav_food(self, food):
        """
        Function that updates favorite food information 
        """
        self.fav_food = food 
    
    def Fav_animal(animal):
        """
        Function that updates favorite animal information 
        """
        self.fav_animal = animal 
    
    def Fav_activity(activity):
        """
        Function that updates favorite activity information 
        """
        self.fav_activity = activity
    
    def Bday_text(self):
        '''
        Function that choses the random txt that is printed on the card
        '''
        assert type(self.name) == str 
        assert type(self.relation) == str

        assert len(self.name) <= 35 and len(self.name) >= 2
        assert len(self.relation) <= 35 and len(self.relation) >= 2
        
        opening_pool = ["Dear ", "Lovely ", "Beloved ", "Dearest ", "Much-loved "]
        op_i = np.random.randint(len(opening_pool))
        adjetive_pool = [" you're a great ", " you're the best ", " you're my favorite ",
                        " you're an awesome "]
        adj_i = np.random.randint(len(adjetive_pool))
        happy_wishes_pool = [" and you deserve the BEST day ever \n for your B-day.",
                             " and you deserve to have a very nice day \n because today is your B-day.",
                             " and I wish you the BEST day ever \n for your B-day.",
                             " and I wish that today you have a great day \n 'couse today is your B-day!"]
        hw_i = np.random.randint(len(happy_wishes_pool))
        
        intro = opening_pool[op_i] + self.name + ', \n' + adjetive_pool[adj_i] + self.relation + ' \n' + happy_wishes_pool[hw_i] +'\n'
        
        interlude_pool = ['The world is incomplete without you.', 
                         'A world witout you is not a place where I wanna live.', 
                         'You make my world meaningful.',
                         'Life is beautiful with you.',
                         'We always have a lot of fun together.',
                         'Your memes and jokes always makes me laugh.']
        in_i = np.random.randint(len(interlude_pool))
        Hbday = intro + interlude_pool[in_i]+ '\n'

        if self.fav_animal != 0:
            assert type(self.fav_animal) == str
            assert len(self.fav_animal) <= 20 and len(self.fav_animal) >= 2

            body1_pool = ['pet ', 'love ', 'take care of ', 'admire ', 'hug ']
            bd1_i = np.random.randint(len(body1_pool))
            body1 = "Who would "+ body1_pool[bd1_i] + self.fav_animal + " like you do? \n"
            Hbday = Hbday+body1

        if self.fav_food != 0:
            assert type(self.fav_food) == str
            assert len(self.fav_food) <= 35 and len(self.fav_food) >= 2

            body2_verb_pool = ['eat', 'enjoy', 'devour', 'eat voraciously']
            bd2_v_i = np.random.randint(len(body2_verb_pool))
            body2_pool = [' leftover ', ' ', ' fresh cooked ']
            bd2_i = np.random.randint(len(body2_pool))
            body2 = " Who else would " + body2_verb_pool[bd2_v_i]  + body2_pool[bd2_i] + ' \n' + self.fav_food + " like you do? \n"
            Hbday = Hbday + body2

        if self.fav_activity != 0:
            assert type(self.fav_activity) == str
            assert len(self.fav_activity) <= 35 and len(self.fav_activity) >= 2

            body3_pool = [" Who will inspire the " + self.fav_activity + ' \n' + " enthusiasts like you do?"]
            bd3_i = np.random.randint(len(body3_pool))
            Hbday = Hbday + body3_pool[bd3_i] + ' \n'

        final_pool = [" Stay alive and keep being YOU <3 love xoxo", 
                      ' I will always look forward to see you again <3',
                      ' Keep being yourself, lots of love', 
                      ' Best wishes, see you around :D']
        fin_i = np.random.randint(len(final_pool))
        Hbday = Hbday + final_pool[fin_i]
        return Hbday
    
    def Bday_card(self, color):
        '''
        Function that computes a costum b-card given the inputs
        '''
        links = ['https://cdn.pixabay.com/photo/2019/05/21/07/11/cat-4218424_960_720.jpg',
                'https://cdn.pixabay.com/photo/2016/11/23/14/22/ducklings-1853178_960_720.jpg',
                'https://cdn.pixabay.com/photo/2017/05/18/15/05/chipmunk-2323827_960_720.jpg',
                'https://cdn.pixabay.com/photo/2016/10/21/19/45/hedgehog-1759027_960_720.jpg',
                'https://cdn.pixabay.com/photo/2016/11/13/21/46/sheep-1822137_960_720.jpg',
                'https://cdn.pixabay.com/photo/2014/04/13/20/49/cat-323262_960_720.jpg',
                'https://cdn.pixabay.com/photo/2014/04/13/20/49/cat-323262_960_720.jpg',
                'https://cdn.pixabay.com/photo/2014/10/01/10/44/hedgehog-468228_960_720.jpg',
                'https://cdn.pixabay.com/photo/2017/07/25/01/22/cat-2536662_960_720.jpg',
                'https://cdn.pixabay.com/photo/2015/10/01/20/28/animal-967657_960_720.jpg',
                'https://cdn.pixabay.com/photo/2020/02/05/15/19/meerkat-4821484_960_720.jpg',
                'https://cdn.pixabay.com/photo/2016/11/23/01/15/red-panda-1851650_960_720.jpg',
                'https://cdn.pixabay.com/photo/2013/02/11/15/54/squirrel-80575_960_720.jpg',
                'https://cdn.pixabay.com/photo/2020/06/22/08/27/cat-5328304_960_720.jpg',
                'https://cdn.pixabay.com/photo/2019/07/24/14/17/monkey-4360298_960_720.jpg',
                'https://cdn.pixabay.com/photo/2019/09/16/14/43/seal-4481175_960_720.jpg',
                'https://cdn.pixabay.com/photo/2020/12/03/05/23/lion-5799523_960_720.jpg',
                'https://cdn.pixabay.com/photo/2018/01/16/06/37/wildlife-3085394_960_720.jpg',
                'https://cdn.pixabay.com/photo/2020/07/03/10/44/horses-5365974_960_720.jpg',
                'https://cdn.pixabay.com/photo/2019/03/01/16/07/pigs-4028140_960_720.jpg',
                'https://cdn.pixabay.com/photo/2014/08/27/12/58/emperor-penguins-429128_960_720.jpg',
                'https://cdn.pixabay.com/photo/2018/03/31/11/37/polar-bear-3277930_960_720.jpg',
                'https://cdn.pixabay.com/photo/2012/09/04/21/20/penguin-56101_960_720.jpg',
                'https://cdn.pixabay.com/photo/2014/11/23/16/12/guinea-pig-542917_960_720.jpg',
                'https://cdn.pixabay.com/photo/2016/12/03/15/11/sloth-1879999_960_720.jpg',
                'https://cdn.pixabay.com/photo/2016/03/04/22/54/panda-1236875_960_720.jpg',
                'https://cdn.pixabay.com/photo/2017/10/07/15/27/wolf-2826741_960_720.jpg',
                'https://cdn.pixabay.com/photo/2017/07/24/19/57/tiger-2535888_960_720.jpg',
                'https://cdn.pixabay.com/photo/2018/07/13/10/20/cat-3535404_960_720.jpg',
                'https://cdn.pixabay.com/photo/2015/02/25/17/56/cat-649164_960_720.jpg',
                'https://cdn.pixabay.com/photo/2017/01/20/21/22/kitten-asleep-in-a-pot-1995961_960_720.jpg']
        
        i = np.random.randint(len(links))
        opener = urllib.request.URLopener()
        opener.addheader('User-Agent', 'whatever')
        path_hrb = './cute_images/'

        if (os.path.isdir(path_hrb)==False):
            os.mkdir(path_hrb)
            pass

        filename, headers = opener.retrieve(links[i],path_hrb + "cute_{}.jpg".format(i))



        img = mpimg.imread(path_hrb + "cute_{}.jpg".format(i))
        
        cute_img = plt.figure(figsize = (15,15)) 
        ax = plt.subplot(111)
        plt.imshow(img)
        t = plt.text(0.5, 0.3, self.Bday_text() , transform=ax.transAxes, fontsize=25, 
                     color = color, ha='center', va='center') 
        t.set_bbox(dict(facecolor='white', alpha=0.5, edgecolor=color, boxstyle="round"))
        plt.axis('off')
        plt.show()
        #plt.savefig('.././Bday-cards/B-day_costum_random_card_' + self.name + '.png', 
        #            DPI=400, bbox_inches='tight')

def run_interactive_mesages():
    '''runs the code to display the interacticve messages and create the card'''
    name = input('What is their name? ')
    relation = input('How does '+name+' relate to you? (sister/cousin/aunt..) ')
    print('Answer the following questions if you know the answer. If you do not know, write None ')
    person = Attributes(name, relation)

    f_food = input('Do you know their favorite food? ')
    if f_food != 'None':
        person.fav_food = f_food

    f_activity = input('Do you know their favorite activity? (please write is as an -ing verb) ')
    if f_activity != 'None':
        person.fav_activity = f_activity
    
    f_animal = input('What is your favorite animal? ')
    if f_animal != 'None':
        person.fav_animal = f_animal
    
    color = input('----------------------\n'
                  +'what color do you want for the font? (blue/purple/black/cyan/green/yellow) ')
    cond = True
    
    person.Bday_card(color)
    while cond == True:
        new_option = input('Do you want it to be different color, make one to another person or exit? (write color or other or exit) ')
        if new_option == 'color':
            color = input('input your new color choice (blue/purple/black/cyan/green/yellow): ')
        elif new_option == 'other':
            run_interactive_mesages()
            cond = False
        elif new_option == 'exit':
            cond = False

# run everything
run_interactive_mesages()
