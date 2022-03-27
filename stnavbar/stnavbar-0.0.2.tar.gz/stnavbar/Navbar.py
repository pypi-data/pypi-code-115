import enum
import base64
import streamlit as st
from streamlit.components.v1 import html

class NotANavbarItem(Exception):
    def __init__(self):
        self.message = f'Incorrect item type, expecting NavbarItem()'
        super().__init__(self.message)
 
    def __str__(self):
        return self.message
 
class IncorrectIcon(Exception):
    def __init__(self):
        self.message = f'Could not use this icon, setting to default'
        super().__init__(self.message)
 
    def __str__(self):
        return self.message

class ItemType(enum.Enum):
    NAVBAR_ITEM = 'navitem'
    DROPDOWN_ITEM = 'settingsNav'
 
class NavbarItem:
    def __init__(
            self,
            callback:None,
            path:str = '',
            title:str = '',
            item_type:ItemType = ItemType.NAVBAR_ITEM,
        ):
        self.callback = callback
        self.item_type = item_type
        self.path = path
        self.title = title
 
    def get_item_as_html(self) -> str():
        return f'<a class="{self.item_type.value}" href="/?nav={self.path}">{self.title}</a>'
 
class Navbar:
    def __init__(self,
                dropdown_state:bool = True
                ):
        self.navbar_items = []
        self.dropdown_state = dropdown_state
        self.dropdown_icon = '<div class="default-dropdown">☰</div>'
        self.dropdown_items = []
        self._html_navbar_items = str()
        self._html_dropdown_items = str()
 
    def _build_html_from_items(self):
        # Building navbar items
        for navbar_item in self.navbar_items:
            self._html_navbar_items = self._html_navbar_items + navbar_item.get_item_as_html()
        # Building dropdown items
        for dropdown_item in self.dropdown_items:
            self._html_dropdown_items = self._html_dropdown_items + dropdown_item.get_item_as_html()
 
    def set_dropdown_icon(self,icon_image_path:str):
        try:
            with open(icon_image_path, "rb") as icon_file:
                image_as_base64 = base64.b64encode(icon_file.read())
            self.dropdown_icon = rf'<img class="dropbtn" src="data:image/png;base64, {image_as_base64.decode("utf-8")}"/>'
        except IncorrectIcon as e:
            self.dropdown_icon = '<div class="default-dropdown">☰</div>'
 
    def inject_navbar_to_page(self):
        dropdown_hidden = "" if self.dropdown_state else "hidden"
        self._build_html_from_items()
        navbar_as_html = rf'''
            <nav class="container navbar" id="navbar">
                <ul class="navlist">
                {self._html_navbar_items}
                </ul>
                <div class="dropdown" id="settingsDropDown" {dropdown_hidden}>
                    {self.dropdown_icon}
                    <div id="myDropdown" class="dropdown-content">
                        {self._html_dropdown_items}
                    </div>
                </div>
            </nav>
            '''
        st.markdown(navbar_as_html,unsafe_allow_html=True)
        navbar_javascript = '''
        <script>
            // navbar elements
            var navigationTabs = window.parent.document.getElementsByClassName("navitem");
 
            var cleanNavbar = function(navigation_element) {
                navigation_element.removeAttribute('target')
            }
 
            for (var i = 0; i < navigationTabs.length; i++) {
                cleanNavbar(navigationTabs[i]);
            }
 
            // dropdown
            var dropdown = window.parent.document.getElementById("settingsDropDown");
            dropdown.onclick = function() {
                var dropWindow = window.parent.document.getElementById("myDropdown");
                if (dropWindow.style.visibility == "hidden"){
                    dropWindow.style.visibility = "visible";
                }else{
                    dropWindow.style.visibility = "hidden";
                }
            };
 
            var settingsNavs = window.parent.document.getElementsByClassName("settingsNav");
 
            var cleanSettings = function(navigation_element) {
                navigation_element.removeAttribute('target')
            }
 
            for (var i = 0; i < settingsNavs.length; i++) {
                cleanSettings(settingsNavs[i]);
            }
        </script>
        '''
        html(navbar_javascript)
 
    def add_navbar_item(self, navbar_item:NavbarItem):
        if navbar_item.item_type == ItemType.NAVBAR_ITEM:
            self.navbar_items.append(navbar_item)
        elif navbar_item.item_type == ItemType.DROPDOWN_ITEM:
            self.dropdown_items.append(navbar_item)
        else:
            raise NotANavbarItem
 
    def add_navbar_items(self,navbar_items_list:list()):
        for item in navbar_items_list:
            self.add_navbar_item(item)
 
 
class Navigation:
    def __init__(self,
            navbar:Navbar = None,
            default_path:str = 'analysis'
            ):
        self._navigations = navbar.navbar_items + navbar.dropdown_items
 
    def navigate(self,
                 current_path:str=""):
        for item in self._navigations:
            if item.path == current_path:
                item.callback()