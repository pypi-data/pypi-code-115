def helper(function='default'):
    function = function
    if function == 'pitch':
        print('1 ~ Open a new python file.')
        print('2 ~ To import RugbyPy, type: from RugbyPython import *, also import matplotlib.pyplot')
        print('3 ~ Start setting up the axis and plot with: fig=plt.figure()')
        print('4 ~ Set the size of the figure as you wish: fig.set_size_inches(x, y)')
        print('5 ~ Add subplot(s): ax=fig.add_subplot(1,1,1)')
        print('6 ~ Enter the following line and customize as wanted: pitch(ax=ax)')
        print("7 ~ Use: help('variables') to get a list of ways to customize the plot")
    
    if function == 'vertpitch':
        print('1 ~ Open a new python file.')
        print('2 ~ To import RugbyPy, type: from RugbyPython import *, also import matplotlib.pyplot')
        print('3 ~ Start setting up the axis and plot with: fig=plt.figure()')
        print('4 ~ Set the size of the figure as you wish: fig.set_size_inches(x, y)')
        print('5 ~ Add subplot(s): ax=fig.add_subplot(1,1,1)')
        print('6 ~ Enter the following line and customize as wanted: vertpitch(ax=ax)')
        print("7 ~ Use: help('variables') to get a list of ways to customize the plot")
        
    if function == 'leaguepitch':
        print('1 ~ Open a new python file.')
        print('2 ~ To import RugbyPy, type: from RugbyPython import *, also import matplotlib.pyplot')
        print('3 ~ Start setting up the axis and plot with: fig=plt.figure()')
        print('4 ~ Set the size of the figure as you wish: fig.set_size_inches(x, y)')
        print('5 ~ Add subplot(s): ax=fig.add_subplot(1,1,1)')
        print('6 ~ Enter the following line and customize as wanted: leaguepitch(ax=ax)')
        print("7 ~ Use: help('variables') to get a list of ways to customize the plot")
    
    if function == 'variables' or function == 'Variables':
        print('ax: which axis you want to plot on. Recommended to leave default or enter ax1')
        print("linecolor: what color the pitch lines will be drawn. Enter a word or color code, for example:'red' or '#ffffff'")
        print("poles: whether to display the rugby poles as a thick line. Only accepts a boolean. Default is False.")
        print("labels: text on the field to mark lines. Only accepts a boolean. Default is False.")
        print('labelalpha: the transparency of the labels. Accepts value between 0 and 1. Default is 0.5.')
        print('shadows: gives the text a slight shadow effect. Only accepts a boolean. Default is False.')
        
    if function == 'setup':
        print('fig=plt.figure()')
        print('fig.set_size_inches(12, 8)')
        print('ax=fig.add_subplot(1,1,1)')
        print('plt.ylim(-1, 71)')
        print('plt.xlim(-1, 101)')
        print()
        print()
        print('Currently the setup function x and y limits do not work with vertical pitches. ')
    
    if function == 'default':
        print('For more information on how to use this package, visit the RugbyPython GitHub page. For help on a function type helper(FUNCTION)')
    
    if function != 'pitch' and function != 'vertpitch' and function != 'default' and function != 'setup' and function != 'leaguepitch' and function != 'variables' and function != 'Variables':
        print('Error, function not found.')
    
def vertpitch(ax='ax', pitchcolor = 'white', linecolor='Black', poles=False, linestyle='--', labels=False, labelalpha=0.5, shadows=False, linealpha=0.2):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, ConnectionPatch
    import matplotlib.patheffects as path_effects
    
    color = linecolor
    lalpha = linealpha
    linestyle = linestyle
    
    ax.add_patch(Rectangle((0, 0), 70, 100, fc = pitchcolor, fill=True, zorder=0))
    
    plt.hlines(50, 0, 70, color)
    plt.hlines(0, 0, 70, color)
    plt.hlines(100, 0, 70, color)

    if linestyle == '-':
        plt.hlines(40, 0, 70, color, '--', alpha=lalpha)
        plt.hlines(60, 0, 70, color, '--', alpha=lalpha)
        plt.hlines(22, 0, 70, color, '-')
        plt.hlines(78, 0, 70, color, '-')
        plt.hlines(5, 0, 70, color, '--', alpha=lalpha)
        plt.hlines(95, 0, 70, color, '--', alpha=lalpha)
        plt.vlines(5, 0, 100, color, '-', alpha=lalpha)
        plt.vlines(65, 0, 100, color, '-', alpha=lalpha)
    
    if linestyle == '--':
        plt.vlines(5, 47, 53, color, '-', alpha=lalpha)
        plt.vlines(5, 37, 43, color, '-', alpha=lalpha)
        plt.vlines(5, 57, 63, color, '-', alpha=lalpha)
        plt.vlines(5, 19, 25, color, '-', alpha=lalpha)
        plt.vlines(5, 75, 81, color, '-', alpha=lalpha)
        plt.vlines(5, 5, 11, color, '-', alpha=lalpha)
        plt.vlines(5, 95, 89, color, '-', alpha=lalpha)
        plt.vlines(15, 47, 53, color, '-', alpha=lalpha)
        plt.vlines(15, 37, 43, color, '-', alpha=lalpha)
        plt.vlines(15, 57, 63, color, '-', alpha=lalpha)
        plt.vlines(15, 19, 25, color, '-', alpha=lalpha)
        plt.vlines(15, 75, 81, color, '-', alpha=lalpha)
        plt.vlines(15, 5, 11, color, '-', alpha=lalpha)
        plt.vlines(15, 95, 89, color, '-', alpha=lalpha)
        plt.vlines(65, 47, 53, color, '-', alpha=lalpha)
        plt.vlines(65, 37, 43, color, '-', alpha=lalpha)
        plt.vlines(65, 57, 63, color, '-', alpha=lalpha)
        plt.vlines(65, 19, 25, color, '-', alpha=lalpha)
        plt.vlines(65, 75, 81, color, '-', alpha=lalpha)
        plt.vlines(65, 5, 11, color, '-', alpha=lalpha)
        plt.vlines(65, 95, 89, color, '-', alpha=lalpha)
        plt.vlines(55, 47, 53, color, '-', alpha=lalpha)
        plt.vlines(55, 37, 43, color, '-', alpha=lalpha)
        plt.vlines(55, 57, 63, color, '-', alpha=lalpha)
        plt.vlines(55, 19, 25, color, '-', alpha=lalpha)
        plt.vlines(55, 75, 81, color, '-', alpha=lalpha)
        plt.vlines(55, 5, 11, color, '-', alpha=lalpha)
        plt.vlines(55, 95, 89, color, '-', alpha=lalpha)
        
        plt.hlines(5, 2, 8, color, '-', alpha=lalpha)
        plt.hlines(5, 12, 18, color, '-', alpha=lalpha)
        plt.hlines(5, 68, 62, color, '-', alpha=lalpha)
        plt.hlines(5, 58, 52, color, '-', alpha=lalpha)
        plt.hlines(5, 22, 31, color, '-', alpha=lalpha)
        plt.hlines(5, 39, 48, color, '-', alpha=lalpha)
        plt.hlines(22, 0, 70, color, '-', alpha=lalpha)
        plt.hlines(78, 0, 70, color, '-', alpha=lalpha)
        plt.hlines(40, 2, 8, color, '-', alpha=lalpha)
        plt.hlines(40, 12, 18, color, '-', alpha=lalpha)
        plt.hlines(40, 68, 62, color, '-', alpha=lalpha)
        plt.hlines(40, 58, 52, color, '-', alpha=lalpha)
        plt.hlines(40, 22, 31, color, '-', alpha=lalpha)
        plt.hlines(40, 39, 48, color, '-', alpha=lalpha)
        plt.hlines(60, 2, 8, color, '-', alpha=lalpha)
        plt.hlines(60, 12, 18, color, '-', alpha=lalpha)
        plt.hlines(60, 68, 62, color, '-', alpha=lalpha)
        plt.hlines(60, 58, 52, color, '-', alpha=lalpha)
        plt.hlines(60, 22, 31, color, '-', alpha=lalpha)
        plt.hlines(60, 39, 48, color, '-', alpha=lalpha)
        plt.hlines(95, 2, 8, color, '-', alpha=lalpha)
        plt.hlines(95, 12, 18, color, '-', alpha=lalpha)
        plt.hlines(95, 68, 62, color, '-', alpha=lalpha)
        plt.hlines(95, 58, 52, color, '-', alpha=lalpha)
        plt.hlines(95, 22, 31, color, '-', alpha=lalpha)
        plt.hlines(95, 39, 48, color, '-', alpha=lalpha)

    plt.vlines(0, 0, 100, color)
    plt.vlines(70, 0, 100, color)

    if labels == True:
        if shadows == True and labelalpha != False:
            ax.text(31, 24, '22', fontsize=45, alpha=labelalpha, fontfamily = 'serif', color=color, path_effects=[path_effects.withSimplePatchShadow()])
            ax.text(31, 80, '22', fontsize=45, alpha=labelalpha, fontfamily = 'serif', color = color, path_effects=[path_effects.withSimplePatchShadow()])
            ax.text(31, 52, '50', fontsize=45, alpha=labelalpha, fontfamily = 'serif', color = color, path_effects=[path_effects.withSimplePatchShadow()])
        elif labelalpha != False: 
            ax.text(31, 24, '22', fontsize=45, alpha=labelalpha, fontfamily = 'serif', color=color)
            ax.text(31, 80, '22', fontsize=45, alpha=labelalpha, fontfamily = 'serif', color = color)
            ax.text(31, 52, '50', fontsize=45, alpha=labelalpha, fontfamily = 'serif', color = color)


    if poles == True:
            plt.hlines(100, 30, 40, color, '-', alpha=1, linewidth=5)
            plt.hlines(0, 30, 40, color, '-', alpha=1, linewidth=5)


def leaguepitch(ax='ax', pitchcolor = 'white', linecolor='Black', poles=False, linestyle='--', labels=False, labelalpha=0.5, shadows=False, linealpha=0.2):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    import matplotlib.patheffects as path_effects
    
    color = linecolor
    pitchcolor = pitchcolor
    linealpha = linealpha
    
    ax.add_patch(Rectangle((0, 0), 100, 68, fc = pitchcolor, zorder=0))
    
    plt.vlines(50, 0, 68, color, alpha=1)
    plt.hlines(0, 0, 100, color)
    plt.hlines(68, 0, 100, color)
    
    plt.vlines(60, 0, 68, color, '-', alpha=linealpha)
    plt.vlines(40, 0, 68, color, '-', alpha=linealpha)
    plt.vlines(30, 0, 68, color, '-', alpha=linealpha)
    plt.vlines(70, 0, 68, color, '-', alpha=linealpha)
    plt.vlines(20, 0, 68, color, '-', alpha=linealpha)
    plt.vlines(80, 0, 68, color, '-', alpha=linealpha)
    plt.vlines(10, 0, 68, color, '-', alpha=linealpha)
    plt.vlines(90, 0, 68, color, '-', alpha=linealpha)
    
    if linestyle == '-':
        plt.hlines(5, 0, 100, color, '-', alpha=0.5)
        plt.hlines(63, 0, 100, color, '-', alpha=0.5)
    if linestyle == '--':
        plt.hlines(10, 7, 13, color, '-', alpha=0.5)
        plt.hlines(10, 17, 23, color, '-', alpha=0.5)
        plt.hlines(10, 27, 33, color, '-', alpha=0.5)
        plt.hlines(10, 37, 43, color, '-', alpha=0.5)
        plt.hlines(10, 47, 53, color, '-', alpha=0.5)
        plt.hlines(10, 57, 63, color, '-', alpha=0.5)
        plt.hlines(10, 67, 73, color, '-', alpha=0.5)
        plt.hlines(10, 77, 83, color, '-', alpha=0.5)
        plt.hlines(10, 87, 93, color, '-', alpha=0.5)
        
        plt.hlines(17, 7, 13, color, '-', alpha=0.5)
        plt.hlines(17, 17, 23, color, '-', alpha=0.5)
        plt.hlines(17, 27, 33, color, '-', alpha=0.5)
        plt.hlines(17, 37, 43, color, '-', alpha=0.5)
        plt.hlines(17, 47, 53, color, '-', alpha=0.5)
        plt.hlines(17, 57, 63, color, '-', alpha=0.5)
        plt.hlines(17, 67, 73, color, '-', alpha=0.5)
        plt.hlines(17, 77, 83, color, '-', alpha=0.5)
        plt.hlines(17, 87, 93, color, '-', alpha=0.5)

        plt.hlines(58, 7, 13, color, '-', alpha=0.5)
        plt.hlines(58, 17, 23, color, '-', alpha=0.5)
        plt.hlines(58, 27, 33, color, '-', alpha=0.5)
        plt.hlines(58, 37, 43, color, '-', alpha=0.5)
        plt.hlines(58, 47, 53, color, '-', alpha=0.5)
        plt.hlines(58, 57, 63, color, '-', alpha=0.5)
        plt.hlines(58, 67, 73, color, '-', alpha=0.5)
        plt.hlines(58, 77, 83, color, '-', alpha=0.5)
        plt.hlines(58, 87, 93, color, '-', alpha=0.5)
        
        plt.hlines(51, 7, 13, color, '-', alpha=0.5)
        plt.hlines(51, 17, 23, color, '-', alpha=0.5)
        plt.hlines(51, 27, 33, color, '-', alpha=0.5)
        plt.hlines(51, 37, 43, color, '-', alpha=0.5)
        plt.hlines(51, 47, 53, color, '-', alpha=0.5)
        plt.hlines(51, 57, 63, color, '-', alpha=0.5)
        plt.hlines(51, 67, 73, color, '-', alpha=0.5)
        plt.hlines(51, 77, 83, color, '-', alpha=0.5)
        plt.hlines(51, 87, 93, color, '-', alpha=0.5)
        
    if linestyle != '-' and linestyle != '--':
        print("Error, five line type not found, please use: - or --")
    
    plt.vlines(0, 0, 68, color)
    plt.vlines(100, 0, 68, color)
    
    if labels == True:
        if shadows == True and labelalpha != False:
            ax.text(7.5, 12, '10', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color=color, path_effects=[path_effects.withSimplePatchShadow()])
            ax.text(17.5, 12, '20', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color = color, path_effects=[path_effects.withSimplePatchShadow()])
            ax.text(27.5, 12, '30', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color = color, path_effects=[path_effects.withSimplePatchShadow()])
            ax.text(37.5, 12, '40', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color=color, path_effects=[path_effects.withSimplePatchShadow()])
            ax.text(47, 12, '5 0', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color = color, path_effects=[path_effects.withSimplePatchShadow()])
            ax.text(57.5, 12, '40', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color = color, path_effects=[path_effects.withSimplePatchShadow()])
            ax.text(67.5, 12, '30', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color=color, path_effects=[path_effects.withSimplePatchShadow()])
            ax.text(77.5, 12, '20', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color = color, path_effects=[path_effects.withSimplePatchShadow()])
            ax.text(87.5, 12, '10', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color = color, path_effects=[path_effects.withSimplePatchShadow()])
            
            ax.text(7.5, 54, '10', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color=color, rotation=180, path_effects=[path_effects.withSimplePatchShadow()])
            ax.text(17.5, 54, '20', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color = color, rotation=180, path_effects=[path_effects.withSimplePatchShadow()])
            ax.text(27.5, 54, '30', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color = color, rotation=180, path_effects=[path_effects.withSimplePatchShadow()])
            ax.text(37.5, 54, '40', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color=color, rotation=180, path_effects=[path_effects.withSimplePatchShadow()])
            ax.text(47, 54, '5 0', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color = color, rotation=180, path_effects=[path_effects.withSimplePatchShadow()])
            ax.text(57.5, 54, '40', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color = color, rotation=180, path_effects=[path_effects.withSimplePatchShadow()])
            ax.text(67.5, 54, '30', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color=color, rotation=180, path_effects=[path_effects.withSimplePatchShadow()])
            ax.text(77.5, 54, '20', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color = color, rotation=180, path_effects=[path_effects.withSimplePatchShadow()])
            ax.text(87.5, 54, '10', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color = color, rotation=180, path_effects=[path_effects.withSimplePatchShadow()])
        elif labelalpha != False: 
            ax.text(7.5, 12, '10', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color=color)
            ax.text(17.5, 12, '20', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color = color)
            ax.text(27.5, 12, '30', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color = color)
            ax.text(37.5, 12, '40', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color=color)
            ax.text(47, 12, '5 0', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color = color)
            ax.text(57.5, 12, '40', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color = color)
            ax.text(67.5, 12, '30', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color=color)
            ax.text(77.5, 12, '20', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color = color)
            ax.text(87.5, 12, '10', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color = color)
            
            ax.text(7.5, 54, '10', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color=color, rotation=180)
            ax.text(17.5, 54, '20', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color = color, rotation=180)
            ax.text(27.5, 54, '30', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color = color, rotation=180)
            ax.text(37.5, 54, '40', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color=color, rotation=180)
            ax.text(47, 54, '5 0', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color = color, rotation=180)
            ax.text(57.5, 54, '40', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color = color, rotation=180)
            ax.text(67.5, 54, '30', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color=color, rotation=180)
            ax.text(77.5, 54, '20', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color = color, rotation=180)
            ax.text(87.5, 54, '10', fontsize=25, alpha=labelalpha, fontfamily = 'serif', color = color, rotation=180)

    if poles == True:
            plt.vlines(0, 30, 40, color, '-', alpha=1, linewidth=5)
            plt.vlines(100, 30, 40, color, '-', alpha=1, linewidth=5) 

def pitch(ax='ax', pitchcolor = 'white', linecolor='Black', poles=False, linestyle='--', labels=False, labelalpha=0.5, shadows=False, linealpha=0.2):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    import matplotlib.patheffects as path_effects
    
    color = linecolor
    lalpha=linealpha
    
    ax.add_patch(Rectangle((0, 0), 100, 70, fc = pitchcolor, zorder=0))

    halfway = plt.vlines(50, 0, 70, color)
    bottom = plt.hlines(0, 0, 100, color)
    top = plt.hlines(70, 0, 100, color)
    
    
    
    if linestyle == '-':
        hfive1 = plt.hlines(5, 0, 100, color, '-', alpha=lalpha)
        hfive2 = plt.hlines(65, 0, 100, color, '-', alpha=lalpha)
        ten1 = plt.vlines(60, 0, 70, color, '--', alpha=lalpha)
        ten2 = plt.vlines(40, 0, 70, color, '--', alpha=lalpha)
        twentytwo1 = plt.vlines(22, 0, 70, color, '-', alpha=lalpha)
        twentytwo2 = plt.vlines(78, 0, 70, color, '-', alpha=lalpha)
        five1 = plt.vlines(5, 0, 70, color, '--', alpha=lalpha)
        five2 = plt.vlines(95, 0, 70, color, '--', alpha=lalpha)
        
    if linestyle == '--':
        plt.hlines(5, 47, 53, color, '-', alpha=lalpha)
        plt.hlines(5, 37, 43, color, '-', alpha=lalpha)
        plt.hlines(5, 57, 63, color, '-', alpha=lalpha)
        plt.hlines(5, 19, 25, color, '-', alpha=lalpha)
        plt.hlines(5, 75, 81, color, '-', alpha=lalpha)
        plt.hlines(5, 5, 11, color, '-', alpha=lalpha)
        plt.hlines(5, 95, 89, color, '-', alpha=lalpha)
        plt.hlines(15, 47, 53, color, '-', alpha=lalpha)
        plt.hlines(15, 37, 43, color, '-', alpha=lalpha)
        plt.hlines(15, 57, 63, color, '-', alpha=lalpha)
        plt.hlines(15, 19, 25, color, '-', alpha=lalpha)
        plt.hlines(15, 75, 81, color, '-', alpha=lalpha)
        plt.hlines(15, 5, 11, color, '-', alpha=lalpha)
        plt.hlines(15, 95, 89, color, '-', alpha=lalpha)
        plt.hlines(65, 47, 53, color, '-', alpha=lalpha)
        plt.hlines(65, 37, 43, color, '-', alpha=lalpha)
        plt.hlines(65, 57, 63, color, '-', alpha=lalpha)
        plt.hlines(65, 19, 25, color, '-', alpha=lalpha)
        plt.hlines(65, 75, 81, color, '-', alpha=lalpha)
        plt.hlines(65, 5, 11, color, '-', alpha=lalpha)
        plt.hlines(65, 95, 89, color, '-', alpha=lalpha)
        plt.hlines(55, 47, 53, color, '-', alpha=lalpha)
        plt.hlines(55, 37, 43, color, '-', alpha=lalpha)
        plt.hlines(55, 57, 63, color, '-', alpha=lalpha)
        plt.hlines(55, 19, 25, color, '-', alpha=lalpha)
        plt.hlines(55, 75, 81, color, '-', alpha=lalpha)
        plt.hlines(55, 5, 11, color, '-', alpha=lalpha)
        plt.hlines(55, 95, 89, color, '-', alpha=lalpha)
        
        plt.vlines(5, 2, 8, color, '-', alpha=lalpha)
        plt.vlines(5, 12, 18, color, '-', alpha=lalpha)
        plt.vlines(5, 68, 62, color, '-', alpha=lalpha)
        plt.vlines(5, 58, 52, color, '-', alpha=lalpha)
        plt.vlines(5, 22, 31, color, '-', alpha=lalpha)
        plt.vlines(5, 39, 48, color, '-', alpha=lalpha)
        plt.vlines(22, 0, 70, color, '-', alpha=lalpha)
        plt.vlines(78, 0, 70, color, '-', alpha=lalpha)
        
        plt.vlines(40, 2, 8, color, '-', alpha=lalpha)
        plt.vlines(40, 12, 18, color, '-', alpha=lalpha)
        plt.vlines(40, 68, 62, color, '-', alpha=lalpha)
        plt.vlines(40, 58, 52, color, '-', alpha=lalpha)
        plt.vlines(40, 22, 31, color, '-', alpha=lalpha)
        plt.vlines(40, 39, 48, color, '-', alpha=lalpha)
        
        plt.vlines(60, 2, 8, color, '-', alpha=lalpha)
        plt.vlines(60, 12, 18, color, '-', alpha=lalpha)
        plt.vlines(60, 68, 62, color, '-', alpha=lalpha)
        plt.vlines(60, 58, 52, color, '-', alpha=lalpha)
        plt.vlines(60, 22, 31, color, '-', alpha=lalpha)
        plt.vlines(60, 39, 48, color, '-', alpha=lalpha)
        
        plt.vlines(95, 2, 8, color, '-', alpha=lalpha)
        plt.vlines(95, 12, 18, color, '-', alpha=lalpha)
        plt.vlines(95, 68, 62, color, '-', alpha=lalpha)
        plt.vlines(95, 58, 52, color, '-', alpha=lalpha)
        plt.vlines(95, 22, 31, color, '-', alpha=lalpha)
        plt.vlines(95, 39, 48, color, '-', alpha=lalpha)


    if linestyle != '-' and linestyle != '--':
        print("Error, five line type not found, please use: - or --")
        pass
    
    plt.vlines(0, 0, 70, color)
    plt.vlines(100, 0, 70, color)
    
    if labels == True:
        if shadows == True and labelalpha != False:
            ax.text(18, 32, '22', fontsize=45, alpha=labelalpha, fontfamily = 'serif', color=color, path_effects=[path_effects.withSimplePatchShadow()])
            ax.text(74, 32, '22', fontsize=45, alpha=labelalpha, fontfamily = 'serif', color = color, path_effects=[path_effects.withSimplePatchShadow()])
            ax.text(46, 32, '50', fontsize=45, alpha=labelalpha, fontfamily = 'serif', color = color, path_effects=[path_effects.withSimplePatchShadow()])
        elif labelalpha != False: 
            ax.text(18, 32, '22', fontsize=45, alpha=labelalpha, fontfamily = 'serif', color=color)
            ax.text(74, 32, '22', fontsize=45, alpha=labelalpha, fontfamily = 'serif', color = color)
            ax.text(46, 32, '50', fontsize=45, alpha=labelalpha, fontfamily = 'serif', color = color)
        
    if poles == True:
            plt.vlines(0, 30, 40, color, '-', alpha=1, linewidth=5)
            plt.vlines(100, 30, 40, color, '-', alpha=1, linewidth=5)

def badge(ax='ax', img='none', alpha=1, zorder=99):
    z = zorder
    logo=img
    alf = alpha
    import matplotlib.image as image
    im = image.imread(logo)
    ax.imshow(im, alpha=alf, aspect='auto', extent=(57, 93, 15, 55), zorder=z)

def zones(data, ax= 'ax', alpha=0.5, paint1 = '#0384fc', paint2 = '#FF4F3F', legend=False):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    import matplotlib.patheffects as path_effects
    
    col1 = '#0384fc'
    col2 = '#FF4F3F'

    ax=ax

    data=data

    col1 = paint1
    col2 = paint2

    edge = 'black'

    alpha=alpha
    colors = [col1, col2]

    if len(data) != 48:
        print('Error, length of data is not equal to 48')

    if len(data) == 48:
        ax.add_patch(Rectangle((0, 0), 11, 15, fc = colors[(data[0])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((11, 0), 11, 15, fc = colors[(data[1])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((22, 0), 18, 15, fc = colors[(data[2])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((40, 0), 10, 15, fc = colors[(data[3])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((50, 0), 10, 15, fc = colors[(data[4])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((60, 0), 18, 15, fc = colors[(data[5])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((78, 0), 11, 15, fc = colors[(data[6])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((89, 0), 11, 15, fc = colors[(data[7])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))

        ax.add_patch(Rectangle((0, 15), 11, 10, fc = colors[(data[8])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((11, 15), 11, 10, fc = colors[(data[9])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((22, 15), 18, 10, fc = colors[(data[10])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((40, 15), 10, 10, fc = colors[(data[11])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((50, 15), 10, 10, fc = colors[(data[12])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((60, 15), 18, 10, fc = colors[(data[13])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((78, 15), 11, 10, fc = colors[(data[14])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((89, 15), 11, 10, fc = colors[(data[15])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))

        ax.add_patch(Rectangle((0, 25), 11, 10, fc = colors[(data[16])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((11, 25), 11, 10, fc = colors[(data[17])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((22, 25), 18, 10, fc = colors[(data[18])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((40, 25), 10, 10, fc = colors[(data[19])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((50, 25), 10, 10, fc = colors[(data[20])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((60, 25), 18, 10, fc = colors[(data[21])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((78, 25), 11, 10, fc = colors[(data[22])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((89, 25), 11, 10, fc = colors[(data[23])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))

        ax.add_patch(Rectangle((0, 35), 11, 10, fc = colors[(data[24])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((11, 35), 11, 10, fc = colors[(data[25])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((22, 35), 18, 10, fc = colors[(data[26])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((40, 35), 10, 10, fc = colors[(data[27])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((50, 35), 10, 10, fc = colors[(data[28])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((60, 35), 18, 10, fc = colors[(data[29])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((78, 35), 11, 10, fc = colors[(data[30])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((89, 35), 11, 10, fc = colors[(data[31])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))

        ax.add_patch(Rectangle((0, 45), 11, 10, fc = colors[(data[32])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((11, 45), 11, 10, fc = colors[(data[33])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((22, 45), 18, 10, fc = colors[(data[34])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((40, 45), 10, 10, fc = colors[(data[35])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((50, 45), 10, 10, fc = colors[(data[36])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((60, 45), 18, 10, fc = colors[(data[37])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((78, 45), 11, 10, fc = colors[(data[38])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((89, 45), 11, 10, fc = colors[(data[39])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))

        ax.add_patch(Rectangle((0, 55), 11, 15, fc = colors[(data[40])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((11, 55), 11, 15, fc = colors[(data[41])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((22, 55), 18, 15, fc = colors[(data[42])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((40, 55), 10, 15, fc = colors[(data[43])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((50, 55), 10, 15, fc = colors[(data[44])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((60, 55), 18, 15, fc = colors[(data[45])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((78, 55), 11, 15, fc = colors[(data[46])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))
        ax.add_patch(Rectangle((89, 55), 11, 15, fc = colors[(data[47])], fill=True, edgecolor=edge, linewidth=0.25, alpha=alpha, zorder=0))


        if legend == True:
            import matplotlib.font_manager as font_manager
            font = font_manager.FontProperties(family='Serif', style='normal', size=16)

            plt.plot((1, 5), (1, 5), zorder= -10, linewidth = 5, label='Team', color=col1)
            plt.plot((1, 5), (1, 5), zorder= -10, linewidth = 5, color=col2, label='Opponent')

            ax.legend(loc='lower center', prop=font, ncol=2, borderaxespad = -2, columnspacing = 1, fontsize='x-large', labelcolor='white', facecolor = 'Black', shadow = False, framealpha = 0)