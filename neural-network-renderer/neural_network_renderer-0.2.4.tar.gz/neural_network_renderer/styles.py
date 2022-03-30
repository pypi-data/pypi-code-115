from pathlib import Path
from sys import platform


class Style:
    def __init__(self):
        self.filename = ""
        self.content = ""

    def generate(self):
        with open(self.filename, "w") as f:
            f.write(self.content)

    def clean(self):
        Path(self.filename).unlink()


class Ball(Style):
    def __init__(self):
        self.filename = "Ball.sty"
        self.content = r"""
        \ProvidesPackage{Ball}
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        %This Block can draw small Ball
        %Elementwise or reduction operations can be drawn with this
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

        \tikzset{Ball/.pic=
            {
                \tikzset{/sphere/.cd,#1}	 	

            \pgfmathsetmacro{\r}{\radius*\scale}

            \shade[ball color=\fill,opacity=\opacity] (0,0,0) circle (\r);
            \draw (0,0,0) circle [radius=\r] node[scale=4*\r] {\logo};

            \coordinate (\name-anchor) at ( 0 , 0  , 0) ;
            \coordinate (\name-east)   at ( \r, 0  , 0) ;
            \coordinate (\name-west)   at (-\r, 0  , 0) ;
            \coordinate (\name-north)  at ( 0 , \r , 0) ;
            \coordinate (\name-south)  at ( 0 , -\r, 0) ;

            \path (\name-south) + (0,-20pt) coordinate (caption-node) 
            edge ["\textcolor{black}{\bf \caption}"'] (caption-node); %Ball caption

            },
            /sphere/.search also={/tikz},
            /sphere/.cd,
            radius/.store       in=\radius,
            scale/.store        in=\scale,
            caption/.store      in=\caption,
            name/.store         in=\name,
            fill/.store         in=\fill,
            logo/.store         in=\logo,
            opacity/.store      in=\opacity,
            logo=$\Sigma$,
            fill=green,
            opacity=0.10,
            scale=0.2,
            radius=0.5,
            caption=,
            name=,
        }"""


class Box(Style):
    def __init__(self):
        self.filename = "Box.sty"
        self.content = r"""
        \ProvidesPackage{Box}
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        % This Block can draw simple block of boxes with custom colors. 
        % Can be used for conv, deconv etc
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        \tikzset{Box/.pic={\tikzset{/boxblock/.cd,#1}
                \tikzstyle{box}=[every edge/.append style={pic actions, densely dashed, opacity=.7},fill opacity=\opacity, pic actions,fill=\fill]
                
                \pgfmathsetmacro{\y}{\cubey*\scale}
                \pgfmathsetmacro{\z}{\cubez*\scale}
        
                %Multiple concatenated boxes
                \foreach[count=\i,%
                        evaluate=\i as \xlabel using {array({\boxlabels},\i-1)},% 
                        evaluate=\unscaledx as \k using {\unscaledx*\scale+\prev}, remember=\k as \prev (initially 0)] 
                        \unscaledx in \cubex
                {
                    \pgfmathsetmacro{\x}{\unscaledx*\scale}
                    \coordinate (a) at (\k-\x , \y/2 , \z/2); 
                    \coordinate (b) at (\k-\x ,-\y/2 , \z/2); 
                    \coordinate (c) at (\k    ,-\y/2 , \z/2); 
                    \coordinate (d) at (\k    , \y/2 , \z/2); 
                    \coordinate (e) at (\k    , \y/2 ,-\z/2); 
                    \coordinate (f) at (\k    ,-\y/2 ,-\z/2); 
                    \coordinate (g) at (\k-\x ,-\y/2 ,-\z/2); 
                    \coordinate (h) at (\k-\x , \y/2 ,-\z/2); 
                
                    \draw [box] 
                        (d) -- (a) -- (b) -- (c) -- cycle     
                        (d) -- (a) -- (h) -- (e) -- cycle
                        %dotted edges
                        (f) edge (g)
                        (b) edge (g)
                        (h) edge (g)    
                    ;
                    \path (b) edge ["\xlabel"',midway] (c);
                    
                    \xdef\LastEastx{\k} %\k persists as \LastEastx after loop 
                }%Loop ends
                \draw [box] (d) -- (e) -- (f) -- (c) -- cycle; %East face of last box     
                
                \coordinate (a1) at (0 , \y/2 , \z/2);
                \coordinate (b1) at (0 ,-\y/2 , \z/2);
                \tikzstyle{depthlabel}=[pos=0,text width=14*\z,midway,sloped]       
                
                \path (c) edge ["\small\zlabel"',depthlabel](f); %depth label
                \path (b1) edge ["\ylabel",midway] (a1);  %height label
                
                
                \tikzstyle{captionlabel}=[text width=15*\LastEastx/\scale,text centered]       
                \path (\LastEastx/2,-\y/2,+\z/2) + (0,-25pt) coordinate (cap) 
                edge ["\textcolor{black}{ \bf \caption}"',captionlabel](cap) ; %Block caption/pic object label
                
                %Define nodes to be used outside on the pic object
                \coordinate (\name-west)   at (0,0,0) ;
                \coordinate (\name-east)   at (\LastEastx, 0,0) ;
                \coordinate (\name-north)  at (\LastEastx/2,\y/2,0);
                \coordinate (\name-south)  at (\LastEastx/2,-\y/2,0);       
                \coordinate (\name-anchor) at (\LastEastx/2, 0,0) ;
                
                \coordinate (\name-near) at (\LastEastx/2,0,\z/2);
                \coordinate (\name-far)  at (\LastEastx/2,0,-\z/2);       
                
                \coordinate (\name-nearwest) at (0,0,\z/2);
                \coordinate (\name-neareast) at (\LastEastx,0,\z/2);
                \coordinate (\name-farwest)  at (0,0,-\z/2);
                \coordinate (\name-fareast)  at (\LastEastx,0,-\z/2);
                
                \coordinate (\name-northeast) at (\name-north-|\name-east);
                \coordinate (\name-northwest) at (\name-north-|\name-west);
                \coordinate (\name-southeast) at (\name-south-|\name-east);
                \coordinate (\name-southwest) at (\name-south-|\name-west);
                
                \coordinate (\name-nearnortheast)  at (\LastEastx, \y/2, \z/2);
                \coordinate (\name-farnortheast)   at (\LastEastx, \y/2,-\z/2);
                \coordinate (\name-nearsoutheast)  at (\LastEastx,-\y/2, \z/2);
                \coordinate (\name-farsoutheast)   at (\LastEastx,-\y/2,-\z/2);
                
                \coordinate (\name-nearnorthwest)  at (0, \y/2, \z/2);
                \coordinate (\name-farnorthwest)   at (0, \y/2,-\z/2);
                \coordinate (\name-nearsouthwest)  at (0,-\y/2, \z/2);
                \coordinate (\name-farsouthwest)   at (0,-\y/2,-\z/2);
                
            },
            /boxblock/.search also={/tikz},
            /boxblock/.cd,
            width/.store        in=\cubex,
            height/.store       in=\cubey,
            depth/.store        in=\cubez,
            scale/.store        in=\scale,
            xlabel/.store       in=\boxlabels,
            ylabel/.store       in=\ylabel,
            zlabel/.store       in=\zlabel,
            caption/.store      in=\caption,
            name/.store         in=\name,
            fill/.store         in=\fill,
            opacity/.store      in=\opacity,
            fill={rgb:red,5;green,5;blue,5;white,15},
            opacity=0.4,
            width=2,
            height=13,
            depth=15,
            scale=.2,
            xlabel={{"","","","","","","","","",""}},
            ylabel=,
            zlabel=,
            caption=,
            name=,
        }"""


class RightBandedBox(Style):
    def __init__(self):
        self.filename = "RightBandedBox.sty"
        self.content = r"""
        \ProvidesPackage{RightBandedBox}
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        % This Block can draw simple block of boxes with custom colors. 
        % Can be used for conv, deconv etc
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        \tikzset{RightBandedBox/.pic=
            {
                \tikzset{/block/.cd,#1}
                            
                \tikzstyle{box}=[every edge/.append style={pic actions, densely dashed, opacity=.7},fill opacity=\opacity, pic actions,fill=\fill]
                        
                \tikzstyle{band}=[every edge/.append style={pic actions, densely dashed, opacity=.7},fill opacity=\bandopacity, pic actions,fill=\bandfill,draw=\bandfill]
                        
                \pgfmathsetmacro{\y}{\cubey*\scale}
                \pgfmathsetmacro{\z}{\cubez*\scale}

                        %Multiple concatenated boxes	 	  	
                \foreach[count=\i,%
                    evaluate=\i as \xlabel using {array({\boxlabels},\i-1)},% 
                    evaluate=\unscaledx as \k using {\unscaledx*\scale+\prev}, remember=\k as \prev (initially 0)] 
                    \unscaledx in \cubex
                {
                    \pgfmathsetmacro{\x}{\unscaledx*\scale}
                    \coordinate (a)     at (\k-\x   , \y/2 , \z/2); 
                    \coordinate (art)   at (\k-\x/3 , \y/2 , \z/2); %a_right_third
                    \coordinate (b)     at (\k-\x   ,-\y/2 , \z/2); 
                    \coordinate (brt)   at (\k-\x/3 ,-\y/2 , \z/2); %b_right_third
                    \coordinate (c)     at (\k      ,-\y/2 , \z/2); 
                    \coordinate (d)     at (\k      , \y/2 , \z/2); 
                    \coordinate (e)     at (\k      , \y/2 ,-\z/2); 
                    \coordinate (f)     at (\k      ,-\y/2 ,-\z/2); 
                    \coordinate (g)     at (\k-\x   ,-\y/2 ,-\z/2); 
                    \coordinate (h)     at (\k-\x   , \y/2 ,-\z/2); 
                    \coordinate (hrt)   at (\k-\x/3 , \y/2 ,-\z/2); %h_right_third
                        
                    %fill box color 			
                    \draw [box] 
                        (d) -- (a) -- (b) -- (c) -- cycle     
                        (d) -- (a) -- (h) -- (e) -- cycle;
                    %dotted edges
                    \draw [box]
                        (f) edge (g)
                        (b) edge (g)
                        (h) edge (g);
                    %fill band color    
                    \draw [band] 
                        (d) -- (art) -- (brt) -- (c) -- cycle     
                        (d) -- (art) -- (hrt) -- (e) -- cycle;
                    %draw edges again which were covered by band
                    \draw [box,fill opacity=0] 
                        (d) -- (a) -- (b) -- (c) -- cycle     
                        (d) -- (a) -- (h) -- (e) -- cycle;            
                        
                    \path (b) edge ["\xlabel"',midway] (c);
                    
                    \xdef\LastEastx{\k} %\k persists as \LastEastx after loop 
                }%Loop ends

                \draw [box] (d) -- (e) -- (f) -- (c) -- cycle; %East face of last box
                \draw [band] (d) -- (e) -- (f) -- (c) -- cycle; %East face of last box 
                \draw [pic actions] (d) -- (e) -- (f) -- (c) -- cycle; %East face edges of last box     
                
                \coordinate (a1) at (0 , \y/2 , \z/2);
                \coordinate (b1) at (0 ,-\y/2 , \z/2);
                \tikzstyle{depthlabel}=[pos=0,text width=14*\z,text centered,sloped]       
                
                \path (c) edge ["\small\zlabels"',depthlabel](f); %depth label
                \path (b1) edge ["\ylabel",midway] (a1);  %height label 	  
                
                \tikzstyle{captionlabel}=[text width=15*\LastEastx/\scale,text centered] 
                \path (\LastEastx/2,-\y/2,+\z/2) + (0,-25pt) coordinate (cap) 
                edge ["\textcolor{black}{ \bf \caption}"',captionlabel] (cap); %Block caption/pic object label
                    
                %Define nodes to be used outside on the pic object
                \coordinate (\name-west)   at (0,0,0) ;
                \coordinate (\name-east)   at (\LastEastx, 0,0) ;
                \coordinate (\name-north)  at (\LastEastx/2,\y/2,0);
                \coordinate (\name-south)  at (\LastEastx/2,-\y/2,0);       
                \coordinate (\name-anchor) at (\LastEastx/2, 0,0) ;
                
                \coordinate (\name-near) at (\LastEastx/2,0,\z/2);
                \coordinate (\name-far)  at (\LastEastx/2,0,-\z/2);       
                
                \coordinate (\name-nearwest) at (0,0,\z/2);
                \coordinate (\name-neareast) at (\LastEastx,0,\z/2);
                \coordinate (\name-farwest)  at (0,0,-\z/2);
                \coordinate (\name-fareast)  at (\LastEastx,0,-\z/2);
                
                \coordinate (\name-northeast) at (\name-north-|\name-east);
                \coordinate (\name-northwest) at (\name-north-|\name-west);
                \coordinate (\name-southeast) at (\name-south-|\name-east);
                \coordinate (\name-southwest) at (\name-south-|\name-west);
                
                \coordinate (\name-nearnortheast)  at (\LastEastx, \y/2, \z/2);
                \coordinate (\name-farnortheast)   at (\LastEastx, \y/2,-\z/2);
                \coordinate (\name-nearsoutheast)  at (\LastEastx,-\y/2, \z/2);
                \coordinate (\name-farsoutheast)   at (\LastEastx,-\y/2,-\z/2);
                
                \coordinate (\name-nearnorthwest)  at (0, \y/2, \z/2);
                \coordinate (\name-farnorthwest)   at (0, \y/2,-\z/2);
                \coordinate (\name-nearsouthwest)  at (0,-\y/2, \z/2);
                \coordinate (\name-farsouthwest)   at (0,-\y/2,-\z/2);
            },
            /block/.search also={/tikz},
            /block/.cd,
            width/.store        in=\cubex,
            height/.store       in=\cubey,
            depth/.store        in=\cubez,
            scale/.store        in=\scale,
            xlabel/.store       in=\boxlabels,
            ylabel/.store       in=\ylabel,
            zlabel/.store       in=\zlabels,
            caption/.store      in=\caption,
            name/.store         in=\name,
            fill/.store         in=\fill,
            bandfill/.store     in=\bandfill,
            opacity/.store      in=\opacity,
            bandopacity/.store  in=\bandopacity,
            fill={rgb:red,5;green,5;blue,5;white,15},
            bandfill={rgb:red,5;green,5;blue,5;white,5},
            opacity=0.4,
            bandopacity=0.6,
            width=2,
            height=13,
            depth=15,
            scale=.2,
            xlabel={{"","","","","","","","","",""}},
            ylabel=,
            zlabel=,
            caption=,
            name=,
        }"""


class PDFExport:
    def __init__(self, filename):
        self.filename = filename

    def export(self, pathname):

        if platform != "win32":
            bash_command = r"""pdflatex FILEROOT.tex > /dev/null 2>&1
            rm *.aux *.log *.tex *.sty"""
        else:
            bash_command = r"""pdflatex -shell-escape FILEROOT.tex > /dev/null"""

        bash_command = bash_command.replace("FILEROOT", pathname)

        with open(self.filename, "w") as f:
            f.write(bash_command)
